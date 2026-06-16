# GPU & Kubernetes Mastery Guide
## Section 8: Kubernetes GPU Fundamentals

---

### 8.1 The Kubernetes GPU Execution Pipeline

By default, Kubernetes does not natively understand what a "GPU" is. Its core scheduler is built to handle CPU and Memory resources. To expose GPU hardware to containerized workloads, Kubernetes relies on the **Device Plugin Framework**.

Here is the exact request-to-execution pipeline when a GPU pod is scheduled:

```
+-------------------------------------------------------------+
|               1. Developer submits Pod Spec                 |
|               (requests: nvidia.com/gpu: 1)                 |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|           2. Kube-Scheduler filters nodes with               |
|               matching Extended Resources                   |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|        3. Kubelet on target node assigns GPU PCI ID         |
|         & calls NVIDIA Container Toolkit via CRI            |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|       4. Container Runtime (containerd) calls OCI           |
|          prestart hook: 'nvidia-container-runtime'          |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|     5. NVIDIA Container Runtime binds host driver           |
|        libraries and physical dev files into container      |
|             (e.g., /dev/nvidia0, /dev/nvidia-uvm)           |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|            6. Containerized application launches            |
|               with full access to CUDA driver               |
+-------------------------------------------------------------+
```

---

### 8.2 Extended Resources and the Device Plugin

#### Extended Resources
Because GPUs are not first-class scheduling objects, they are registered in the Node status as **Extended Resources** using the format `nvidia.com/gpu`.
When the **NVIDIA Device Plugin** registers itself with the local Kubelet, it announces the number of available physical GPUs:
```json
"status": {
  "allocatable": {
    "cpu": "64",
    "memory": "263884824Ki",
    "nvidia.com/gpu": "8"
  },
  "capacity": {
    "cpu": "64",
    "memory": "263884824Ki",
    "nvidia.com/gpu": "8"
  }
}
```

* **Scheduling Limit**: Extended Resources do not support overcommit. Unlike CPU/Memory where you can specify `requests` and `limits` differently, for GPUs, **requests and limits must be equal**. If you ask for `nvidia.com/gpu: 1`, you are guaranteed exclusive access to that physical GPU device.

---

### 8.3 Node Labels, Affinity, Taints, and Tolerations

Running multi-tenant AI clusters requires separating CPU-only workloads from expensive GPU nodes. You do this using Node Labels, Node Affinity, Taints, and Tolerations.

#### 1. Node Labels
The GPU Operator or Node Feature Discovery (NFD) automatically applies descriptive labels to your nodes:
```text
nvidia.com/gpu.family=hopper
nvidia.com/gpu.machine=HGX-H100
nvidia.com/gpu.memory=80160MiB
nvidia.com/gpu.product=NVIDIA-H100-SXM5-80GB
```

#### 2. Taints and Tolerations
GPU nodes are extremely expensive (an 8-GPU H100 node can cost upwards of $300,000 to buy, or $4/hour per GPU to rent). You must prevent standard web microservices or background cronjobs from accidentally scheduling on them.
* **Taint the GPU Nodes**:
```bash
kubectl taint nodes node-gpu-01.cluster.local sku=gpu:NoSchedule
```
* **Add Toleration to GPU Pods**: Only pods with the corresponding toleration can schedule on these nodes.

---

### 8.4 Complete Production Kubernetes GPU Manifest

Here is a complete, production-grade manifest illustrating best practices for node isolation, scheduling affinity, and device resource consumption:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llama-inference-deployment
  namespace: serving
  labels:
    app: llama-inference
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llama-inference
  template:
    metadata:
      labels:
        app: llama-inference
    spec:
      # 1. Prevent standard microservices from using these nodes, and allow this pod to schedule on GPU tainted nodes
      tolerations:
        - key: "sku"
          operator: "Equal"
          value: "gpu"
          effect: "NoSchedule"

      # 2. Strict scheduling: Force placement ONLY on H100 SXM5 nodes
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: nvidia.com/gpu.product
                    operator: In
                    values:
                      - NVIDIA-H100-SXM5-80GB

      containers:
        - name: vllm-server
          image: vllm/vllm-openai:v0.4.2
          imagePullPolicy: IfNotPresent
          command:
            - "python3"
            - "-m"
            - "vllm.entrypoints.openai.api_server"
            - "--model"
            - "meta-llama/Meta-Llama-3-8B-Instruct"
            - "--port"
            - "8000"
          ports:
            - containerPort: 8000
              name: http
          resources:
            # 3. Requesting exact GPU allocations
            requests:
              cpu: "8"
              memory: "32Gi"
              nvidia.com/gpu: "1" # Request exactly 1 physical GPU
            limits:
              cpu: "16"
              memory: "64Gi"
              nvidia.com/gpu: "1" # Limit must equal request for extended resources
          env:
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: huggingface-secret
                  key: hf_token
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 120
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 120
            periodSeconds: 20
```
This configuration guarantees your expensive Hopper nodes are preserved solely for the targeted inference pipelines and ensures standard pods never steal valuable scheduling slots.
