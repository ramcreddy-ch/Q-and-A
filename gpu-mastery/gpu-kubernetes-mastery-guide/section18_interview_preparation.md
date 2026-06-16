# GPU & Kubernetes Mastery Guide
## Section 18: Staff-Level Interview Preparation

---

This section contains highly technical, scenario-based interview questions designed for Staff AI Platform, Principal MLOps, and GPU Infrastructure positions. Each question is analyzed across three seniority levels to show the depth of knowledge required for Principal and Architect roles.

---

### Category 1: GPU Core Architecture & Hardware Systems

#### Question 1: What is the physical difference between NVLink and PCIe, and how does the presence of an NVSwitch backplane change your distributed training strategy?

##### Expected Answer (Junior/Mid Level)
"PCIe is the standard motherboard slot that connect graphics cards to the computer. NVLink is a faster connector made by NVIDIA that connects GPUs directly to each other. An NVSwitch is a chip that helps connect many GPUs together so they can talk faster."

##### Senior-Level Answer
"PCIe Gen 5 provides up to 128 GB/s bidirectional bandwidth and operates over a host root complex, which means all communication between GPUs must go through the CPU's memory bus, causing a bottleneck. NVLink 4, however, is a direct GPU-to-GPU interconnect providing 900 GB/s bidirectional bandwidth. It bypasses the PCIe bus completely. 
In a system without NVSwitch (like standard PCIe cards linked by physical bridge cables), NVLink only works in point-to-point pairs. In an HGX system with NVSwitches, all NVLinks from every GPU terminate at the NVSwitch crossbar. This turns the interconnect into a non-blocking fabric: any GPU can talk to any other GPU at full 900 GB/s bandwidth simultaneously, which is critical for scaling Tensor Parallelism."

##### Architect-Level Answer
"From a systems architecture perspective, NVLink and NVSwitch decouple GPU interconnectivity from host-board topologies. With PCIe, multi-GPU scaling is physically capped by the host CPU's PCIe lane count and root-complex routing paths. 
When designing for distributed training (e.g., Megatron-LM), the physical presence of NVSwitch dictates our sharding topologies:
1. **Intra-node (Within Server)**: Because NVSwitch provides a high-speed, non-blocking crossbar, we can scale **Tensor Parallelism (TP)** up to 8 GPUs. TP relies on high-frequency, low-latency `AllReduce` operations.
2. **Inter-node (Across Servers)**: Once we cross the host node boundary, NVLink is no longer natively available. We must route traffic over high-speed networks. Because of this, we must restrict TP to the node (max TP=8) and scale horizontally using **Pipeline Parallelism (PP)** and **Data Parallelism (DP/ZeRO)** over InfiniBand/RoCE, as PP and DP have far lower communication frequencies.
If we attempted to scale TP=16 across two nodes without a unified NVLink Network (like NVLink Switch System), the `AllReduce` latency over standard networking would completely stall the execution pipeline, rendering the extra compute useless."

---

#### Question 2: Explain the "Transformer Engine" in Hopper and Blackwell architectures. How does it maintain model accuracy while utilizing ultra-low precision FP8 or FP4 formats?

##### Expected Answer (Junior/Mid Level)
"The Transformer Engine automatically uses FP8 (8-bit floating point) math instead of FP16 to make things run faster and save memory. It keeps the model accurate by converting numbers back and forth when needed."

##### Senior-Level Answer
"The Transformer Engine is a software and hardware integration in Hopper (and upgraded in Blackwell) that dynamically manages precision formats during training and inference. FP8 has two formats: **E4M3** (4 exponent, 3 mantissa bits) which is optimized for precision, and **E5M2** (5 exponent, 2 mantissa bits) which has higher dynamic range but lower precision.
During execution, the Transformer Engine monitors the distribution of weights and activation tensors at each layer. It calculates scaling factors dynamically and converts tensors to FP8 for the matrix multiplication (GEMM) on Tensor Cores, while accumulating the results in FP16 or FP32 to prevent underflow/overflow. This delivers the speed of FP8 with the numerical stability of FP16."

##### Architect-Level Answer
"The architectural significance of the Transformer Engine is its solution to the numerical stability problem in low-precision training. In standard deep learning, directly quantizing a model to 8-bit or 4-bit causes severe degradation because gradients can have a dynamic range spanning several orders of magnitude.
The Transformer Engine implements a **Dynamic Scaling and Calibration** loop:
1. At each layer's execution, the engine tracks the maximum absolute values ($AMAX$) of the input tensors in a history buffer.
2. It calculates an optimal scaling factor $S$ that scales the tensor values to occupy the maximum representative range of the FP8 format without saturating (overflowing).
3. The hardware performs the high-speed GEMM on FP8 Tensor Cores.
4. During the backward pass, it dynamically switches to the higher-range format (E5M2) for gradients, since gradient values are highly sensitive to underflow.
In Blackwell, this is scaled down to FP4 (supporting E2M1 and E3M0 structures) via dual-die routing. This dynamic scaling is fully abstracted away from the ML developer, allowing for a 2x throughput increase during pre-training and 4x during inference with $<0.5\%$ loss in perplexity."

---

#### Question 3: Explain "Register Spilling" and "Warp Occupancy" during kernel profiling with Nsight Compute. How do register limits affect thread scalability?

##### Expected Answer (Junior/Mid Level)
"Register spilling happens when a GPU runs out of fast memory for its registers and has to use slower main memory instead. Warp occupancy is the percentage of active threads on the GPU. You want both to be optimized."

##### Senior-Level Answer
"Each Streaming Multiprocessor (SM) has a fixed, physical size Register File (e.g., 256 KB in Hopper). This register file is shared among all active threads allocated to that SM. 
If a custom CUDA kernel uses too many local variables, the compiler cannot fit them into the allocated registers per thread. To prevent failure, the compiler 'spills' these variables into **Local Memory**, which physically resides in slow off-chip Global VRAM. This introduces massive latency.
**Warp Occupancy** is the ratio of active warps on an SM to the maximum supported warps. If each thread in a block requires a high number of registers, the GPU scheduler cannot run as many blocks concurrently on that SM, lowering occupancy and degrading performance."

##### Architect-Level Answer
"From a kernel design and compiler perspective, register usage is the primary constraint on execution parallelism.
1. **The Math**: If an SM supports a maximum of 2,048 threads (64 warps) and has 256 KB of register space (65,536 32-bit registers):
   $$\text{Max Registers Per Thread} = \frac{65,536}{2,048} = \mathbf{32 \text{ Registers}}$$
   If your compiler (`nvcc`) generates a kernel that requires **64 registers per thread**, the hardware scheduler can only schedule a maximum of 1,024 threads on that SM, capping your theoretical **Warp Occupancy at 50%**.
2. **Nsight Compute Profiling**: During profiling, we look at the metric `launch__occupancy_theoretical` vs `launch__occupancy_achieved`. If theoretical occupancy is low, we check `gpc__registers_per_thread`.
3. **Architectural Trade-off**: High occupancy is not always necessary if your kernel is completely memory-bandwidth bound (where threads spend most of their time waiting for VRAM transfers). However, for compute-bound kernels (like GEMMs), maximizing occupancy is critical. We optimize this by:
   - Using the `__launch_bounds__` compiler directive to force `nvcc` to limit register allocation.
   - Restructuring the mathematical formulas to reuse intermediate registers.
   - Utilizing **Shared Memory (SRAM)** explicitly to store block-level matrices instead of relying on individual thread-level registers."

---

### Category 2: Kubernetes GPU Scheduling & Container Runtime

#### Question 4: Walk me through the step-by-step low-level sequence of events when a Pod requesting `nvidia.com/gpu: 1` is scheduled on a bare-metal Kubernetes node.

##### Expected Answer (Junior/Mid Level)
"The Kubernetes scheduler looks for a node that has a free GPU. It assigns the Pod to that node. The node’s container runtime pulls the image and runs the container. The NVIDIA device plugin makes sure the container can see the GPU."

##### Senior-Level Answer
"1. The user submits the Pod spec. The Kube-Scheduler identifies the `resources.limits.nvidia.com/gpu: 1` requirement.
2. The scheduler filters nodes using Node Labels and Node Status, locating a node where `Allocatable` contains at least one GPU. It decrements the allocatable GPU count by 1 on that node.
3. The Kubelet on the target node receives the pod spec and calls the **NVIDIA Device Plugin** via gRPC to allocate a GPU.
4. The Device Plugin selects a specific physical GPU (e.g., PCI Bus ID `0000:01:00.0`, mapped to `/dev/nvidia0`) and returns this environment configuration back to Kubelet.
5. Kubelet invokes the container runtime (e.g., `containerd`) via the Container Runtime Interface (CRI).
6. containerd starts the container creation process and invokes the **NVIDIA Container Runtime Hook** (configured in OCI).
7. This hook queries the host's NVIDIA driver and binds the physical device nodes (`/dev/nvidia*`, `/dev/nvidia-uvm`) and driver libraries (e.g., `libcuda.so`) into the container's root file system.
8. The container starts, and the application can execute CUDA operations."

##### Architect-Level Answer
"This entire pipeline relies on **OCI (Open Container Initiative) prestart hooks** to bridge the barrier between the host kernel space and container user space.
1. **The Scheduler Stage**: Standard Kube-Scheduler treats `nvidia.com/gpu` as an opaque integer value. It does not know if the GPU is an H100 or a T4, which is why we must configure Node Affinity rules based on labels applied by **Node Feature Discovery (NFD)** and **GPU Feature Discovery (GFD)**.
2. **The Kubelet Stage**: Kubelet communicates with the Device Plugin via the `Allocate` gRPC endpoint. The Device Plugin returns a response containing environment variables (like `NVIDIA_VISIBLE_DEVICES=0`) and Mounts (pointing to the target driver files).
3. **The Runtime Stage**: In modern setups utilizing the **NVIDIA Container Toolkit**, containerd uses an OCI runtime spec patcher. The container runtime hook parses `NVIDIA_VISIBLE_DEVICES`. If set to `all` or a specific index, it dynamically intercepts container generation.
4. **The Security/System Boundary**: Crucially, the host's physical kernel driver (`nvidia.ko`) is *never* copied into the container; only the user-space libraries (`libcuda.so`, `libnvidia-ml.so`) are bind-mounted. This is why the host driver version must always be greater than or equal to the CUDA runtime version used to compile the application, unless **CUDA Forward Compatibility** is active, which relies on mapping a custom user-space compatibility library (`libcuda.so` wrapper) into the container namespace."

---

#### Question 5: How do you build a multi-node GPU training scheduling pipeline using Volcano or Kueue while enforcing GPUDirect RDMA affinity?

##### Expected Answer (Junior/Mid Level)
"You use Volcano to run gang scheduling so that all pods start at the same time. You write a YAML file that requests GPUs and networks, and Volcano assigns them to nodes with RDMA."

##### Senior-Level Answer
"To scale multi-node training, we use **Kueue** or **Volcano** to enforce **Gang Scheduling (All-or-Nothing)**. This prevents resource deadlocks where jobs hold partial resources.
To enforce GPUDirect RDMA affinity, we must ensure that the pods are placed on nodes that have both H100 GPUs and high-speed RDMA network interfaces (like ConnectX-7). We do this by:
1. Labeling nodes with RDMA network capability (e.g., `topology.kubernetes.io/network=rdma-800g`).
2. Configuring the PodSpec with explicit `nodeAffinity` targeting those labels.
3. Using Volcano's `PodGroup` CRD to ensure that all tasks in the group are scheduled simultaneously across those specific nodes."

##### Architect-Level Answer
"Enforcing GPUDirect RDMA affinity in a multi-node Kubernetes cluster requires tightly coupling GPU topology scheduling with network topology scheduling.

1. **Topology Awareness**: Inside a modern HGX node, physical GPUs are routed to specific PCIe switches, which in turn map directly to specific **ConnectX network adapters (NICs)**. To achieve true GPUDirect RDMA (bypassing the host CPU entirely during network transfers), a Pod's GPU must be physically routed to the *same* PCIe switch as the NIC.
2. **Kubelet Topology Manager**: We configure the host Kubelet with the **Topology Manager** enabled, using a `single-numa-node` or `restricted` topology policy:
```yaml
# Kubelet config
topologyManagerPolicy: single-numa-node
```
This forces Kubelet to allocate GPU and PCIe NIC resources from the same physical NUMA socket and PCIe tree.
3. **Scheduler Integration (Kueue)**: We define a Kueue `Workload` that references a `ClusterQueue` mapped to our RDMA-capable bare-metal nodes. 
4. **Gang Scheduling Implementation**: Volcano orchestrates the job placement. By using a Volcano `Job` spec with a `minMember` parameter, the controller ensures that the entire distributed training group is scheduled in a single transaction. If a single node in the fabric is degraded or unavailable, Volcano queues the entire job, preventing partial execution states and protecting the network fabric from idle congestion."

---

### Category 3: MLOps & Large-Scale Distributed Architecture

#### Question 6: How would you design a highly available, multi-tenant Kubernetes platform supporting both large-scale LLM pre-training runs (thousands of GPUs) and real-time low-latency LLM serving? How do you prevent noisy-neighbor issues?

##### Expected Answer (Junior/Mid Level)
"I would create two different node pools: one for training and one for serving. I would use namespaces and resource limits to keep the teams separated, and use autoscaling to spin up nodes when needed."

##### Senior-Level Answer
"To separate these workloads effectively, we must isolate them at both the hardware and scheduling layers:
1. **Node Pools**: Create dedicated Node Pools. Training runs on HGX H100 SXM5 nodes with high-speed InfiniBand networking. Serving runs on PCIe-based nodes (e.g., L40S or H100 PCIe) or smaller MIG partitioned instances depending on model sizes.
2. **Scheduling**: Use **Taints and Tolerations** to prevent standard CPU workloads or serving pods from scheduling on the expensive training nodes. Use **Kueue** or **Volcano** for the training workloads to manage job queuing and prevent resource deadlocks.
3. **Noisy Neighbor Prevention**:
   * For training: Workloads are allocated whole nodes exclusively. No sharing.
   * For serving: If sharing is necessary, use **MIG (Multi-Instance GPU)** to guarantee physical hardware-level resource isolation (VRAM and SMs), preventing one tenant's memory spike from causing an OOM in another tenant's pod."

##### Architect-Level Answer
"A resilient, enterprise-grade AI platform architecture must address physical isolation, scheduling deadlocks, network topologies, and cost attribution.

```
==========================================================================================
                              ENTERPRISE MULTI-TENANT ARCHITECTURE
==========================================================================================
                 [ Istio Ingress Gateway / Gateway API ]
                                   ↓
        +--------------------------+--------------------------+
        ↓                                                     ↓
 [ Serving Namespace ]                                 [ Training Namespace ]
 - Requests: nvidia.com/gpu: 1 (or MIG)                 - Requests: nvidia.com/gpu: 8
 - Scaler: KEDA (on queue length)                      - Scheduler: Kueue (Gang Scheduling)
 - Eviction: Disruptions blocked                       - Priority: Low (Preemptible)
        ↓                                                     ↓
 [ NodePool: PCIe L4/L40S / H200 ]                     [ NodePool: HGX H100 SXM5 ]
 - Optimized for memory bandwidth                     - Optimized for NVLink & RDMA
==========================================================================================
```

#### Detailed Architectural Design:
1. **Network Topology Isolation**: Training nodes are configured with **GPUDirect RDMA** over a dedicated, non-blocking InfiniBand Leaf-Spine fabric. We must ensure that training traffic (highly synchronized collective communication) is physically separated from user-facing serving traffic to prevent packet drops and latency spikes.
2. **Resource Queuing & Gang Scheduling (Kueue)**: We implement **Kueue** to manage queue structures. Large pre-training runs are submitted to a `ClusterQueue` with a nominal quota. If a high-priority serving spike occurs, Kueue can trigger the preemptive eviction of low-priority development or fine-tuning jobs, reclaiming those physical nodes within seconds.
3. **Autoscaling and Capacity Management**: We integrate **Karpenter** directly with AWS/Azure fleet APIs. For training, we provision whole bare-metal instances on-demand. To prevent cold-start delays for serving (which can take minutes to boot a GPU node and load a 140GB model), we maintain a warmed "buffer pool" of active instances, using Knative's scale-to-zero capabilities only for low-priority internal APIs.
4. **Data Plane Performance**: Model weights are served via a read-only, high-performance distributed file system (e.g., WekaFS or cached locally via host-level NVMe SSDs). When a new serving pod boots, it pulls the model at 10+ GB/s from the local cache rather than downloading it from S3 over standard HTTP, cutting cold-start times from 15 minutes to under 30 seconds."

---

#### Question 7: Compare DeepSpeed ZeRO-3 parameter sharding against standard Pipeline Parallelism (PP) in a bandwidth-constrained multi-node cloud cluster. When would you choose one over the other?

##### Expected Answer (Junior/Mid Level)
"ZeRO-3 shards everything (parameters, optimizer states, and gradients) across all GPUs, while Pipeline Parallelism splits the model layers across different GPUs. You use Pipeline Parallelism if your network is slow."

##### Senior-Level Answer
"**ZeRO-3** removes redundancy by splitting the model, gradients, and optimizer states across all available GPUs. During execution, it uses high-frequency `AllGather` operations to fetch weights dynamically for each layer and discards them immediately after. This has a very high communication overhead.
**Pipeline Parallelism (PP)** splits layers sequentially (e.g., GPU 0 runs layers 1-10, GPU 1 runs layers 11-20). It only transfers activation tensors at the boundaries between stages, which requires far less bandwidth.
In a bandwidth-constrained multi-node cluster (e.g., standard Ethernet nodes without InfiniBand), ZeRO-3 is too slow. Pipeline Parallelism is preferred because it minimizes inter-node network traffic."

##### Architect-Level Answer
"This comparison boils down to **Communication Volume vs. Interconnect Latency Sensitivity**.

1. **ZeRO-3 Communication Profile**:
   ZeRO-3 requires two communication steps during the forward pass (an `AllGather` to retrieve layer parameters) and two during the backward pass (an `AllGather` for parameters, and a `ReduceScatter` to aggregate gradients). The total volume of network traffic scales as:
   $$\text{Traffic Volume} = 1.5 \times \text{Model Parameters} \times 2 \text{ (mixed precision bytes)}$$
   This communication happens continuously at every single layer boundary. If inter-node networks are limited to 10 or 100 Gbps TCP/IP, ZeRO-3 execution will spend $>80\%$ of its time blocked on network synchronization.

2. **Pipeline Parallelism (PP) Profile**:
   PP splits the model layers into sequential stages. It only transfers the **activation tensors** (and their corresponding gradients during the backward pass) between physical nodes. The communication volume is bounded by the model's hidden dimension size and batch size, rather than the total number of model parameters:
   $$\text{PP Traffic Volume} = O(\text{Batch Size} \times \text{Hidden Dimension})$$
   This represents a tiny fraction of the traffic generated by ZeRO-3.

3. **Architectural Recommendation**:
   * **Choose Pipeline Parallelism (PP)**: In multi-node setups running over standard Ethernet or virtual cloud private networks where inter-node bandwidth is limited (e.g., $<200$ Gbps). PP allows you to bridge slow physical boundaries.
   * **Choose ZeRO-3**: In dense, single-node systems (like HGX H100s linked by NVLink) or ultra-high-speed InfiniBand fabrics ($800\text{ Gbps}$ per node). ZeRO-3 is far more flexible than PP because it does not introduce the idle 'pipeline bubble' and handles dynamic batching more naturally.
   * **Hybrid Approach (3D Parallelism)**: For trillion-parameter models, we combine them: we scale Tensor Parallelism within the HGX node (NVLink), utilize ZeRO-3 sharding across nodes within the same physical rack (local InfiniBand leaf), and use Pipeline Parallelism to bridge high-latency rack boundaries."
