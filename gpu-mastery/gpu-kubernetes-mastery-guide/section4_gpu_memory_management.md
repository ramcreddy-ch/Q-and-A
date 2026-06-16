# GPU & Kubernetes Mastery Guide
## Section 4: GPU Memory Management

---

### 4.1 The GPU Memory Hierarchy

To write high-performance deep learning code or debug container memory issues, you must understand the GPU's internal physical and logical memory hierarchy.

```
+-------------------------------------------------------------------+
|                           REGISTERS                               |
|  - Speed: ~100 TB/s | Capacity: ~256 KB per SM                    |
|  - Scope: Private to individual thread                            |
+-------------------------------------------------------------------+
                                 ↓
+-------------------------------------------------------------------+
|                        SHARED MEMORY / L1 CACHE                   |
|  - Speed: ~10-20 TB/s | Capacity: ~128 KB per SM                  |
|  - Scope: Shared within a Thread Block                            |
+-------------------------------------------------------------------+
                                 ↓
+-------------------------------------------------------------------+
|                            L2 CACHE                               |
|  - Speed: ~5 TB/s | Capacity: ~50-100 MB per GPU                  |
|  - Scope: Shared across all SMs                                   |
+-------------------------------------------------------------------+
                                 ↓
+-------------------------------------------------------------------+
|                       GLOBAL MEMORY (VRAM / HBM)                  |
|  - Speed: ~1-5 TB/s | Capacity: 16 - 192 GB                       |
|  - Scope: Accessible by all threads and Host (via PCIe)           |
+-------------------------------------------------------------------+
```

1. **Registers**: The fastest memory on the GPU. Variables created inside CUDA kernels are automatically stored in registers. If a kernel uses too many registers, the compiler spills them to global memory (**Register Spilling**), which severely degrades performance.
2. **Shared Memory (SRAM)**: On-chip memory located on the SM. It is highly configurable. Threads within the same thread block can use it to share data rapidly, bypassing global memory.
3. **L2 Cache**: A larger, on-chip cache shared across all SMs. It reduces memory access latency to the off-chip VRAM.
4. **Global Memory (VRAM)**: The main memory of the GPU (HBM or GDDR). It is slow compared to registers and shared memory, but has the largest capacity.

---

### 4.2 GPU Out of Memory (OOM), Fragmentation, and Leaks

#### What Really Happens During a GPU OOM?
When PyTorch or another framework runs out of memory, it's rarely because the physical GPU runs out of bytes instantly. Instead, it is typically a failure of the **PyTorch Caching Allocator**.
* **Why PyTorch uses a Caching Allocator**: Allocating memory via the CUDA driver (`cudaMalloc`) is extremely slow because it requires a round-trip to the kernel space and halts the GPU pipeline. To avoid this, PyTorch allocates a large block of memory from the GPU driver once and manages it internally. When your code requests memory, PyTorch assigns a slice from its pool without calling `cudaMalloc`.

#### Memory Fragmentation
If your code frequently allocates and deletes tensors of varying sizes, the PyTorch allocator's memory block becomes highly fragmented:

```
PyTorch Block Memory Map:
[ Allocated: 2GB ] [ Free: 500MB ] [ Allocated: 4GB ] [ Free: 1GB ] [ Allocated: 10GB ]
```

* Total Free Memory: 1.5 GB.
* If you try to allocate a contiguous tensor of **1.2 GB**, PyTorch will fail with an OOM error! This is because there is no single contiguous 1.2 GB free slot available, even though the total free memory is 1.5 GB.

#### Memory Leaks
Memory leaks on GPUs occur when tensors are unintentionally kept alive in Python, preventing the PyTorch allocator from freeing them. Common causes include:
* **Accumulating History**: Appending a PyTorch tensor (e.g., loss) to a list without calling `.item()` or `.detach()`. This retains the entire autograd computation graph in memory.
```python
# BAD (causes memory leak)
losses.append(loss)

# GOOD
losses.append(loss.item())
```

---

### 4.3 The KV Cache and PagedAttention

In autoregressive Large Language Models (like Llama, Mistral, DeepSeek, and Qwen), text is generated token-by-token. To generate token $t$, the model must attend to all previous tokens $1 \dots t-1$. 

Instead of recomputing the Key ($K$) and Value ($V$) projections for all past tokens at every generation step, frameworks store these matrices in memory: this is the **KV Cache**.

#### The KV Cache Memory Crisis
The size of the KV cache scales linearly with the sequence length, batch size, and number of layers. For a single Llama-3-70B model with a batch size of 32 and a context length of 8,192:
$$\text{KV Cache Size} = 2 \times \text{layers} \times \text{heads} \times \text{dimension} \times \text{seq\_len} \times \text{batch\_size} \times \text{bytes\_per\_param}$$

For Llama-3-70B:
* Layers = 80
* Key-Value Heads (GQA) = 8
* Head Dimension = 128
* Bytes per parameter = 2 (FP16)

$$\text{KV Cache Size} = 2 \times 80 \times 8 \times 128 \times 8192 \times 32 \times 2 \approx \mathbf{107.3 \text{ GB}}$$

This requires more than a single 80GB GPU just to hold the KV cache!

#### PagedAttention (The vLLM Revolution)
Before PagedAttention, frameworks allocated the KV Cache as large, contiguous blocks of virtual memory for each request. 
* **The Problem**: Because sequence lengths are dynamic, the framework had to pre-allocate memory for the *maximum possible context length* (e.g., 2048 tokens). This meant up to **60-80% of VRAM was wasted** holding empty space. This is called **Internal Fragmentation**.

* **The Solution**: PagedAttention (inspired by virtual memory paging in operating systems) divides the KV Cache into small, fixed-size blocks (pages) that do not need to be contiguous in physical memory.

```
Logical KV Cache (Request 1): [ Block 0 ] [ Block 1 ] [ Block 2 ]
                                    \           /           /
Physical VRAM Pages:         [ Page 8 ] [ Page 12 ] [ Page 1 ]
```

A lookup table maps logical tokens to physical pages. This eliminates internal fragmentation, allowing vLLM to utilize up to 96% of free VRAM for the KV cache, boosting inference throughput by 2x to 4x.

---

### 4.4 Memory Optimization Techniques

To train or serve large models on commodity GPUs, architects employ several memory optimization strategies:

#### 1. FlashAttention
Standard self-attention computes $S = Q \times K^T$, applies Softmax, and computes $O = S \times V$. The intermediate attention matrix $S$ is of size $N \times N$ (where $N$ is sequence length). For $N=100,000$, $S$ occupies **40GB** of memory!
* **FlashAttention** is a custom CUDA kernel that computes attention incrementally. By utilizing GPU shared memory (SRAM) and online Softmax scaling, it computes attention without writing the massive $N \times N$ intermediate matrix back to slow VRAM, reducing memory footprint from $O(N^2)$ to $O(N)$ and accelerating execution by 2-4x.

#### 2. Activation Checkpointing (Gradient Checkpointing)
During training, PyTorch stores all intermediate layer activations in VRAM during the forward pass so they can be used to calculate gradients during the backward pass.
* **Activation Checkpointing** drops most intermediate activations from memory. During the backward pass, it re-computes these activations on-the-fly when needed. This reduces VRAM consumption by up to 60% at the cost of a ~30% computational overhead.

#### 3. DeepSpeed ZeRO (Zero Redundancy Optimizer)
Standard data parallelism replicates the entire model, optimizer states, and gradients on every GPU. This creates massive redundancy. ZeRO removes this redundancy:
* **ZeRO-1**: Shards optimizer states (e.g., Adam states) across GPUs.
* **ZeRO-2**: Shards optimizer states + gradients across GPUs.
* **ZeRO-3**: Shards optimizer states + gradients + model parameters across GPUs. During execution, parameters are gathered via high-speed NVLink when needed and discarded immediately after.

```
Standard DP:   [Model + Grad + Opt] [Model + Grad + Opt] [Model + Grad + Opt]
ZeRO-3 Sharding: [Model_1|Grad_1|Opt_1] [Model_2|Grad_2|Opt_2] [Model_3|Grad_3|Opt_3]
```

#### 4. Quantization
Converts weights from high-precision formats (like FP32 or BF16) to lower-precision formats (like FP8, INT8, or INT4).
* A 70B parameter model in FP16 requires **140 GB** of VRAM just to load.
* The same model quantized to INT4 requires only **~35 GB** of VRAM, allowing it to easily fit on a single 48GB GPU (like the L40S) or a dual L4 configuration.
