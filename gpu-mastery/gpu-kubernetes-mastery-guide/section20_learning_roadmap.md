# GPU & Kubernetes Mastery Guide
## Section 20: Learning Roadmap & Career Progression

---

This section provides a structured learning roadmap to take you from absolute beginner to production-scale Staff AI Infrastructure Engineer.

---

### Phase 1: Days 1 to 30 (Core GPU & CUDA Fundamentals)

#### Objective
Understand the underlying physics, hardware execution, and basic software compiler mechanics of GPUs.

#### Weekly Goals
* **Week 1**: CPU vs. GPU hardware architecture. Master the concepts of Streaming Multiprocessors (SMs), ALUs, Registers, Cache hierarchies, and the differences between GDDR and HBM memory.
* **Week 2**: Learn the **SIMT (Single Instruction, Multiple Threads)** execution model. Understand Warps, Thread Blocks, Thread Divergence, and physical scheduling.
* **Week 3**: Dive into the CUDA Software Stack. Learn the differences between the NVIDIA Kernel Driver, Driver API, Runtime API, and CUDA Toolkit.
* **Week 4**: Write a basic CUDA kernel. Compile a vector-addition or matrix-multiplication program in C++ using `nvcc`.

#### Hands-On Project: The Custom CUDA Matrix Multiplication
1. Write a basic sequential matrix multiplication in standard C++.
2. Write a parallel version using CUDA, executing it on a free cloud GPU (e.g., Google Colab T4).
3. Optimize the kernel using **Shared Memory (SRAM)** to load data tiles, reducing global memory accesses.
4. Profile the execution speed using `nsight-compute` to measure your memory bandwidth and arithmetic intensity.

---

### Phase 2: Days 31 to 60 (Kubernetes GPU Infrastructure)

#### Objective
Expose, schedule, and isolate GPU hardware natively in a containerized cluster environment.

#### Weekly Goals
* **Week 5**: Understand the Kubernetes **Device Plugin Framework**. Learn how extended resources like `nvidia.com/gpu` are registered with the Kubelet.
* **Week 6**: Deploy and configure the **NVIDIA GPU Operator** using Helm. Learn what each sub-component (NFD, GFD, Container Toolkit, DCGM Exporter) does.
* **Week 7**: Master GPU partitioning. Configure **MIG (Multi-Instance GPU)** dynamic partitioning and **Time-Slicing** setups.
* **Week 8**: Implement GPU monitoring. Deploy DCGM Exporter, configure Prometheus scraping rules, and build a custom Grafana dashboard.

#### Hands-On Lab: The Automated MIG partitioning cluster
1. Set up a local Kubernetes cluster (using Kind, Minikube, or a cheap single-node GPU cloud instance).
2. Install the GPU Operator with MIG mode enabled.
3. Configure a Node label that dynamically splits a GPU into multiple MIG slices.
4. Deploy multiple workloads requesting specific MIG slices, verifying hardware isolation.

---

### Phase 3: Days 61 to 90 (Production Scale MLOps & serving)

#### Objective
Design and operate highly available, autoscaling inference pipelines for massive models.

#### Weekly Goals
* **Week 9**: Deep dive into LLM inference bottlenecks. Master the concepts of the Prefill vs. Decode phases, the KV Cache, and **PagedAttention**.
* **Week 10**: Deploy and scale **vLLM** and **TensorRT-LLM** APIs. Compare execution latencies and throughputs.
* **Week 11**: Configure advanced autoscaling. Set up **KEDA** to scale inference pods based on active queue size metrics pulled from Prometheus.
* **Week 12**: Implement model sharding. Configure **Tensor Parallelism** and **Pipeline Parallelism** configurations across multi-GPU setups.

#### Production Simulation: The Autoscaling LLM Gateway
1. Deploy vLLM serving Llama-3-8B.
2. Configure Prometheus to scrape vLLM queue metrics.
3. Install KEDA and define a ScaledObject that tracks waiting requests.
4. Use a load-testing tool (like Locust) to simulate a massive user spike, monitoring how KEDA scales the pods and how Karpenter boots new GPU nodes.

---

### Phase 4: Days 91 to 180 (Enterprise AI Platform Architecture)

#### Objective
Architect secure, multi-tenant AI platforms supporting both massive-scale training and low-latency serving.

#### Weekly Goals
* **Week 13-16**: Master multi-node training clusters. Learn **GPUDirect RDMA**, RoCE v2, InfiniBand networking, and NCCL communication tuning.
* **Week 17-20**: Deep dive into cluster security. Configure NetworkPolicies, RBAC, encrypted VRAM (Hopper Confidential Computing), and private registries.
* **Week 21-24**: Career mastery & Interview Preparation. Solve system design scenarios, study production incidents, and practice mock technical interview questions.

#### Recommended Resource Repositories
* **NVIDIA/gpu-operator**: Study the official Helm charts and custom resource definition (CRD) files.
* **vllm-project/vllm**: Analyze their custom C++ and CUDA memory management kernels.
* **kubernetes-sigs/kueue**: Explore their batch scheduling and job queuing engine.
