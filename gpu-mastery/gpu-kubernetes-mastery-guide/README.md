# GPU & Kubernetes Mastery Guide: The Ultimate Engineering Resource

Welcome to the **GPU & Kubernetes Mastery Guide**. This repository contains the most comprehensive, deeply technical learning guide ever created, designed specifically for Staff AI Platform Engineers, MLOps Engineers, AI Infrastructure Engineers, HPC Engineers, and Platform Architects preparing for principal-level interviews and production operations.

This guide contains **no high-level summaries** or generalized notes; every chapter is a deep dive filled with real-world examples, precise system architecture diagrams, mathematical formulas, exact command line outputs, and production troubleshooting playbooks.

---

## 🗺️ Table of Contents & Navigation

This guide has been divided into modular chapters to ensure maximal depth and absolute technical clarity:

### [Section 1: GPU Fundamentals](./section1_gpu_fundamentals.md)
* Learn why GPUs exist, the breakdown of Dennard Scaling, and transistor budgeting.
* CPU vs. GPU architectural comparison (Latency-Optimized vs. Throughput-Optimized design).
* Deep dive into Parallel Computing: SIMD (Single Instruction, Multiple Data) vs. SIMT (Single Instruction, Multiple Threads) models.
* Hardware cores: CUDA Cores (FP32/FP64/INT32), Tensor Cores (mixed-precision), and RT Cores.
* Streaming Multiprocessor (SM) internals.
* Architecture evolution: From Tesla and Pascal to Hopper and Blackwell.

### [Section 2: GPU Hardware Deep Dive](./section2_gpu_hardware_deep_dive.md)
* Comprehensive hardware matrix (V100, T4, A100, L4, L40S, H100, H200, B200, Grace Hopper).
* Interconnect technologies: PCIe Gen 4/5, NVLink 3/4/5, and physical NVSwitch crossbar architectures.
* High-Bandwidth Memory (HBM3e) vs. GDDR6 memory structures.
* Comprehensive workload matching: Sizing GPUs for Training, PEFT, LLM Inference, and HPC.

### [Section 3: CUDA Deep Dive](./section3_cuda_deep_dive.md)
* The CUDA execution stack: Kernel Space vs. User Space (`nvidia.ko` -> `libcuda.so` -> `libcudart.so`).
* Asynchronous execution: CUDA Streams, default streams, and overlapping pipelines.
* Latency reduction: CUDA Graphs creation, warm-up, and compilation.
* Framework integration: How PyTorch, TensorFlow, and vLLM compile down to cuBLAS, cuDNN, and NCCL.
* Real debugging playbooks for `CUDA out of memory`, `device-side assert triggered`, and `illegal memory access`.

### [Section 4: GPU Memory Management](./section4_gpu_memory_management.md)
* Physical memory hierarchy: Registers, Shared Memory (SRAM), L2 Cache, and Global VRAM.
* The mechanics of the PyTorch Caching Allocator: Contiguous memory blocks and fragmentation.
* Silent memory leaks and tracking list histories.
* The KV Cache memory bottleneck in LLMs.
* The vLLM revolution: **PagedAttention** virtual memory architecture.
* Advanced memory optimizations: FlashAttention, Activation Checkpointing, DeepSpeed ZeRO-1/2/3, and quantization.

### [Section 5: AI Model Sizing](./section5_ai_model_sizing.md)
* Precision format bit structures: FP32, FP16, BF16, FP8, INT8, and INT4.
* Model training VRAM equation (Adam optimizer, parameters, gradients, and optimizer states).
* Model inference VRAM equation.
* Step-by-step sizing scenarios with exact mathematical formulations: Llama 3 8B, Mistral 13B, CodeLlama 34B, Llama 3 70B, and Llama 3 405B.

### [Section 6: GPU Monitoring](./section6_gpu_monitoring.md)
* Direct kernel query overheads: `nvidia-smi` vs. lightweight C++ DCGM.
* Key telemetry metrics explained: GPU Util, Memory Bus, Power consumption, Thermal violation, and ECC/PCIe/NVLink errors.
* Production-grade Prometheus scraping configurations and alerting rules.
* Complete Grafana JSON panel declarations.

### [Section 7: GPU Troubleshooting](./section7_gpu_troubleshooting.md)
* Real production incident runbooks for hardware, driver, and network failures.
* Diagnosing uncorrectable Volatile Double-Bit ECC Errors and dynamic Row Remapping.
* Fixing host-to-container Driver and CUDA runtime mismatches.
* Eliminating network-bound training bottlenecks (GPUDirect RDMA over InfiniBand).
* Diagnosing thermal throttling performance drops.

### [Section 8: Kubernetes GPU Fundamentals](./section8_kubernetes_gpu_fundamentals.md)
* The Kubernetes Device Plugin framework execution pipeline.
* Extended Resources (`nvidia.com/gpu`) and the requests/limits equivalence rule.
* Isolating expensive hardware: Node Labels, Node Affinity, Taints, and Tolerations.
* Complete production-grade Pod manifest with advanced scheduling.

### [Section 9: NVIDIA Kubernetes Ecosystem](./section9_nvidia_kubernetes_ecosystem.md)
* Breakdown of sub-components: NFD, GFD, Container Toolkit, Device Plugin, and MIG Manager.
* Complete production-grade Helm values file (`values.yaml`) for deploying the NVIDIA GPU Operator.

### [Section 10: GPU Operator](./section10_gpu_operator.md)
* Operator state machine and sequence of initialization.
* Debugging common Operator failures (Kernel header mismatches, Containerd injection bugs).
* Production upgrade strategies: Live driver unload/reload without reboots.

### [Section 11: GPU Scheduling](./section11_gpu_scheduling.md)
* GPU sharing comparison: Time-Slicing vs. Multi-Process Service (MPS) vs. Multi-Instance GPU (MIG).
* Virtual replica ConfigMap setups.
* Batch queuing and Gang Scheduling using Kueue and Volcano to prevent resource deadlocks.

### [Section 12: MIG (Multi Instance GPU)](./section12_mig_multi_instance_gpu.md)
* Hardware partitioning in H100 vs. A100.
* Creating, deleting, and modifying physical partitions via CLI.
* Dynamic MIG allocation ConfigMaps under the GPU Operator.
* Manifest examples requesting `nvidia.com/mig-1g.10gb` slices.

### [Section 13: AI Inference Infrastructure](./section13_ai_inference_infrastructure.md)
* In-depth framework comparison: vLLM vs. TensorRT-LLM vs. TGI vs. Ray Serve vs. KServe.
* Architecture blueprints for low-latency concurrent model serving.

### [Section 14: Large Scale Model Serving](./section14_large_scale_model_serving.md)
* 3D parallelisms: Tensor Parallelism, Pipeline Parallelism, Expert Parallelism (MoE).
* Column and Row matrix splits under Megatron-LM.
* Complete pod manifests deploying Llama-3-70B and Mixtral 8x22B across multiple nodes.

### [Section 15: GPU Autoscaling](./section15_gpu_autoscaling.md)
* Designing the scaling pipeline: Event-driven KEDA, HPAs, and pending pods.
* Production KEDA ScaledObject tracking vLLM queue length.
* Dynamic node provisioning with AWS Karpenter NodePool specifications.

### [Section 16: GPU Security](./section16_gpu_security.md)
* Multi-tenant security vectors and memory leakage threats.
* Tight ingress/egress isolation using NetworkPolicies.
* Confidential Computing: Secure guest VMs, PCIe bus encryption (AES-GCM-256), and protected VRAM (APM).

### [Section 17: Real AI Platform Architectures](./section17_real_ai_platform_architectures.md)
* Architectural blueprints (ASCII diagrams) and design rationales for:
  * Small AI Startups (Karpenter scale-to-zero, PCIe cards).
  * Enterprise Platforms (MIG mode sharing, strict RBAC, Istio service mesh).
  * Frontier Training Clusters (Thousands of HGX H100s, non-blocking InfiniBand fabrics, Lustre storage).

### [Section 18: Interview Preparation](./section18_interview_preparation.md)
* Scenario-based questions covering Core Hardware, Scheduling, Runtimes, and Systems Architecture.
* Step-by-step answers structured across Junior, Senior, and Staff Architect dimensions.

### [Section 19: Production War Stories](./section19_production_war_stories.md)
* Real production incidents including:
  * The Infinite PyTorch Caching Allocator Loop.
  * The Degraded Speed NVLink Link Failure.
  * The Jupyter Notebook Ghost CUDA Context VRAM leak.

### [Section 20: Learning Roadmap](./section20_learning_roadmap.md)
* A comprehensive 30, 60, 90, and 180-day career roadmap.
* Hands-on laboratory assignments, projects, and diagnostic profiling steps.

---

## 🚀 How to Use This Guide

This guide is designed to be read sequentially or as a real-time production reference handbook.
To run or explore any of the files locally:
1. Clone this repository to your system.
2. Read the markdown files in any markdown viewer or text editor.
3. Utilize the provided YAML manifests directly in your staging or development Kubernetes clusters to build, test, and run next-generation AI platforms.
