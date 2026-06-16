# GPU & Kubernetes Mastery Guide
## Section 7: Production GPU Troubleshooting & Incident Response Playbooks

---

### Incident 1: Silent ECC Double-Bit Error (Hardware Failure)

#### Symptoms
A multi-node Llama-3-70B training run suddenly halts. The Pod log ends abruptly or exits with code `139` (Segmentation Fault) or prints a bus/memory error. The master Pod reports high peer-to-peer timeout failures over NCCL.

#### Detection
1. Run `kubectl get pods -n ml-platform` and observe Pods in `Error` or `CrashLoopBackOff` state.
2. Query Prometheus metric `delta(DCGM_FI_DEV_ECC_DBE[5m]) > 0`.
3. Check host dmesg logs for hardware exceptions.

#### Investigation
SSH into the node hosting the failed Pod and query NVML directly for ECC error counters:
```bash
nvidia-smi -q -d ECC
```
Look for the section containing uncorrectable (double-bit) volatile errors:
```text
ECC Errors
    Volatile
        Single Bit
            Active              : 12
        Double Bit
            Active              : 1    <-- CRITICAL: Volatile Double Bit error!
```
Next, run `dmesg` and search for NVIDIA errors:
```bash
dmesg -T | grep -i "NVRM"
```
You find:
```text
[Sat Jun 13 16:12:04 2026] NVRM: Xid (PCI:0000:01:00): 95, pid=245122, Row Remapping failed, ECC uncorrectable error.
```

#### Root Cause
A cosmic ray or thermal stress caused a physical memory flip in the GPU’s high-bandwidth memory (HBM). Because the error was a Double-Bit Error (DBE), the hardware’s internal Hamming codes could detect but not correct it. The GPU immediate triggers an internal interrupt (Xid 95) and isolates the faulty memory space, causing the running CUDA kernel to crash.

#### Resolution
1. **Immediate Action**: Drain the node in Kubernetes so no new jobs are scheduled on it:
```bash
kubectl drain node-gpu-39.cluster.local --ignore-daemonsets --delete-emptydir-data
```
2. **Reboot**: Perform a hard system reset of the host node. This triggers NVIDIA's hardware-based **Row Remapping**, which attempts to dynamically map out the broken silicon cells to healthy spare rows.
3. **Check Status**: After boot, check if row remapping succeeded:
```bash
nvidia-smi -q | grep -A 4 "Row Remapping"
```
If Row Remapping states "Failed" or "No remaining rows available", the GPU has sustained permanent physical damage.
4. **Replacement**: RMA the physical GPU card or request a hardware node replacement from your cloud provider.

#### Prevention
* Enable the NVIDIA GPU Operator's **GPU Feature Discovery** to label nodes with active ECC issues automatically.
* Implement a Kubernetes Controller (like **Kube-Node-Agent** or **Node Problem Detector**) that monitors system logs for Xid errors and automatically taints nodes with `gpu-healthy=false:NoSchedule`.

---

### Incident 2: Host-to-Device Driver & CUDA Mismatch

#### Symptoms
A data scientist attempts to deploy a new PyTorch container, but the Pod remains in `CrashLoopBackOff` or the container log prints:
```text
UserWarning: CUDA initialization: CUDA driver version is insufficient for CUDA runtime version
```

#### Detection
Check Pod status and describe the Pod:
```bash
kubectl describe pod inference-api-69fc7 -n serving
```
You see the container exiting immediately. The container logs show PyTorch is unable to locate a compatible driver.

#### Investigation
Check the installed host driver version:
```bash
nvidia-smi
```
Output:
```text
NVIDIA-SMI 525.60.13    Driver Version: 525.60.13    CUDA Version: 12.0
```
Next, check the CUDA runtime version packed inside the user’s Docker image:
```bash
docker run -it --entrypoint /bin/bash <user-image-name> -c "ldconfig -p | grep libcudart"
```
Or check PyTorch's compiled CUDA version inside the container:
```bash
python3 -c "import torch; print(torch.version.cuda)"
```
Output:
```text
12.4
```

#### Root Cause
The host kernel driver version is `525.60.13` (which supports up to CUDA 12.0). However, the application inside the container was compiled using **CUDA Toolkit 12.4**. The low-level User-Space driver API (`libcuda.so`) mapped into the container by the NVIDIA Container Runtime is too old to support the newer entrypoints requested by the container's CUDA 12.4 runtime.

#### Resolution
You have two choices:
1. **Option A (Infrastructure-level - Recommended)**: Upgrade the host node drivers to a version $\ge$ `550.54.14` (which fully supports CUDA 12.4).
2. **Option B (Application-level)**: Downgrade the CUDA runtime or PyTorch image used by the user to compile against CUDA 12.0.

#### Prevention
* Enforce **CUDA Forward Compatibility** matching rules using Kubernetes mutating webhooks.
* Implement the **NVIDIA GPU Operator** with automated dynamic driver updates via containers, decoupling host OS life-cycles from CUDA versions.

---

### Incident 3: Network-Bound GPU Starvation (The "AllReduce" Bottleneck)

#### Symptoms
During a multi-node distributed training run (using PyTorch DDP / NCCL), the total training time is 5x slower than expected. High GPU utilization is reported, but training progress is extremely slow.

#### Detection
Prometheus shows `DCGM_FI_DEV_GPU_UTIL` is near 100%, but:
1. `DCGM_FI_DEV_POWER_USAGE` is sitting at only 40% of TDP (e.g., 160W instead of 400W on an A100).
2. NCCL logs are flooded with long synchronization timeouts.

#### Investigation
Enable NCCL debug logging by setting environment variables inside your training Pod spec:
```yaml
env:
  - name: NCCL_DEBUG
    value: "INFO"
  - name: NCCL_DEBUG_SUBSYS
    value: "INIT,COLL"
```
Re-run the training and check logs:
```text
node-0: NCCL INFO Ring 00 : 0[0] -> 1[1] [via PCIe]
node-0: NCCL INFO Ring 01 : 1[1] -> 0[0] [via PCIe]
node-0: NCCL INFO NCCL WARN: Using slow PCIe interface. No InfiniBand or RoCE found.
```

#### Root Cause
The training cluster was deployed across standard Ethernet instances without InfiniBand or RoCE (RDMA over Converged Ethernet) network adapters. In multi-node distributed training, gradients must be averaged across all nodes during the backward pass (the `AllReduce` phase) at every step. Because of the missing RDMA connection, PyTorch had to fall back to transferring gigabytes of gradients over a standard 10 Gbps Ethernet connection via the host CPU's TCP/IP stack. This caused the GPUs to sit completely idle (drawing very little power) while waiting for network transfers to complete.

#### Resolution
1. Re-deploy the workloads onto nodes configured with **GPUDirect RDMA** interfaces (such as AWS `p4de.24xlarge` or Azure `NDv4` instances with 800 Gbps InfiniBand interfaces).
2. If network hardware cannot be changed, switch your model training architecture from standard Data Parallelism to **DeepSpeed ZeRO-3 with CPU Offloading**, or implement aggressive **Gradient Accumulation** to reduce the frequency of network updates.

#### Prevention
* Block multi-node distributed Pods from scheduling on non-RDMA nodes by configuring strict node affinity rules:
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: network-speed
              operator: In
              values:
                - infiniband-800g
```

---

### Incident 4: Thermal Throttling Silent Degradation

#### Symptoms
An inference service running on a Kubernetes node starts returning high latency spikes (p99 increases from 50ms to 2500ms). The GPU does not crash or throw exceptions.

#### Detection
Verify active thermal violations:
```bash
nvidia-smi -q -d PERFORMANCE
```
Output:
```text
Performance State
    Clocks Throttle Reasons
        HW Thermal Slowdown     : Active    <-- CRITICAL: Thermal throttling is ON!
        SW Power Cap            : Inactive
```

#### Investigation
Check current core temperatures:
```bash
nvidia-smi --query-gpu=temperature.gpu,clocks.current.graphics --format=csv -i 0
```
Output:
```text
temperature.gpu, clocks.current.graphics [MHz]
87, 450 MHz    <-- Note: Clocks should be ~1400-1900 MHz!
```
The GPU temp has reached 87°C, forcing the internal firmware to aggressively scale down the graphics core clocks to 450 MHz (a 4x performance reduction) to prevent permanent silicon breakdown.

#### Root Cause
A physical fan failure on the server node, or a clogged dust filter in the server chassis blocking fresh airflow.

#### Resolution
1. Drain the node in Kubernetes:
```bash
kubectl drain node-gpu-12.cluster.local --ignore-daemonsets
```
2. Trigger an automated hardware alert to replace the chassis fan or clean the physical heat sink.

#### Prevention
* Implement Prometheus alert rules on `DCGM_FI_DEV_THERMAL_VIOLATION > 0`.
* Implement a daemonset that exports temperature metrics and automatically taints nodes with `thermal-throttling=true` if temperature exceeds 80°C.
