# GPU & Kubernetes Mastery Guide
## Section 9: The NVIDIA Kubernetes Ecosystem Deep Dive

---

### 9.1 Component Breakdown

Manually installing drivers, container runtimes, monitoring agents, and partitioning tools across hundreds of Kubernetes nodes is operationally impossible. To solve this, NVIDIA created the **GPU Operator**, which packages the entire ecosystem into a single unified control loop.

To operate this platform, you must understand what each sub-component does and how they interact:

```
========================================================================
                     THE NVIDIA GPU OPERATOR STACK
========================================================================
 [ Node Feature Discovery (NFD) ] -> Scans hardware, labels node with PCI details
                ↓
 [ GPU Feature Discovery (GFD) ]  -> Scans GPU specs, adds 'nvidia.com/gpu' labels
                ↓
 [ Driver Container ]             -> Compiles & loads kernel modules (nvidia.ko)
                ↓
 [ Container Toolkit Container ]  -> Installs OCI hooks & configures containerd
                ↓
 [ Device Plugin DaemonSet ]      -> Registers 'nvidia.com/gpu' with local Kubelet
                ↓
 [ MIG Manager ]                  -> Configures physical hardware MIG slices
                ↓
 [ DCGM Exporter DaemonSet ]      -> Exposes Prometheus telemetry on port 9400
========================================================================
```

#### 1. Node Feature Discovery (NFD)
* **Role**: A Kubernetes-native daemon that scans the physical host node for hardware capabilities (e.g., CPU instructions like AVX-512, PCI devices, kernel versions) and labels the Kubernetes Node object accordingly.

#### 2. GPU Feature Discovery (GFD)
* **Role**: Works alongside NFD, but focuses exclusively on the GPU hardware. It queries NVML and adds hyper-specific GPU labels to the Node (e.g., VRAM size, architecture family, product model, CUDA capabilities).

#### 3. NVIDIA Container Toolkit
* **Role**: Modifies the local container runtime (such as `containerd` or `CRI-O`) on the host. It installs the `nvidia-container-runtime-hook` which intercept OCI container startup commands, injecting driver binaries and direct `/dev/nvidia*` device nodes into the container namespace.

#### 4. NVIDIA Device Plugin
* **Role**: A DaemonSet that runs on every GPU node. It registers itself with the Kubelet's Device Plugin API, discovers how many physical GPUs are on the node, and handles the allocation and routing of specific physical GPU PCI paths to scheduled containers.

#### 5. DCGM Exporter
* **Role**: Operates as a lightweight DaemonSet, reading GPU metrics directly from NVML and presenting them as standard Prometheus metrics.

#### 6. MIG Manager
* **Role**: Dynamically splits massive GPUs (like the A100 or H100) into smaller physical instances (MIG partitions) based on a declarative configuration map.

---

### 9.2 Complete GPU Operator Helm Values Production Configuration

In production, the best practice is to deploy the GPU Operator using its Helm chart. Below is a highly-tuned, production-grade `values.yaml` file that enables driver compilation on-node, MIG dynamic partitioning, and Prometheus scraping.

```yaml
# production-gpu-operator-values.yaml

# 1. Host Kernel Driver Configurations
driver:
  enabled: true
  useDirectPaths: true
  # Compile the driver in-container matching the host's exact kernel headers
  repository: nvcr.io/nvidia
  image: driver
  version: "550.54.14" # Pin the target enterprise driver version
  env:
    - name: PRIVATE_REGISTRY
      value: "true"

# 2. NVIDIA Container Toolkit (Injects drivers into containerd)
toolkit:
  enabled: true
  repository: nvcr.io/nvidia
  image: k8s-container-toolkit
  version: v1.15.0
  env:
    - name: CONTAINERD_CONFIG
      value: "/etc/containerd/config.toml"
    - name: CONTAINERD_SOCKET
      value: "/run/containerd/containerd.sock"

# 3. Device Plugin (Registers nvidia.com/gpu)
devicePlugin:
  enabled: true
  repository: nvcr.io/nvidia
  image: k8s-device-plugin
  version: v0.14.5
  args:
    - "--fail-on-init-error=true"
    - "--pass-device-specs=true"

# 4. GPU Feature Discovery (Applies GPU labels)
gfd:
  enabled: true
  repository: nvcr.io/nvidia
  image: gpu-feature-discovery
  version: v0.14.5

# 5. MIG Management (Dynamic Multi-Instance Partitioning)
mig:
  strategy: mixed # Allows combining different partition sizes on a single GPU

# 6. DCGM Exporter (Exposes monitoring metrics)
dcgmExporter:
  enabled: true
  repository: nvcr.io/nvidia
  image: dcgm-exporter
  version: "3.3.5-3.4.0-ubuntu22.04"
  serviceMonitor:
    enabled: true # Automatically configures Prometheus Operator ServiceMonitor
    interval: 15s
    honorLabels: true

# 7. Node Feature Discovery integration
node-feature-discovery:
  master:
    serviceAccount:
      create: true
  worker:
    config:
      sources:
        pci:
          deviceClassWhitelist:
            - "03" # Discover graphics controllers
            - "02" # Discover network controllers (for RDMA/InfiniBand)
```

To install this in your cluster:
```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update
helm upgrade --install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  -f production-gpu-operator-values.yaml
```
Deploying this architecture creates an autonomous control loop: when a bare-metal node with a physical H100 card joins your Kubernetes cluster, the Operator automatically boots the driver container, configures containerd, registers the GPU with the scheduler, starts exposing Prometheus metrics, and readies the node for massive deep learning workloads without any manual operator intervention.
