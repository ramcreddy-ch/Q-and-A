# GPU & Kubernetes Mastery Guide
## Section 15: GPU Autoscaling & Karpenter Integration

---

### 15.1 The Autoscaling Stack

Autoscaling GPU workloads is fundamentally different from scaling traditional CPU-bound web APIs. 
* **Traditional APIs**: Scale based on CPU utilization or HTTP request rate.
* **GPU Inference APIs**:
  * Scaling based on CPU is useless.
  * Scaling based on standard GPU utilization is highly lagging or misleading (due to the PyTorch allocator reserving memory/cycles).
  * **The Correct Approach**: Scale based on **vLLM queue length** (active + pending requests), **concurrency**, or **latency**.

```
+-------------------------------------------------------------+
|                     Client Request Spikes                   |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|             KEDA (Polling vLLM Metrics Endpoint)            |
|       - Identifies queue size / pending requests > 10        |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|           Horizontal Pod Autoscaler (HPA) triggers          |
|                 - Schedules new Inference Pod               |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|             Pod is "Pending" (Insufficient GPUs)            |
+-------------------------------------------------------------+
                               ↓
+-------------------------------------------------------------+
|              Karpenter (or Cluster Autoscaler)              |
|        - Intercepts Pending Pod, provisions H100 node       |
|          from cloud provider in < 60 seconds                |
+-------------------------------------------------------------+
```

---

### 15.2 KEDA (Kubernetes Event-Driven Autoscaling)

**KEDA** is a lightweight operator that acts as a custom metrics adapter. It can query external or internal sources (like Prometheus) and drive the Horizontal Pod Autoscaler directly.

For vLLM, we scale based on the metric `vllm:num_requests_waiting` (the number of user requests waiting in the queue because the KV cache is full).

#### Production KEDA Scaler Manifest
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: vllm-autoscaler
  namespace: serving
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llama-inference-deployment
  minReplicaCount: 1
  maxReplicaCount: 10
  cooldownPeriod: 300 # Wait 5 minutes before scaling down to prevent "flapping"
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleUp:
          stabilizationWindowSeconds: 0
          policies:
            - type: Percent
              value: 100
              periodSeconds: 15
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus-k8s.monitoring.svc.cluster.local:9090
        metricName: vllm_num_requests_waiting
        # Scale up if the average queue size of waiting requests exceeds 5
        query: sum(vllm:num_requests_waiting)
        threshold: '5'
```

---

### 15.3 Fast Node Provisioning with Karpenter

When KEDA/HPA scales your deployment from 1 replica to 5 replicas, the new pods will immediately enter the `Pending` state because there are no free H100 GPUs in the cluster.

Standard **Cluster Autoscaler** is notoriously slow; it can take 5 to 10 minutes to spin up a new GPU node because it evaluates nodes sequentially and makes slow cloud API requests.

**Karpenter** (developed by AWS) is an ultra-fast, node-level scheduler. It bypasses Kubernetes Node Groups and talks directly to the cloud provider's EC2 fleet API, spinning up raw instances based on the exact requirements of the pending pods in **less than 60 seconds**.

#### Production Karpenter NodePool Specification
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: gpu-nodepool
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"] # Use on-demand for critical training/inference
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["p4", "p5"] # Allocate AWS p4d (A100) or p5 (H100) instances
        - key: karpenter.k8s.aws/instance-generation
          operator: In
          values: ["edge", "current"]
      nodeClassRef:
        name: default-aws-nodeclass
  limits:
    nvidia.com/gpu: 64 # Absolute cap on total cluster GPUs to prevent run-away costs
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 720h # Auto-recycle nodes after 30 days to apply OS updates
```

With this autoscaling integration, your platform dynamically scales up under high user traffic, spins up fresh physical hardware in a minute, and tears them down the moment the queue empties, preventing thousands of dollars in idle cloud compute costs.
