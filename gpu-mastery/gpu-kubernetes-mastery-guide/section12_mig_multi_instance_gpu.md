# GPU & Kubernetes Mastery Guide
## Section 12: Multi-Instance GPU (MIG) Deep Dive

---

### 12.1 Understanding MIG Architecture (A100 vs. H100)

**Multi-Instance GPU (MIG)** is a hardware-level virtualization technology introduced in the Ampere architecture (A100) and enhanced in Hopper (H100). It allows you to partition a single physical GPU into up to 7 completely isolated hardware instances.

Unlike software partitioning (such as Time-Slicing), each MIG instance has its own dedicated physical resources:
* **SMs (Streaming Multiprocessors)**
* **VRAM (High-Bandwidth Memory)**
* **Memory Controllers and Decoders**
* **L2 Cache Slices and Bus Bandwidth**

```
========================================================================
                      H100 PHYSICAL GPU (80GB VRAM)
========================================================================
+----------------------------------------------------------------------+
|                 MIG PARTITION 1: "1g.10gb" (10GB VRAM, 1/7th SMs)    |
+----------------------------------------------------------------------+
|                 MIG PARTITION 2: "2g.20gb" (20GB VRAM, 2/7th SMs)    |
+----------------------------------------------------------------------+
|                 MIG PARTITION 3: "4g.40gb" (40GB VRAM, 4/7th SMs)    |
+----------------------------------------------------------------------+
| * Note: All runs inside strict physical and hardware memory walls    |
+----------------------------------------------------------------------+
```

#### MIG Naming Convention: `[Compute_Slices]g.[Memory_Size]gb`
* Example: `1g.10gb`
  * `1g`: Allocates 1 physical GPU Slice (representing ~1/7th of the GPU's compute).
  * `10gb`: Allocates 10GB of physical VRAM.

#### Differences between A100 and H100 MIG
* **A100 MIG**: Offers static configurations. If you split an A100-80GB into seven `1g.10gb` instances, you have exactly seven independent GPUs. If you need a larger instance, you must destroy the partitions and rebuild them.
* **H100 MIG**: Features 2nd-generation MIG. It supports dynamic partitioning with dramatically higher memory bandwidth and double the compute performance per slice compared to the A100. It also supports **Confidential Computing** inside individual MIG slices, encrypting data directly in physical memory.

---

### 12.2 Creating and Configuring MIG Partitions

To configure MIG, you must first enable MIG mode on the physical GPU. This requires unloading active CUDA workloads.

#### Manual Configuration via CLI:
1. Enable MIG Mode on GPU 0:
```bash
nvidia-smi -i 0 -mig 1
```
2. View available MIG profiles:
```bash
nvidia-smi mig -lgip
```
3. Create a `3g.40gb` partition and a `4g.40gb` partition on GPU 0:
```bash
# Create 3g.40gb
nvidia-smi mig -cgi 9,9,9 -C
# Create 4g.40gb
nvidia-smi mig -cgi 19,19,19,19 -C
```

#### Verification:
```bash
nvidia-smi
```
The output will now display two distinct, independent GPU devices, each with its own UUID.

---

### 12.3 Managing and Scheduling MIG in Kubernetes

In a Kubernetes environment managed by the **GPU Operator**, you do not create partitions manually. Instead, you use the **MIG Manager** to partition GPUs dynamically using a declarative ConfigMap.

#### Step 1: Define the Partition Configurations
Create a custom ConfigMap detailing your desired layouts:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: default-mig-config
  namespace: gpu-operator
data:
  # Split 1 physical GPU into seven 1g.10gb instances
  all-1g-10gb: |-
    version: v1
    mig-configs:
      all-1g.10gb:
        - devices: all
          mig-enabled: true
          mig-devices:
            "1g.10gb": 7
  # Split 1 physical GPU into one 3g.40gb and one 4g.40gb instance
  mixed-3g-4g: |-
    version: v1
    mig-configs:
      mixed-3g-4g:
        - devices: all
          mig-enabled: true
          mig-devices:
            "3g.40gb": 1
            "4g.40gb": 1
```

#### Step 2: Apply the Label to the Target Node
To trigger the MIG Manager to repartition a physical node, apply the corresponding configuration label:
```bash
kubectl label node node-gpu-05.cluster.local nvidia.com/mig.config=all-1g-10gb --overwrite
```
The MIG Manager daemon running on `node-gpu-05` will detect the label, drain any active workloads, re-configure the hardware partitions via NVML, and re-register the node’s extended resources with Kubelet.

#### Step 3: Schedule Workloads onto MIG Slices
The GPU Operator registers these partitions as specialized resources. Instead of asking for `nvidia.com/gpu: 1`, you request the specific partition size:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: whisper-speech-to-text
  namespace: ml-platform
spec:
  containers:
    - name: whisper
      image: openai/whisper:latest
      resources:
        requests:
          nvidia.com/mig-1g.10gb: "1" # Request exactly one 10GB hardware slice
        limits:
          nvidia.com/mig-1g.10gb: "1"
```

---

### 12.4 Production Best Practices & Limitations of MIG

#### Benefits
* **Cost Efficiency**: You can run 7 completely separate developers or models (e.g., small embeddings models, Whisper transcription, tabular classifiers) on a single physical $30,000 H100 card.
* **Security & Reliability**: One container running out of memory or hitting an infinite CUDA loop cannot affect other workloads on the same physical chip.

#### Limitations
* **No Inter-MIG NVLink**: NVLink is physically disabled between MIG partitions on the same GPU. If you have two `3g.40gb` slices, they cannot communicate via high-speed NVLink; they must route traffic over slow PCIe buses.
* **Limited Partitions**: You cannot mix arbitrary partitions. The hardware layout must follow strict geometrical partitioning blocks (e.g., you cannot have a `5g` partition because the hardware blocks are grouped in powers of 2).
* **Static Reconfiguration**: Changing a node's MIG layout from `all-1g-10gb` to `mixed-3g-4g` requires draining *all* active pods on that physical GPU, leading to brief scheduling delays.
