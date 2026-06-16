# GPU & Kubernetes Mastery Guide
## Section 1: GPU Fundamentals

---

### 1.1 What is a GPU and Why Does It Exist?

A **Graphics Processing Unit (GPU)** is a specialized, highly parallel hardware accelerator designed to perform mathematical operations on large datasets simultaneously. 

#### Why GPUs Exist (The Physics and Economics of Computing)
In the early days of computing, Central Processing Units (CPUs) followed **Moore’s Law** and **Dennard Scaling**. Every two years, transistors shrank, clock speeds doubled, and performance scaled without increasing power density. However, around 2005, Dennard Scaling broke down due to leakage currents and thermal limits (the "Power Wall"). Clock speeds plateaued around 3.5 GHz - 5.0 GHz.

To continue scaling compute performance, chipmakers shifted from making single cores faster to putting more cores on a single die (multicore CPUs). But CPUs are fundamentally designed for **latency-optimized sequential execution**. They use massive caches, sophisticated branch predictors, and complex out-of-order execution logic to run a single thread of instructions as fast as possible.

Meanwhile, workloads like computer graphics, physical simulations, and deep learning are **throughput-optimized embarrassingly parallel problems**. They require performing the exact same mathematical operation (e.g., matrix multiplication, vector addition) over millions of independent data points. 

This mismatch gave birth to the GPU: a processor that sacrifices complex instruction pipelines, branch prediction, and massive low-latency caches in favor of packing thousands of smaller, simpler arithmetic logic units (ALUs) onto a single silicon die.

---

### 1.2 CPU vs. GPU Architecture and Execution Models

#### The Structural Comparison
To understand the architectural difference, consider the transistor allocation budget of each chip:

```
=========================================
          CPU ARCHITECTURE
=========================================
+---------------------------------------+
|  [Core 0]      [Core 1]     [Core 2]  |
|  +--------+    +--------+   +-------+ |
|  | ALU/FPU|    | ALU/FPU|   |ALU/FPU| |
|  +--------+    +--------+   +-------+ |
|  | Control|    | Control|   |Control| |
|  +--------+    +--------+   +-------+ |
+---------------------------------------+
|               L1/L2 Cache             |
+---------------------------------------+
|       MASSIVE SHARED L3 CACHE         |
+---------------------------------------+
|  Branch Predictor | Out-of-Order Logic|
+---------------------------------------+

=========================================
          GPU ARCHITECTURE
=========================================
+---------------------------------------+
|  [SM 0] [SM 1] [SM 2] [SM 3] [SM 4]   |
|  +---+ +---+ +---+ +---+ +---+ +---+  |
|  |ALU| |ALU| |ALU| |ALU| |ALU| |ALU|  |
|  |ALU| |ALU| |ALU| |ALU| |ALU| |ALU|  |
|  |ALU| |ALU| |ALU| |ALU| |ALU| |ALU|  |
|  |ALU| |ALU| |ALU| |ALU| |ALU| |ALU|  |
|  +---+ +---+ +---+ +---+ +---+ +---+  |
|  |Ctrl | Shared Mem | L1 Cache     |  |
|  +---+---+---+---+---+---+---+---+---+  |
+---------------------------------------+
|             SHARED L2 CACHE           |
+---------------------------------------+
|          HIGH-SPEED VRAM (HBM)        |
+---------------------------------------+
```

| Feature | CPU (Central Processing Unit) | GPU (Graphics Processing Unit) |
| :--- | :--- | :--- |
| **Design Philosophy** | Latency-Optimized (Minimize time to complete a single task) | Throughput-Optimized (Maximize tasks completed per unit time) |
| **Core Count** | Few (4 to 128 cores) | Many Thousands (e.g., 18,432 CUDA cores in NVIDIA H100) |
| **Control Logic** | Highly complex (Branch prediction, speculative execution, out-of-order execution) | Simple (Decodes instructions for warps/groups of threads simultaneously) |
| **Cache Size** | Very large (Megabytes per core; absorbs memory latency) | Small (Kilobytes per core; relies on thread parallelism to hide latency) |
| **Memory Bandwidth** | Moderate (DDR5: ~50-100 GB/s) | Ultra-high (HBM3: ~3.35 TB/s on H100) |
| **Thread Context Switch**| Heavyweight (Registers/state saved to RAM; hundreds of clock cycles) | Zero-overhead hardware context switching |

#### Execution Models: Sequential vs. Parallel
* **CPU Latency-Hiding**: Uses massive caches so that data is almost always immediately available to the ALU. If a branch occurs, speculative execution predicts the path.
* **GPU Latency-Hiding**: Tolerates long memory access latencies (hundreds of clock cycles to high-speed VRAM) by context-switching to another thread warp instantaneously. If Warp A is waiting for data from memory, the scheduler immediately switches to Warp B to execute its math, ensuring the ALUs are never idle.

---

### 1.3 Parallel Computing and SIMD / SIMT

#### SIMD (Single Instruction, Multiple Data)
SIMD is a hardware execution model where a single vector instruction is applied to multiple data elements simultaneously. Examples include CPU instruction set extensions like Intel's AVX-512 or ARM's NEON.
* *Analogy*: A high-school math teacher writing a single formula on the board and telling all 30 students to solve it using their individual worksheets.

#### SIMT (Single Instruction, Multiple Threads)
NVIDIA popularized the **SIMT** execution model in CUDA. SIMT is an evolution of SIMD. Instead of dealing with vector registers directly, programmers write sequential thread code. The hardware automatically groups these threads into units called **Warps** (always 32 threads in NVIDIA GPUs).
* The 32 threads in a warp execute the same instruction at the same time.
* Unlike SIMD, each thread has its own independent instruction address counter and register state. This allows for **Thread Divergence** (conditional branching like `if/else`).
* If threads in a warp diverge, the hardware serializes the branches, executing the `if` path first (disabling threads that evaluate to `false`) and then the `else` path, which degrades performance (called branch divergence).

```
Warp Execution with Branch Divergence:
Warp Thread Index: [01][02][03] ... [32]
Instruction 1 (IF):  [X] [X] [ ]     [ ]  <-- Threads 3..32 are masked (idle)
Instruction 2 (ELSE):[ ] [ ] [X]     [X]  <-- Threads 1..2 are masked (idle)
```

---

### 1.4 Deep Dive into GPU Core Types

NVIDIA GPUs contain three distinct types of computational units designed for specialized tasks:

```
+-------------------------------------------------------------+
|               Streaming Multiprocessor (SM)                 |
|                                                             |
|  +---------------------+  +------------------------------+  |
|  |     CUDA Cores      |  |         Tensor Cores         |  |
|  |  [FP32] [FP64] [INT] |  |  Mixed-Precision Matrix Math |  |
|  |  Scalar math & logic |  |  (A x B + C) in 1 cycle      |  |
|  +---------------------+  +------------------------------+  |
|                                                             |
|  +---------------------+  +------------------------------+  |
|  |      RT Cores       |  |     Shared Mem / L1 Cache    |  |
|  |  Ray tracing / BVH   |  |  Ultra-fast block memory     |  |
|  +---------------------+  +------------------------------+  |
+-------------------------------------------------------------+
```

#### 1. CUDA Cores
Standard scalar/vector execution units. They perform one mathematical operation (like floating-point addition or multiplication) per clock cycle per core.
* **FP32 Cores**: Execute single-precision (32-bit) floating-point calculations. Critical for general simulation and traditional HPC.
* **FP64 Cores**: Execute double-precision (64-bit) calculations. Essential for scientific computing (physics, weather, molecular dynamics).
* **INT32 Cores**: Execute 32-bit integer arithmetic. Used for array indexing and addressing calculations.

#### 2. Tensor Cores
Specialized, hardwired matrix-multiplication units introduced in the Volta (V100) architecture. Instead of operating on individual scalar numbers, a single Tensor Core instruction operates on whole matrices in a single clock cycle.
* **Operation**: Computes $D = A \times B + C$, where $A, B, C, D$ are matrices.
* **Mixed Precision**: They typically take input matrices in lower-precision (FP16, BF16, FP8, or INT8) to accelerate the math and save memory bandwidth, but accumulate the result in higher-precision (FP32) to maintain training stability.
* **Performance Impact**: Tensor Cores are the primary reason AI workloads speed up by 10x to 100x compared to standard CPU or GPU scalar cores.

#### 3. RT (Ray Tracing) Cores
Specialized hardware accelerators designed to perform ray-triangle intersection tests and Bounding Volume Hierarchy (BVH) traversals.
* **AI Use Case**: Primarily used in computer graphics and rendering, but increasingly explored for spatial AI, physics-informed neural networks (PINNs), and rapid spatial searches.

---

### 1.5 Streaming Multiprocessors (SMs)

The **Streaming Multiprocessor (SM)** is the fundamental building block of an NVIDIA GPU. A GPU does not scale by making a single SM bigger; instead, it scales by stamping out dozens or hundreds of identical SMs onto the silicon.

An H100 GPU, for example, contains up to 144 SMs. Inside a single SM, you will find:
* **Warp Schedulers and Instruction Dispatch Units**: Manage and schedule the execution of threads in groups of 32 (Warps).
* **Register File**: A massive, ultra-fast storage area (e.g., 256 KB per SM) that holds the variables and states of thousands of active threads.
* **L1 Instruction / Data Cache**: High-speed local cache.
* **Shared Memory (SRAM)**: High-speed, programmer-managed scratchpad memory shared among threads in the same thread block. Essential for optimizing global memory bandwidth.
* **CUDA Cores and Tensor Cores**: The execution units.

---

### 1.6 GPU Architecture Evolution: From Tesla to Blackwell

NVIDIA's architectures are named after famous scientists. Let's trace the evolutionary trajectory that turned a graphics chip into an AI powerhouse:

```
[Tesla] -> [Fermi] -> [Kepler] -> [Maxwell] -> [Pascal] -> [Volta] -> [Ampere] -> [Hopper] -> [Blackwell]
  2006       2010       2012        2014       2016       2017       2020       2022        2024
  CUDA     L1 Cache     Dynamic     Power      NVLink    Tensor      MIG,     Transformer  Liquid Cooled,
  Born     & ECC        Parallel    Effic.     & HBM      Cores      Sparsity   Engine (FP8) Second-Gen NVLink
```

1. **Tesla (2006)**: Introduced unified shader architecture and the CUDA programming model. No caches, no ECC memory support.
2. **Fermi (2010)**: Added true L1/L2 cache hierarchy, ECC memory protection, and native 64-bit floating-point support.
3. **Kepler (2012)**: Focused on energy efficiency and introduced Dynamic Parallelism (allowing a GPU to launch kernels on itself without host CPU intervention).
4. **Maxwell (2014)**: Optimized tiles-based rasterization and dramatic power-efficiency improvements.
5. **Pascal (2016 - P100)**: Game-changer for deep learning. Introduced **HBM2 (High Bandwidth Memory)**, **NVLink** (first-generation high-speed interconnect), and unified memory architectures.
6. **Volta (2017 - V100)**: First architecture to feature **Tensor Cores** (specifically FP16 matrix multiplication), enabling the deep learning revolution. Added Independent Thread Scheduling.
7. **Ampere (2020 - A100)**: Introduced **Multi-Instance GPU (MIG)** for hardware partitioning, **TensorFloat-32 (TF32)** format, and **Sparsity** support (2x throughput for 2:4 sparse matrices).
8. **Hopper (2022 - H100/H200)**: Introduced the **Transformer Engine** (dynamically switches between FP8 and FP16 to maximize performance while preserving accuracy), DPX instructions for dynamic programming, and **Distributed Shared Memory**.
9. **Blackwell (2024 - B100/B200)**: Dual-die architecture linked by a 10 TB/s high-bandwidth interconnect. Features 2nd Generation Transformer Engine supporting FP4/FP6, native support for massive-scale MoE (Mixture of Experts) models, and NVLink 5 (up to 1.8 TB/s bidirectional bandwidth per GPU).

---

### 1.7 Why AI Workloads Require GPUs

To understand why deep learning is completely dependent on GPUs, look at the core mathematical operation of neural networks: **Matrix Multiplication**.

Consider a single layer of a multi-layer perceptron:
$$y = \sigma(W \cdot x + b)$$

Where:
* $x$ is an input vector of size $1 \times N$.
* $W$ is a weight matrix of size $N \times M$.
* $b$ is a bias vector.
* $\sigma$ is an activation function (like ReLU or GELU).

For a modern Large Language Model (like Llama-3-70B), the dimension $N$ can be 8,192. Performing a single forward pass of a token involves multiplying a vector of size 8,192 with multiple weight matrices of size $8,192 \times 8,192$. This equates to **billions of floating-point operations (FLOPs) per token per layer**.

#### Sequential vs. Massively Parallel Multiplications
* **CPU Approach**: A CPU core executes operations sequentially. It may have vector instructions (like AVX-512) that can process 16 floats at a time. But even with 64 cores, it can only process a fraction of the matrix multiplication at once. It will loop millions of times, leading to high latency.
* **GPU Approach**: A GPU splits the matrix multiplication into thousands of tiny tiles. It assigns each tile to a separate **Thread Block** running on a separate **Streaming Multiprocessor (SM)**. Inside each SM, hundreds of threads compute individual cell multiplications simultaneously. Tensor Cores execute entire sub-matrix multiplications in a single clock cycle. The entire layer is processed in parallel, cutting execution time from seconds to microseconds.
