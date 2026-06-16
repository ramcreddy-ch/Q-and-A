# GPU & Kubernetes Mastery Guide
## Section 11: Advanced GPU Scheduling & Sharing

---

### 11.1 GPU Sharing Technologies: Time-Slicing vs. MPS vs. MIG

By default, the Kubernetes device plugin assigns an entire physical GPU exclusively to a single container. If a developer launches a small model or a simple Python script, the GPU will sit largely idle, wasting expensive resources. 

To solve this, you can implement one of three main GPU sharing technologies:

```
===================================================================================
                              GPU SHARING COMPARISON
===================================================================================
1. TIME-SLICING (Software-based)
   [Pod A] -> [  GPU Compute  ] (10ms)  <-- Context Switch (Heavy overhead)
   [Pod B] -> [  GPU Compute  ] (10ms)  <-- No memory/compute boundary isolation
   --------------------------------------------------------------------------------
2. MPS (Multi-Process Service)
   [Pod A] [Pod B] -> [ Unified GPU Context ] <-- Shared memory space
   (Active parallel execution; risk of one crash killing the other)
   --------------------------------------------------------------------------------
3. MIG (Multi-Instance GPU - Hardware-isolated)
   [Pod A] -> [ Hardware Slice 1 (10GB) ] <-- Dedicated SMs & Memory
   [Pod B] -> [ Hardware Slice 2 (10GB) ] <-- Strict hardware physical wall
===================================================================================
```

#### 1. Time-Slicing
* **How it works**: The NVIDIA Device Plugin tricks Kubernetes into thinking a single GPU is actually multiple GPUs (e.g., exposing 1 physical A100 as 4 virtual GPUs). The GPU driver uses a round-robin temporal scheduler. It executes Pod A's work for a brief slice of time (e.g., 10ms), swaps it out, and then executes Pod B's work.
* **Pros**: Simple to set up; works on all GPU architectures (even old Pascal/Turing cards).
* **Cons**: No physical memory or compute isolation. If Pod A allocates too much VRAM, it can cause Pod B to crash with a `CUDA out of memory` error. High context-switching latency.

#### 2. MPS (Multi-Process Service)
* **How it works**: MPS allows multiple different processes to share the same CUDA context. Instead of context switching sequentially (like Time-Slicing), MPS merges the execution queues of both Pods, running their operations **simultaneously** on different SMs of the same GPU.
* **Pros**: Highly efficient; near-zero overhead; allows resource limits (e.g., Pod A can be limited to use only 40% of the GPU's compute).
* **Cons**: Shared address space. If Pod A crashes due to a memory corruption event, the entire shared CUDA context can crash, bringing down Pod B as well.

#### 3. MIG (Multi-Instance GPU)
* **How it works**: A hardware-level partitioning technology available on Ampere and Hopper GPUs. It splits a single physical GPU into up to 7 distinct, fully isolated GPU instances. Each instance has its own dedicated physical SMs, memory controllers, and VRAM.
* **Pros**: Absolute physical and security isolation. A crash or OOM on one instance has zero impact on other instances.
* **Cons**: Static partitioning (requires restarting the GPU to change configurations); only available on high-end enterprise GPUs (A100, H100, H200).

---

### 11.2 Time-Slicing Production Configuration

To configure Time-Slicing, create a `ConfigMap` detailing how many virtual replicas of each GPU you want to expose:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: device-plugin-config
  namespace: gpu-operator
data:
  any-gpu: |-
    version: v1
    sharing:
      timeSlicing:
        resources:
          - name: nvidia.com/gpu
            replicas: 4   # Split every single physical GPU into 4 virtual instances
```

Specify this ConfigMap in your GPU Operator Helm chart deployment values to instantly enable time-slicing across your nodes.

---

### 11.3 Gang Scheduling with Kueue / Volcano

When training massive models using multi-node configurations, standard Kubernetes scheduling is highly vulnerable to **Resource Deadlocks**.

#### The Resource Deadlock Scenario
Imagine you have a training job that requires **16 GPUs** (2 nodes of 8 GPUs) to execute. 
* Job A starts and schedules on Node 1, consuming **8 GPUs**.
* Job B starts concurrently and schedules on Node 2, consuming **8 GPUs**.
* Both Job A and Job B are now waiting for an additional 8 GPUs to materialize. Because they cannot get their required 16 GPUs, they both hang indefinitely, refusing to release their current 8 GPUs. This is a classic scheduling deadlock.

#### Gang Scheduling (All-or-Nothing)
Gang Scheduling engines like **Kueue** or **Volcano** solve this. They intercept Pod placement. Instead of scheduling individual Pods, they schedule **PodGroups**.
* A PodGroup is only scheduled if the cluster has enough aggregate available resources to run **every single Pod in the group simultaneously**. If resources are insufficient, the entire group is queued, preventing partial allocation and deadlocks.

```yaml
# Kueue ResourceFlavor & ClusterQueue Configuration
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: gpu-training-queue
spec:
  namespaceSelector: {} # Allow all namespaces to submit
  cohort: gpu-pool
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: h100-sxm5
          resources:
            - name: "nvidia.com/gpu"
              nominalQuota: 32 # Total physical H100 GPUs in the cluster
```

Any batch training job submitted via Volcano or Kueue will queue safely, executing only when a full multi-node block of GPUs is entirely free. This maximizes cluster throughput and prevents expensive idling.
