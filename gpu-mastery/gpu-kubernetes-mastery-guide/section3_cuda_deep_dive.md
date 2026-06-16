# GPU & Kubernetes Mastery Guide
## Section 3: CUDA Deep Dive

---

### 3.1 Understanding the CUDA Stack Architecture

NVIDIA's **CUDA (Compute Unified Device Architecture)** is the proprietary parallel computing platform and programming model that allows developers to write standard C/C++ (and Python via wrappers) to execute general-purpose programs on GPUs.

To build reliable containerized GPU applications, you must understand how the different layers of the CUDA stack interact:

```
+-------------------------------------------------------------+
|               User Application / ML Framework               |
|                    (PyTorch, vLLM, JAX)                     |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|             CUDA Libraries (cuDNN, cuBLAS, NCCL)             |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|             CUDA Runtime API (libcudart.so)                 |
|             (High-level, managed memory/threads)            |
+-------------------------------------------------------------+
                               ↓   [Boundary: Container / Host]
============================= USER SPACE ======================
                             KERNEL SPACE
===============================================================
                               ↓
+-------------------------------------------------------------+
|             CUDA Driver API (libcuda.so)                    |
|             (Low-level, direct hardware access)             |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|             NVIDIA Kernel Driver (nvidia.ko)                |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|                    Physical GPU Hardware                     |
+-------------------------------------------------------------+
```

#### 1. The NVIDIA Kernel Driver (`nvidia.ko`)
* **Location**: Loaded into the host operating system kernel.
* **Role**: Talks directly to the physical GPU hardware over the PCIe bus. It handles memory mapping, interrupts, physical GPU configuration, and DMA (Direct Memory Access) transfers.

#### 2. The CUDA Driver API (`libcuda.so`)
* **Location**: User-space library.
* **Role**: Exposes a low-level API for controlling the GPU (e.g., loading modules, context management, raw memory allocation). It is backward compatible: a newer driver can run applications compiled with older toolkits.

#### 3. The CUDA Runtime API (`libcudart.so`)
* **Location**: High-level C++ API compiled into your application or installed via python wheels/packages.
* **Role**: Automates context management, device initialization, stack tracking, and high-level memory allocation (`cudaMalloc`, `cudaFree`). Most applications talk to the Runtime, not the Driver API.

#### 4. The CUDA Toolkit
* A collection of development utilities including:
  * **`nvcc`**: The NVIDIA CUDA Compiler that splits host C++ code from GPU device code.
  * **Math Libraries**: `cuBLAS` (dense linear algebra), `cuDNN` (deep neural networks), `cuFFT` (fast Fourier transforms).
  * **Communication Libraries**: `NCCL` (NVIDIA Collective Communications Library) for multi-GPU training/inference communication.

---

### 3.2 CUDA Streams, Graphs, and Scheduling

#### CUDA Streams: Asynchronous Execution
By default, CUDA operations are executed sequentially on the GPU. However, a **CUDA Stream** is a queue of commands (kernels, memory copies) that execute in order. Different streams can execute their work **concurrently** and asynchronously on the same GPU, allowing for overlapping computation and communication.

* **Stream 0 (Default Stream)**: Synchronous. Any operation in the default stream blocks all other streams until it finishes.
* **Non-Default Streams**: Asynchronous. They can run parallel operations.

```
STREAM 1 (MemCopy H2D)  =======> [H2D Copy] ------------------------------->
STREAM 2 (Kernel Exec)  --------------------> [Kernel 1] ------------------->
STREAM 3 (MemCopy D2H)  -----------------------------------> [D2H Copy] ---->
                                        (All running concurrently!)
```

#### CUDA Graphs
Historically, launching thousands of small kernels in a loop (very common in LLM decoding) introduced a significant CPU-side bottleneck. Every `cudaLaunchKernel` call incurs driver and hardware scheduling overhead (~5 to 10 microseconds per launch).

**CUDA Graphs** solve this by grouping multiple CUDA operations (kernels, memory copies, dependencies) into a single execution graph.
1. The graph is recorded once during warm-up.
2. The entire graph is instantiated and submitted to the GPU in a single driver call.
3. The GPU hardware executes the entire graph internally, reducing host-to-device launch latency to near zero.

---

### 3.3 How AI Frameworks (PyTorch, TensorFlow, vLLM) Interact with CUDA

Deep learning frameworks do not write raw CUDA kernels from scratch for every model. Instead, they act as massive compilers and orchestrators.

#### The PyTorch Execution Flow
```
1. PyTorch Code: y = x @ W (Matrix multiplication)
2. PyTorch Dispatcher identifies tensors are on device 'cuda:0'
3. PyTorch calls the specialized "aten" (A Tensor Library) operator: `aten::mm`
4. The operator calls the high-performance 'cuBLAS' library function: `cublasSgemm`
5. cuBLAS passes the request to the CUDA Runtime (`libcudart.so`)
6. The Runtime submits the kernel execution command to the CUDA Driver (`libcuda.so`)
7. The Driver pushes the instruction to the hardware Ring Buffer / command queue on the GPU
8. The GPU hardware schedules and executes the matrix multiplication across its SMs
```

#### The vLLM Custom Kernel Advantage
Engineered for ultra-fast LLM inference, **vLLM** bypasses several PyTorch layers to achieve maximum throughput. It uses custom C++ and CUDA extensions for:
1. **PagedAttention**: Replaces standard PyTorch attention matrices (which require contiguous virtual memory allocations) with a custom CUDA kernel that handles non-contiguous memory pages.
2. **Custom Quantization Kernels**: Direct hardware execution of AWQ/GPTQ INT4/INT8 operations on Tensor Cores using custom written-in-CUDA lookup tables and matrix-multiply logic.

---

### 3.4 Real Debugging Examples & Common CUDA Failures

Here are three real-world CUDA debugging scenarios with precise steps, command inputs, outputs, and resolutions.

#### Incident 1: `CUDA out of memory` (OOM)
* **Symptom**: PyTorch script crashes during training.
* **Terminal Error Output**:
```bash
Traceback (most recent call last):
  File "train.py", line 42, in <module>
    loss.backward()
  File "/opt/conda/lib/python3.10/site-packages/torch/_tensor.py", line 487, in backward
    torch.autograd.backward(
RuntimeError: CUDA out of memory. Tried to allocate 4.12 GiB (GPU 0; 79.35 GiB total capacity; 73.12 GiB already allocated; 2.11 GiB free; 74.50 GiB reserved in total by PyTorch) If reserved memory is >> allocated memory try setting max_split_size_mb to avoid fragmentation.
```

##### Investigation using Environment Variables
Set `PYTORCH_CUDA_ALLOC_CONF` to profile memory allocation and pinpoint if it is raw model size or fragmentation:
```bash
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
python train.py
```
If the error persists, use **PyTorch Memory Profiling** or check the active memory allocations.

##### Resolution
1. Reduce the `per_device_train_batch_size` in your training arguments.
2. Enable **Gradient Accumulation** (e.g., set actual batch size to 2, and aggregate gradients over 4 steps to achieve an effective batch size of 8).
3. Enable **Activation Checkpointing** (recomputes intermediate layers during the backward pass instead of storing them all in memory).
```python
model.gradient_checkpointing_enable()
```

---

#### Incident 2: `CUDA error: device-side assert triggered`
* **Symptom**: Code crashes, but the traceback point is misleading (pointing to an unrelated loss function or print statement).
* **Terminal Error Output**:
```bash
/pytorch/aten/src/ATen/native/cuda/IndexKernel.cu:92: operator(): block: [0,0,0], thread: [15,0,0] Assertion `index >= -sizes[i] && index < sizes[i] && "index out of bounds"` failed.
RuntimeError: CUDA error: device-side assert triggered
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging, consider passing CUDA_LAUNCH_BLOCKING=1.
```

##### Investigation
CUDA execution is asynchronous. When a kernel fails an assertion, the GPU halts, but PyTorch has already queued up multiple subsequent instructions. The error is only reported back to the CPU when it next synchronizes (e.g., when calculating loss or copying data back).

To fix this, force synchronous kernel execution so that PyTorch halts *exactly* on the line of code that caused the failure:
```bash
export CUDA_LAUNCH_BLOCKING=1
python train.py
```
Running this produces the true stack trace:
```bash
Traceback (most recent call last):
  File "train.py", line 28, in <module>
    outputs = model(input_ids)
  File "/opt/conda/lib/python3.10/site-packages/torch/nn/modules/module.py", line 1501, in _call_impl
    return forward_call(*args, **kwargs)
  File "/opt/conda/lib/python3.10/site-packages/transformers/models/llama/modeling_llama.py", line 692, in forward
    inputs_embeds = self.embed_tokens(input_ids)
IndexError: index out of range in self
```

##### Root Cause
The `input_ids` contain a token ID (e.g., `32001`) that is larger than the model’s vocabulary size (e.g., `32000`).

##### Resolution
Fix the tokenizer or pad the embedding layer of the model:
```python
model.resize_token_embeddings(len(tokenizer))
```

---

#### Incident 3: `CUDA error: an illegal memory access was encountered`
* **Symptom**: Kernel crash that corrupts the entire CUDA context. Subsequent CUDA calls in the same script fail immediately.
* **Terminal Error Output**:
```bash
RuntimeError: CUDA error: an illegal memory access was encountered
```

##### Investigation
This is the GPU equivalent of a **Segmentation Fault (SegFault)**. It means a thread tried to read or write to a memory address that it does not own (e.g., out-of-bounds array access inside a custom CUDA kernel).

To investigate, use `cuda-memcheck` or `compute-sanitizer` (NVIDIA's diagnostic tool):
```bash
compute-sanitizer --tool memcheck python train.py
```
This output points directly to the invalid memory offset:
```bash
========= COMPUTE-SANITIZER
========= Invalid __global__ read of size 4 at 0x7fbf20000000 on thread (12,0,0) in block (0,0,0)
=========     by thread 12 in block 0 in custom_attention_kernel(float*, float*)
=========     Address 0x7fbf20000000 is out of bounds
```

##### Resolution
Review the custom CUDA/C++ extension code. Fix the thread index calculations (e.g., ensure thread index `threadIdx.x + blockIdx.x * blockDim.x` does not exceed the allocated array boundary).
