# GPU & Kubernetes Mastery Guide
## Section 10: GPU Operator In-Depth & Live Upgrades

---

### 10.1 Operator State Machine and Lifecycle

The **NVIDIA GPU Operator** is implemented as a standard Kubernetes Custom Resource Definition (CRD) called `ClusterPolicy`. The Operator acts as a state machine, orchestrating the installation of each daemon container sequentially on every node.

```
       +---------------------------------------------+
       |             Driver Container                |  <-- Compiles & inserts nvidia.ko
       +---------------------------------------------+
                              ↓ [Success]
       +---------------------------------------------+
       |             Toolkit Container               |  <-- Injects config & restarts runtime
       +---------------------------------------------+
                              ↓ [Success]
       +---------------------------------------------+
       |           Device Plugin Container           |  <-- Registers GPU allocatable capacities
       +---------------------------------------------+
                              ↓ [Success]
       +---------------------------------------------+
       |           DCGM Exporter DaemonSet           |  <-- Begins publishing metrics
       +---------------------------------------------+
```

If any layer of the state machine fails (e.g., driver fails to compile), the entire downstream pipeline halts for that node.

---

### 10.2 Common GPU Operator Troubleshooting & Failure Scenarios

#### Failure 1: Driver Container Stuck in `CrashLoopBackOff` due to Kernel Header Mismatch
* **Symptom**: After a node OS patching event, the GPU Operator fails to run. The driver container is stuck crash-looping.
* **Logs from Driver Container**:
```text
ERROR: Cannot find a compatible toolchain or kernel headers for running kernel 6.5.0-1018-aws.
Please install the appropriate kernel headers (linux-headers-6.5.0-1018-aws) and try again.
```

##### Root Cause
The on-node compilation container requires the host kernel’s exact header packages to build the proprietary `nvidia.ko` binary. If the host operating system was recently patched or updated to a newer kernel version, but the node’s package repositories are not reachable or the corresponding header package is missing, compilation will fail.

##### Resolution
1. Verify what kernel is running on the host node:
```bash
uname -r
```
2. Check if host headers are installed:
```bash
dpkg -l | grep linux-headers-$(uname -r)
```
3. If missing, manually install them on the host or ensure your proxy/firewall allows the driver container to access the package mirrors:
```bash
sudo apt-get install -y linux-headers-$(uname -r)
```
4. If the node has no outbound internet access, you must build a custom **Precompiled Driver Image** containing the compiled modules for your target kernel, and specify that image in the `ClusterPolicy` Helm config.

---

#### Failure 2: Containerd Runtime Injection Failure
* **Symptom**: The driver is loaded on the host, but scheduled pods fail with:
```text
RuntimeError: Found no NVIDIA driver on your system.
```

##### Root Cause
The `nvidia-container-toolkit` container failed to inject the NVIDIA OCI configuration hooks into the local `containerd` config file `/etc/containerd/config.toml`, or failed to signal containerd to reload its configuration.

##### Investigation
1. SSH into the node and inspect the containerd configuration:
```bash
cat /etc/containerd/config.toml | grep nvidia
```
If you do not see lines detailing the `nvidia-container-runtime` plugin or execution hooks, the injection failed.
2. Check if the OCI hook is registered:
```bash
ls -la /usr/share/containers/oci/hooks.d/
```

##### Resolution
Restart the container toolkit daemon to trigger re-injection:
```bash
kubectl rollout restart ds/nvidia-container-toolkit -n gpu-operator
```
If that fails, manually patch `/etc/containerd/config.toml` to register the runtime and reload containerd:
```bash
sudo systemctl restart containerd
```

---

### 10.3 Production Live Upgrade Strategy (No-Downtime Upgrades)

Historically, upgrading the NVIDIA driver required draining all nodes, stopping all GPU pods, and rebooting. In massive production clusters running continuous inference APIs or multi-week training jobs, this is incredibly expensive.

NVIDIA introduced **Driver Auto-Upgrade (Safe Live Upgrades)** via the GPU Operator.

#### How Live Upgrades Work
1. **Dynamic Driver Unload/Reload**: The driver container can stop, compile the new driver, and reload it into the running kernel without rebooting the host.
2. **Container Pause / Resume**: Utilizing NVIDIA's **Open Kernel Modules (OOM)**, active GPU contexts of workloads that do not use physical GPU virtualization can survive the driver reload if properly configured.
3. However, for maximum safety in production, we use **Graceful Drain & Rollout** of the Operator:

```yaml
# Upgrade configuration in ClusterPolicy
spec:
  driver:
    upgradeStrategy:
      enabled: true
      autoUpgrade: true
      maxUnavailable: 1 # Upgrade nodes one-by-one
      drain:
        enabled: true
        force: true
        deleteEmptyDirData: true
        timeoutSeconds: 300
```

When you update the GPU Operator Helm values with a new driver version:
1. The Operator automatically picks the first node.
2. It taints the node to prevent new workloads.
3. It performs a Kubernetes eviction of all active GPU pods on that node.
4. Once empty, it stops the driver container, unloads the old kernel module, loads the new kernel module, and reloads containerd.
5. It untaints the node and moves to the next node in the pool. This guarantees continuous, zero-downtime rolling upgrades across your cluster.
