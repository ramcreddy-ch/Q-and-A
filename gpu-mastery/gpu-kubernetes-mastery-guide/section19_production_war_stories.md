# GPU & Kubernetes Mastery Guide
## Section 19: Production War Stories (Real-World Incidents)

---

This section documents real-world production incidents, outlining the symptoms, step-by-step investigation flows, resolutions, and long-term architectural prevention strategies.

---

### War Story 1: The Infinite PyTorch Caching Allocator Loop

* **Workload**: Real-Time Llama-3-70B serving on 4x A100 (80GB) using vLLM.
* **Impact**: CPU usage pegged at 100% across all cores. Inference API latency skyrocketed from 20ms to $>10,000$ms. Pod liveness probes failed, leading to continuous, cascading container restarts.

#### Investigation Flow
1. **Initial Alert**: Prometheus fired high latency warnings for the `serving` namespace.
2. **First Check**: Checked GPU utilization and VRAM using `nvidia-smi`.
   * GPU core utilization was at **0%**.
   * VRAM usage was completely full on all 4 cards (80GB/80GB).
3. **CPU Profiling**: Run `top` on the host node. CPU usage was at 100% across all 64 physical CPU cores, entirely consumed by the `vllm` Python process.
4. **Thread Tracing**: Attached a Python thread profiler (`py-spy`) to the running container process:
```bash
py-spy dump --pid <vllm-pid>
```
The thread dump showed thousands of active allocations stuck inside the internal PyTorch Caching Allocator method `allocate()` -> `malloc_with_retry()`.

#### Root Cause
Under a heavy concurrent user-request spike, the vLLM engine attempted to allocate a new physical memory page for a long KV cache sequence. 
Because the physical VRAM was completely full and heavily fragmented, the PyTorch Caching Allocator was unable to find a contiguous block of memory. 
Instead of instantly throwing a "CUDA out of memory" error and failing the request, PyTorch's allocator entered a retry loop: it executed `cudaFree(0)` (which flushes the internal cache) and scanned the memory blocks again. Because this was a tight loop executing in Python user-space on the host CPU, it locked up the Python interpreter completely, causing a total freeze of the inference engine while pinning the host CPU.

#### Resolution
1. **Immediate**: Force-killed the frozen container using `kubectl delete pod --force --grace-period=0`.
2. **Short-Term**: Configured the vLLM engine parameter `--gpu-memory-utilization` to `0.90` (reducing the max allocation limit from the default `0.95`), leaving a safe 10% buffer for dynamic allocations.
3. **Long-Term**: Decreased the maximum sequence length parameter in the model serving configurations to match the physical VRAM pages, and enabled vLLM's automatic **request preemption** to safely drop low-priority requests instead of allowing the allocator to enter a retry loop.

---

### War Story 2: The Silent NVLink Fault (The "Degraded Speed" Trap)

* **Workload**: Multi-Node Pre-training (64x H100 SXM5 GPUs across 8 nodes) of a 70B parameter model.
* **Impact**: Total training step time suddenly increased by **350%**. No errors or crashes were thrown. The model continued to train, but at a catastrophic speed and cost.

#### Investigation Flow
1. **Initial Alert**: ML engineers noticed the logs showed training throughput dropped from 120,000 tokens/sec to 34,000 tokens/sec.
2. **GPU Metric Analysis**:
   * All 64 GPUs reported `DCGM_FI_DEV_GPU_UTIL` at **100%**.
   * However, `DCGM_FI_DEV_POWER_USAGE` was sitting at only **35% of TDP** (245W instead of 700W) on `node-gpu-04` and `node-gpu-05`.
3. **Network Inspection**: Checked InfiniBand network interfaces. Traffic was moving, but throughput was low.
4. **Interconnect Analysis**: Run NVLink error check on the suspected nodes:
```bash
nvidia-smi nvlink --status
```
On `node-gpu-04`, the output showed:
```text
GPU 0: NVLink Link 0: Active
GPU 0: NVLink Link 1: Inactive   <-- CRITICAL: NVLink 1 is INACTIVE!
GPU 0: NVLink Link 2: Active
```
On `node-gpu-04`, 4 out of the 18 physical NVLink channels had failed and entered an "Inactive" state due to signal degradation.

#### Root Cause
A physical ASIC interconnect fault on the motherboard's HGX baseboard. Because some NVLink channels failed, the GPU driver automatically routed the high-frequency training tensors over the remaining active NVLink lanes. When those became saturated, it fell back to routing the remaining traffic over the slow PCIe motherboard bus. Because PCIe is 14x slower than NVLink, this created a massive, silent communication bottleneck.

#### Resolution
1. **Immediate**: Drained `node-gpu-04` and rescheduled the training run across the remaining 7 healthy nodes.
2. **Hardware Action**: Dispatched an on-site data center technician to swap out the physical motherboard/HGX baseboard for the faulty node.

#### Lessons Learned
* **Never rely solely on GPU Utilization metrics**. A GPU can report 100% utilization while its execution pipelines are completely stalled waiting for communications.
* **Always monitor GPU Power Draw**. Power consumption is a direct proxy for actual floating-point compute activity.
* Set up real-time alerting on the Prometheus metric `DCGM_FI_DEV_NVLINK_ERROR_COUNT > 0` to immediately intercept physical link failures.

---

### War Story 3: The Ghost of CUDA Contexts Past (Silent VRAM Leak)

* **Workload**: Shared development cluster running Jupyter Notebooks and interactive training.
* **Impact**: Cluster showed 0 active pods running, yet `nvidia-smi` reported VRAM was almost fully occupied, preventing new data science jobs from scheduling.

#### Investigation Flow
1. **Initial Alert**: Developers reported they could not launch new notebooks because of `Insufficient nvidia.com/gpu` scheduling errors.
2. **First Check**: Run `kubectl get pods -A` and verified that no pods were requesting GPUs.
3. **Node Inspection**: Logged into a GPU node directly and run `nvidia-smi`.
   * VRAM was at 78GB / 80GB utilized.
   * Under the "Processes" list, there was a running process:
```text
Processes:
  GPU      PID   Type   Process name                             Required VRAM
  ============================================================================
    0   124512      C   python3                                         78120MiB
```
4. **Process Tracing**: Traced the PID `124512` back to the host system namespace:
```bash
ps -ef | grep 124512
```
The output showed the process belonged to a Jupyter Notebook server container that had been deleted by Kubernetes 6 hours prior!

#### Root Cause
When Kubernetes deletes a Pod, the Kubelet signals the container runtime (containerd) to stop the container using a `SIGTERM` signal, followed by a `SIGKILL` if it does not exit within 30 seconds. 
In this case, the developer's Jupyter container was running a custom C++ extension. The extension caught the `SIGTERM` but entered an infinite loop trying to release a resource, preventing a clean exit.
When containerd timed out and sent a `SIGKILL`, the kernel terminated the container namespace, but due to a known bug in the older container runtime integration, the low-level physical CUDA context remained registered with the host kernel driver (`nvidia.ko`). The GPU memory space was never garbage-collected by the driver, creating a "ghost" memory leak on the node.

#### Resolution
1. **Immediate**: Manually killed the leaked host process:
```bash
sudo kill -9 124512
```
VRAM instantly dropped back to 0.
2. **Long-Term**: Upgraded the host container runtime to the latest version of `containerd`, and updated the NVIDIA Container Toolkit to ensure all OCI hook resources are aggressively cleaned up upon container death, regardless of how the container exits.
3. Configured an automated daily CronJob daemonset to scan nodes for any active CUDA processes that do not map to an active, running container PID.

---

### War Story 4: The Driver Upgrade Cascading Kernel Panic

* **Workload**: Multi-tenant GPU cluster running live production web services and model APIs.
* **Impact**: Automated upgrade of the NVIDIA GPU Operator triggered a cascade of host kernel panics, taking down 12 bare-metal H100 nodes and causing a complete platform outage.

#### Investigation Flow
1. **Initial Alert**: Multiple nodes suddenly went into a `NotReady` state in Kubernetes.
2. **Host Logging**: Logged into the physical IPMI out-of-band console of a crashed node. The screen showed a host kernel trace and a **Kernel Panic** state:
```text
BUG: unable to handle kernel NULL pointer dereference at 0000000000000028
IP: nvidia_modeset_rm_ops_alloc+0x24/0x90 [nvidia_modeset]
...
Kernel panic - not syncing: Fatal exception in interrupt
```
3. **Operator Inspection**: Investigated the GPU Operator `ClusterPolicy` and discovered that the Helm charts were recently upgraded with automatic driver upgrades enabled (`upgradeStrategy.autoUpgrade: true`).

#### Root Cause
The GPU Operator attempted to perform a rolling live upgrade of the NVIDIA kernel driver from version `535.x` to `550.x`.
The Operator stopped the driver container and executed `rmmod nvidia` to unload the old module from the host kernel.
However, several active user-space container processes (which had bypassed Kubernetes and mapped `/dev/nvidia*` paths directly) were still actively writing to the memory registers. 
When the kernel driver was forced to unload while active page-fault transactions were pending in hardware, it triggered a NULL pointer dereference in the kernel space, causing an immediate, fatal kernel panic. As the nodes crashed, Kubernetes attempted to reschedule the lost pods onto remaining nodes, which were *also* in the middle of driver upgrades, triggering a cascading chain-reaction panic across the entire cluster.

#### Resolution
1. **Immediate Action**: Disabled automatic upgrades in the GPU Operator `ClusterPolicy` and performed a hard physical reboot of the crashed bare-metal servers via IPMI.
2. **Workaround**: Configured the driver upgrade strategy to require manual confirmation and strict node drain policies.
3. **Long-Term Prevention**: Configured strict `preStop` hooks on all GPU containers to cleanly close CUDA contexts, and mapped a specialized DaemonSet to monitor if any active contexts are open on `/dev/nvidia*` before the operator is allowed to trigger a module unload.

---

### War Story 5: The Karpenter Autoscaler "Flapping" Storm

* **Workload**: Highly dynamic auto-scaling public web API serving image generation (Stable Diffusion) on L40S nodes.
* **Impact**: New L40S nodes were constantly booted and then immediately terminated every 5 minutes, causing client request timeouts, slow scheduling, and massive cloud billing costs.

#### Investigation Flow
1. **Initial Alert**: Finance flagged a 300% spike in AWS compute spend.
2. **Autoscaler Log Inspection**: Analyzed Karpenter controller logs:
```text
2026-06-13T16:15:24Z INFO controller.node  deprovisioning node node-gpu-12a (underutilized)
2026-06-13T16:17:10Z INFO controller.node  provisioning node with 1x L40S for pending pod
```
3. **Metric Tracking**: Correlated Karpenter events with KEDA metrics. The number of waiting requests in the queue would spike above the threshold, triggering KEDA to scale the deployment. As soon as Karpenter booted a new node (taking ~45 seconds) and the pods initialized (taking another 30 seconds to load the 15GB model weights), the traffic spike would have already subsided. The new pods would see 0 traffic, Karpenter's consolidation policy would instantly flag the node as underutilized, and terminate it.

#### Root Cause
The KEDA metric evaluation window was set too narrow, and Karpenter's consolidation parameters were too aggressive. This created a classic **feedback loop (flapping)**: the system reacted instantly to brief, sub-second traffic spikes, provisioned expensive nodes that arrived too late to handle the traffic, and then immediately killed them before they could provide any real value.

#### Resolution
1. **Scale-Down Stabilization**: Configured a `cooldownPeriod` and `scaleDown` stabilization window of **600 seconds** (10 minutes) inside the KEDA `ScaledObject` configuration to prevent rapid scaling down.
2. **Karpenter Consolidation Delay**: Patched the Karpenter NodePool consolidation parameters, adding a strict `consolidateAfter` delay of 15 minutes to guarantee that a newly booted node is kept alive for a minimum period to absorb potential follow-up spikes.
3. **Model Caching**: Pre-baked the model weights directly into the node's local machine image (AMI) using host-level NVMe caching, reducing pod startup initialization time from 30 seconds to 2 seconds, allowing the system to react fast enough to utilize the newly booted nodes during traffic spikes.
