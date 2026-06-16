# GPU & Kubernetes Mastery Guide
## Section 14: Large-Scale Model Serving & Distributed Inference

---

### 14.1 Sharding Strategies for Massive Models

When serving models that exceed the VRAM capacity of a single GPU (e.g., Llama-3-70B requires ~140GB in FP16, but an H100 only has 80GB), you must distribute (shard) the model across multiple GPUs. 

There are three primary dimensions of distributed parallel execution:

```
========================================================================
                      DISTRIBUTED PARALLELISM DIMENSIONS
========================================================================

1. TENSOR PARALLELISM (TP) - Intra-node (High speed)
   [ GPU 0 ] -> Splits matrix columns: W_1 = [A|B]
   [ GPU 1 ] -> Splits matrix columns: W_2 = [C|D]
   * Communicates on EVERY LAYER via high-speed NVLink (AllReduce).

2. PIPELINE PARALLELISM (PP) - Inter-node (Slower)
   [ GPU 0 ] -> Computes Layers 1 to 20   ====> Passes output tensor
   [ GPU 1 ] -> Computes Layers 21 to 40  ====> Passes output tensor
   * Communicates ONLY at boundary points.

3. EXPERT PARALLELISM (EP) - MoE Specific (e.g., DeepSeek, Mixtral)
   [ GPU 0 ] -> Hosts Expert 1 & 2
   [ GPU 1 ] -> Hosts Expert 3 & 4
   * Router routes tokens dynamically to different physical GPUs.
========================================================================
```

---

### 14.2 Deep Dive: Tensor Parallelism (TP)

Tensor Parallelism (Megatron-LM style) splits individual weight matrices *inside* a single layer across multiple GPUs. 

#### Column-Parallel Linear Layer
Consider a standard matrix multiplication $Y = X \cdot W$. 
We can split the weight matrix $W$ vertically into two halves: $W = [W_1 \mid W_2]$.
* **GPU 0** computes: $Y_1 = X \cdot W_1$
* **GPU 1** computes: $Y_2 = X \cdot W_2$
* The outputs are concatenated: $Y = [Y_1 \mid Y_2]$. This requires zero inter-GPU communication!

#### Row-Parallel Linear Layer
Now consider the next linear layer in the network: $Z = Y \cdot V$.
We split the weight matrix $V$ horizontally: $V = \begin{bmatrix} V_1 \\ V_2 \end{bmatrix}$.
* **GPU 0** computes: $Z_1 = Y_1 \cdot V_1$
* **GPU 1** computes: $Z_2 = Y_2 \cdot V_2$
* To get the final output, we must add the partial results: $Z = Z_1 + Z_2$. 
* This addition requires an **`AllReduce`** collective communication operation across NVLink!

$$\mathbf{\text{Communication Bottleneck}}: \text{Because every single Transformer layer contains an MLP block and an Attention block, TP requires multiple AllReduce operations per layer.}$$

*Rule of Thumb*: Because of this intense, low-latency communication requirement, **Tensor Parallelism should NEVER be used across multiple nodes (over standard networks)**. Keep TP restricted to GPUs within the same server (linked by NVLink).

---

### 14.3 Deep Dive: Pipeline Parallelism (PP)

Pipeline Parallelism splits the model vertically by grouping layers. For instance, a model with 80 layers running with PP=4:
* **GPU 0**: Layers 1 - 20
* **GPU 1**: Layers 21 - 40
* **GPU 2**: Layers 41 - 60
* **GPU 3**: Layers 61 - 80

#### Communication
GPU 0 processes its layers, then sends the resulting activation tensors over the network to GPU 1. This happens only once per forward/backward pass of a batch.
* **Pros**: Requires very low network bandwidth. Can be safely executed across physical nodes over standard network connections.
* **Cons**: Introduces the **Pipeline Bubble** (periods where GPUs sit completely idle waiting for activations to arrive from upstream nodes).

---

### 14.4 Mixture of Experts (MoE) & Expert Parallelism (EP)

Models like **Mixtral 8x7B** or **DeepSeek-V2** use a Mixture of Experts architecture. Instead of a single dense feed-forward network (FFN), they contain multiple independent "Experts". A routing network directs each individual token to the top $K$ most qualified experts.

#### Expert Parallelism
Because hosting 8 or 16 experts on a single GPU is impossible, you shard them across physical GPUs.
* **GPU 0**: Expert 1, Expert 2
* **GPU 1**: Expert 3, Expert 4
* When a token is processed, the router identifies which expert is needed. The token is dispatched over NVLink/PCIe to the physical GPU hosting that specific expert (an `AllToAll` collective communication pattern).

---

### 14.5 Real Production Deployment Examples

Here is how you specify these parameters in production container deployments.

#### 1. Serving Llama-3-70B on 4x A100 (80GB) using vLLM
To host this model, we split the 140GB weight matrix across 4 GPUs within a single node using Tensor Parallelism:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: llama-70b-serving
  namespace: serving
spec:
  containers:
    - name: vllm-server
      image: vllm/vllm-openai:latest
      command:
        - "python3"
        - "-m"
        - "vllm.entrypoints.openai.api_server"
        - "--model"
        - "meta-llama/Meta-Llama-3-70B-Instruct"
        - "--tensor-parallel-size"
        - "4" # Set Tensor Parallel to 4 (spreads layers across 4 GPUs in parallel)
        - "--port"
        - "8000"
      resources:
        requests:
          nvidia.com/gpu: "4" # Allocate exactly 4 physical GPUs to this pod
        limits:
          nvidia.com/gpu: "4"
```

#### 2. Serving Mixtral 8x22B on 8x H100 (80GB) using vLLM
Mixtral 8x22B is massive. In FP16, it is over 280GB. We can serve it at ultra-high speed by allocating an entire 8-GPU node:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mixtral-serving
  namespace: serving
spec:
  containers:
    - name: vllm-server
      image: vllm/vllm-openai:latest
      command:
        - "python3"
        - "-m"
        - "vllm.entrypoints.openai.api_server"
        - "--model"
        - "mistralai/Mixtral-8x22B-Instruct-v0.1"
        - "--tensor-parallel-size"
        - "8" # Split model across all 8 GPUs inside the HGX node via high-speed NVLink
        - "--max-model-len"
        - "32768"
        - "--port"
        - "8000"
      resources:
        requests:
          nvidia.com/gpu: "8"
        limits:
          nvidia.com/gpu: "8"
```
This configuration utilizes the physical HGX crossbar backplane, passing model activation layers back and forth over 900 GB/s NVLinks, providing low-latency generation for highly concurrent enterprise workloads.
