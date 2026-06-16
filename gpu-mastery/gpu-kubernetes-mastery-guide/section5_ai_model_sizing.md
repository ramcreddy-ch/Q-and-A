# GPU & Kubernetes Mastery Guide
## Section 5: AI Model Sizing and Capacity Planning

---

### 5.1 Precision Formats: Bytes and Mathematical representation

To estimate how many GPUs your cluster needs, you must first understand precision formats and how much space a single model parameter occupies.

```
+-----------------------------------------------------------------------+
| FP32 (Single Precision) - 4 Bytes                                      |
| [1 Sign Bit] [8 Exponent Bits] [23 Mantissa Bits]                     |
+-----------------------------------------------------------------------+
| FP16 (Half Precision) - 2 Bytes                                       |
| [1 Sign Bit] [5 Exponent Bits] [10 Mantissa Bits]                     |
+-----------------------------------------------------------------------+
| BF16 (Brain Floating Point) - 2 Bytes                                 |
| [1 Sign Bit] [8 Exponent Bits] [7 Mantissa Bits]                      |
| *Note: Has the same dynamic range as FP32, making training more stable!|
+-----------------------------------------------------------------------+
| FP8 (E4M3 or E5M2) - 1 Byte                                           |
| [1 Sign Bit] [4/5 Exponent Bits] [3/2 Mantissa Bits]                  |
+-----------------------------------------------------------------------+
| INT8 (Integer) - 1 Byte                                               |
| [8 Integer Bits]                                                      |
+-----------------------------------------------------------------------+
| INT4 (Integer) - 0.5 Bytes                                            |
| [4 Integer Bits]                                                      |
+-----------------------------------------------------------------------+
```

---

### 5.2 The VRAM Equation: Training vs. Inference

VRAM capacity requirements are vastly different for training versus inference.

#### 1. Inference Memory Requirements
To run inference, the GPU must hold:
* **Model Parameters ($M_p$)**: The weight tensors of the model.
* **KV Cache ($M_{kv}$)**: Space for active sessions/tokens.
* **Overhead ($M_{oh}$)**: CUDA context, framework allocations (~1-2 GB).

$$\text{VRAM}_{\text{inference}} = (\Phi \times B_p) + M_{kv} + M_{oh}$$

Where:
* $\Phi$ = Number of model parameters (in billions).
* $B_p$ = Bytes per parameter based on precision (FP16 = 2, INT8 = 1, INT4 = 0.5).

#### 2. Training Memory Requirements (Adam Optimizer)
Training is far more memory-intensive because we must store gradients, optimizer states, and activations.
Using the Adam optimizer in mixed precision (BF16/FP32):
* **Parameters**: 2 bytes per parameter (BF16).
* **Gradients**: 2 bytes per parameter (BF16).
* **Optimizer States**: Adam maintains two states per parameter in FP32 (mean and variance), plus an FP32 master copy of the weights.
  * FP32 Master Weights = 4 bytes/param.
  * Momentum (FP32) = 4 bytes/param.
  * Variance (FP32) = 4 bytes/param.
  * **Total Optimizer States = 12 bytes per parameter.**
* **Activations**: Scales with sequence length, batch size, and architecture depth.

$$\text{VRAM}_{\text{training\_base}} = \Phi \times (2_{\text{Params}} + 2_{\text{Gradients}} + 12_{\text{Optimizer}}) = \mathbf{\Phi \times 16 \text{ Bytes}}$$

*Rule of Thumb*: Standard mixed-precision training requires **at least 16-20 GB of VRAM per Billion parameters** (excluding activations and checkpoints).

---

### 5.3 Step-by-Step VRAM and GPU Sizing Calculations

Let's calculate the exact VRAM and GPU requirements for 5 key models.

---

#### Scenario 1: Llama-3-8B (FP16, BF16, INT4 Inference)
* **Parameters ($\Phi$)**: 8 Billion

##### FP16 / BF16 Inference Sizing:
* Model Weights: $8 \times 2 \text{ Bytes} = \mathbf{16 \text{ GB}}$
* KV Cache (Batch size 16, context 4,096, Grouped-Query Attention): $\approx \mathbf{2.5 \text{ GB}}$
* Overhead: $\mathbf{1.5 \text{ GB}}$
* **Total VRAM Needed**: $16 + 2.5 + 1.5 = \mathbf{20 \text{ GB}}$
* **GPU Requirement**: **1x L4 (24GB)**, **1x A10 (24GB)**, or **1x A100 (40GB/80GB)**.

##### INT4 Quantized Inference Sizing:
* Model Weights: $8 \times 0.5 \text{ Bytes} = \mathbf{4 \text{ GB}}$
* KV Cache + Overhead: $\approx \mathbf{3 \text{ GB}}$
* **Total VRAM Needed**: $4 + 3 = \mathbf{7 \text{ GB}}$
* **GPU Requirement**: **1x T4 (16GB)** or **1x L4 (24GB)**. Highly cost-effective.

---

#### Scenario 2: Mistral-13B (FP16 Inference and Training)
* **Parameters ($\Phi$)**: 13 Billion

##### FP16 Inference Sizing:
* Model Weights: $13 \times 2 = \mathbf{26 \text{ GB}}$
* KV Cache (Batch size 32, context 4,096): $\approx \mathbf{8 \text{ GB}}$
* Overhead: $\mathbf{2 \text{ GB}}$
* **Total VRAM Needed**: $26 + 8 + 2 = \mathbf{36 \text{ GB}}$
* **GPU Requirement**: **1x A100 (40GB or 80GB)**, **1x L40S (48GB)**, or **2x L4 (24GB x 2 = 48GB using Tensor Parallelism)**.

##### Training Sizing (Adam Mixed Precision):
* Base VRAM (Params, Grads, Opt): $13 \times 16 \text{ Bytes} = \mathbf{208 \text{ GB}}$
* Activations: $\approx \mathbf{40 \text{ GB}}$
* **Total VRAM Needed**: $\approx \mathbf{248 \text{ GB}}$
* **GPU Requirement**: **4x A100 (80GB)** or **4x H100 (80GB)**, using DeepSpeed ZeRO or Model Sharding.

---

#### Scenario 3: CodeLlama-34B (FP16 Inference)
* **Parameters ($\Phi$)**: 34 Billion

##### FP16 Inference Sizing:
* Model Weights: $34 \times 2 = \mathbf{68 \text{ GB}}$
* KV Cache (Batch size 16, context 8,096): $\approx \mathbf{12 \text{ GB}}$
* Overhead: $\mathbf{2 \text{ GB}}$
* **Total VRAM Needed**: $68 + 12 + 2 = \mathbf{82 \text{ GB}}$
* **GPU Requirement**: **1x H100 (80GB)** is just barely too small. You require **2x A100 (80GB)**, **2x H100 (80GB)**, or **2x L40S (48GB x 2 = 96GB)** running Tensor Parallelism.

---

#### Scenario 4: Llama-3-70B (BF16 Inference and Training)
* **Parameters ($\Phi$)**: 70 Billion

##### BF16 Inference Sizing:
* Model Weights: $70 \times 2 = \mathbf{140 \text{ GB}}$
* KV Cache (Batch size 32, context 8,192): $\approx \mathbf{22 \text{ GB}}$
* Overhead: $\mathbf{3 \text{ GB}}$
* **Total VRAM Needed**: $140 + 22 + 3 = \mathbf{165 \text{ GB}}$
* **GPU Requirement**: 
  * **2x H100 (80GB)** = 160GB (Too small for full 8,192 context at high batch size).
  * **2x H200 (141GB)** = 282GB (Excellent, lots of head-room for high batch sizes).
  * **4x A100 (80GB)** = 320GB (Standard cloud placement).

##### Training Sizing (Adam Mixed Precision):
* Base VRAM: $70 \times 16 \text{ Bytes} = \mathbf{1,120 \text{ GB}}$ (1.12 Terabytes!)
* Activations (with checkpointing): $\approx \mathbf{200 \text{ GB}}$
* **Total VRAM Needed**: $\approx \mathbf{1,320 \text{ GB}}$
* **GPU Requirement**:
  * **16x H100 (80GB)** = 1,280 GB (Just barely enough if ZeRO-3 is fully optimized).
  * **32x H100 (80GB)** (Standard industrial partition size).

---

#### Scenario 5: Llama-3-405B (FP16 Inference and Training)
* **Parameters ($\Phi$)**: 405 Billion

##### FP16 Inference Sizing:
* Model Weights: $405 \times 2 = \mathbf{810 \text{ GB}}$
* KV Cache (Batch size 32, context 8,192): $\approx \mathbf{120 \text{ GB}}$
* Overhead: $\mathbf{10 \text{ GB}}$
* **Total VRAM Needed**: $810 + 120 + 10 = \mathbf{940 \text{ GB}}$
* **GPU Requirement**:
  * **8x H100 (80GB)** = 640GB (Insufficient).
  * **8x H200 (141GB)** = 1,128GB (Perfect. A single HGX H200 node can host Llama-3-405B in FP16/BF16 at full speed).
  * **16x A100 (80GB)** = 1,280GB.

##### Training Sizing (Adam Mixed Precision):
* Base VRAM: $405 \times 16 \text{ Bytes} = \mathbf{6,480 \text{ GB}}$ (6.48 Terabytes!)
* **Total VRAM Needed (including activations)**: $\approx \mathbf{7.5 \text{ Terabytes}}$
* **GPU Requirement**:
  * Minimum of **128x H100 (80GB)** GPUs utilizing 3D Parallelism (Tensor, Pipeline, and Data Parallelism via Megatron-LM).
