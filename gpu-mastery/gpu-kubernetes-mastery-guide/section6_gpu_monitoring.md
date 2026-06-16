# GPU & Kubernetes Mastery Guide
## Section 6: Production GPU Monitoring and Observability

---

### 6.1 The Monitoring Stack: From Hardware to Grafana

To operate an enterprise-grade AI Platform, you need real-time visibility into your GPU hardware. Blindly running workloads leads to silent failures, performance bottlenecks, and massive power bills without corresponding utilization.

The industry-standard observability stack for GPUs on Kubernetes is:

```
+---------------------------------------------------------------+
|                      Grafana Dashboard                        |
|        Visualizes metrics, triggers PagerDuty alerts          |
+---------------------------------------------------------------+
                               ▲
+---------------------------------------------------------------+
|                      Prometheus Server                        |
|        Scrapes metrics and stores time-series data            |
+---------------------------------------------------------------+
                               ▲
+---------------------------------------------------------------+
|                      DCGM Exporter                            |
|  K8s DaemonSet. Exposes GPU metrics in Prometheus format      |
+---------------------------------------------------------------+
                               ▲
+---------------------------------------------------------------+
|             NVIDIA Data Center GPU Manager (DCGM)              |
|  Low-level C library interfacing directly with NVIDIA driver  |
+---------------------------------------------------------------+
                               ▲
+---------------------------------------------------------------+
|                     NVIDIA Kernel Driver                      |
+---------------------------------------------------------------+
```

---

### 6.2 The Tools: nvidia-smi vs. DCGM

#### 1. `nvidia-smi` (NVIDIA System Management Interface)
A command-line utility based on top of **NVML (NVIDIA Management Library)**.
* **Pros**: Installed out-of-the-box with drivers; great for quick ad-hoc CLI inspections.
* **Cons**: Querying `nvidia-smi` requires spawning a subprocess and polling the kernel driver. It is **extremely CPU-heavy**. If you poll `nvidia-smi` once every second, it can consume a significant amount of host CPU cycles and stall GPU command queues. Do **not** use it for production scraping!

#### 2. DCGM (Data Center GPU Manager)
A suite of tools designed specifically for massive clusters.
* **Pros**: It runs as a persistent agent and queries NVML directly in C/C++ memory space. It is extremely lightweight, performant, and supports concurrent metric readers. It also provides advanced telemetry like hardware diagnostic tests and NVLink traffic tracking.

---

### 6.3 Core Production GPU Metrics Explained

Here are the key metrics scraped by DCGM Exporter that must be monitored in production:

#### 1. GPU Utilization (`DCGM_FI_DEV_GPU_UTIL`)
* **What it is**: The percentage of time over the last sample period that one or more kernels were executing on the GPU.
* **The Catch (Misleading Metric)**: This is **not** like CPU utilization. A GPU core is "utilized" if a kernel is running, even if that kernel is sitting idle waiting for memory or utilizing only 1 out of 10,000 threads. To see if your math units are actually busy, you must track **Tensor Core Activity** (`DCGM_FI_DEV_TENSOR_CO_UTIL`) and **FP32 Activity** (`DCGM_FI_DEV_FP32_ACTIVE`).

#### 2. Memory Copy Utilization (`DCGM_FI_DEV_MEM_COPY_UTIL`)
* **What it is**: The percentage of time spent moving data over the memory bus (between VRAM and cache/registers).
* **Significance**: If this metric is high (e.g., >80%) but GPU Utilization is low, your workload is **memory-bandwidth bound**. The GPU is wasting cycles waiting for data to arrive from VRAM.

#### 3. Power Usage (`DCGM_FI_DEV_POWER_USAGE`) & Violations
* **What it is**: Power draw in Watts.
* **Why it matters**: Sudden drops in power consumption indicate training runs have stalled or are waiting on network sync (e.g., all-reduce).
* **Power Violations (`DCGM_FI_DEV_POWER_VIOLATION`)**: Indicates if the GPU is being throttled because it reached its maximum TDP limit.

#### 4. GPU Temperature & Thermal Throttling (`DCGM_FI_DEV_THERMAL_VIOLATION`)
* **What it is**: Core temperature in Celsius.
* **Significance**: If temperatures cross the critical threshold (usually ~80-85°C), the GPU enters thermal throttling, scaling down its core clock speed to prevent physical damage. This causes massive, silent performance degradation.

#### 5. ECC (Error Correcting Code) Errors
* **`DCGM_FI_DEV_ECC_SBE` (Single-Bit Errors)**: Corrected on-the-fly by hardware. High counts indicate degrading memory.
* **`DCGM_FI_DEV_ECC_DBE` (Double-Bit Errors)**: Uncorrectable. This causes the kernel to panic, terminating your container with a bus error. Nodes with DBE must be immediately drained and RMA'd.

#### 6. PCIe and NVLink Bandwidth
* **`DCGM_FI_DEV_PCIE_TX_THROUGHPUT` / `RX_THROUGHPUT`**: Data rate over PCIe.
* **`DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL`**: Data rate over high-speed NVLink.
* **Significance**: Low NVLink utilization during multi-GPU training indicates your parallelization strategies are poorly optimized, or your network card (NIC) is bottlenecking.

---

### 6.4 DCGM Exporter Configuration and Prometheus Scrape Rules

To deploy DCGM Exporter on Kubernetes, you use a DaemonSet that exposes metrics on port `9400`. Here is a production-grade Prometheus scraping rule configuration (`prometheus.yaml` fragment):

```yaml
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

#### Production Prometheus Alerting Rules (`alerts-gpu.yaml`)
These rules alert your platform team *before* hardware issues cause jobs to crash.

```yaml
groups:
  - name: GPUHardwareAlerts
    rules:
      - alert: GPUDoubleBitErrorDetected
        expr: delta(DCGM_FI_DEV_ECC_DBE[5m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Uncorrectable Double-Bit ECC error on node {{ $labels.node }}"
          description: "GPU memory corruption has occurred. This node must be drained and replaced immediately."

      - alert: GPUThermalThrottling
        expr: DCGM_FI_DEV_THERMAL_VIOLATION > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "GPU Thermal Throttling on node {{ $labels.node }}"
          description: "GPU core temperature has exceeded the safe limit. The GPU is scaling back its clock speeds."

      - alert: GPUNVLinkError
        expr: DCGM_FI_DEV_NVLINK_ERROR_COUNT > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "NVLink error detected on node {{ $labels.node }}"
          description: "Physical NVLink connection is failing. Multi-GPU communication is degraded."
```

---

### 6.5 Production Grafana Dashboard Definition (JSON snippet)

Below is an extraction of a production-grade Grafana dashboard panel configuration showing **GPU Utilization** and **VRAM Usage**:

```json
{
  "panels": [
    {
      "title": "GPU Utilization per Device",
      "type": "timeseries",
      "datasource": "Prometheus",
      "targets": [
        {
          "expr": "DCGM_FI_DEV_GPU_UTIL{kubernetes_node=~\"$node\"}",
          "legendFormat": "GPU {{device_id}} on {{kubernetes_node}}"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "drawStyle": "line",
            "lineInterpolation": "smooth"
          },
          "unit": "percent",
          "min": 0,
          "max": 100
        }
      }
    },
    {
      "title": "GPU Memory (VRAM) Usage",
      "type": "timeseries",
      "datasource": "Prometheus",
      "targets": [
        {
          "expr": "DCGM_FI_DEV_FB_USED{kubernetes_node=~\"$node\"} / 1024",
          "legendFormat": "GPU {{device_id}} Memory Used (GB)"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "decbytes",
          "min": 0
        }
      }
    }
  ]
}
```
This telemetry pipeline guarantees that your platform is observable down to individual PCIe buses and memory cells, isolating noisy tenants and flaky hardware in seconds.
