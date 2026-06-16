# GPU & Kubernetes Mastery Guide
## Section 16: GPU Security & Multi-Tenancy

---

### 16.1 Multi-Tenant Isolation Strategies

Running multi-tenant GPU infrastructure (where different teams, clients, or untrusted user scripts share the same physical cluster) introduces unique security vectors. 

```
========================================================================
                      GPU SECURITY THREAT MATRIX
========================================================================
1. MEMORY LEAKAGE  -> Pod A reads data left in VRAM by Pod B
   * Fix: Enable MPS isolation or use physical MIG partitions.

2. HOST ESCAPE     -> Pod escapes container via NVIDIA Driver exploit
   * Fix: Run non-root containers; utilize gVisor/Kata Containers.

3. MODEL THEFT     -> Unauthorized access to physical model weights in storage
   * Fix: Encrypt volumes at rest; implement strict K8s RBAC.

4. CONFIDENTIAL AI -> Data decrypted in HBM during processing
   * Fix: Enable Hopper APM (Asynchronous Protected Memory).
========================================================================
```

#### 1. Software-Level Isolation
If multiple tenants share a GPU via **Time-Slicing**, there is no hardware memory separation. The GPU driver attempts to clear VRAM when context switching, but vulnerabilities in the driver's memory management have historically allowed "cold boot" style data extraction. 
* *Rule*: Never mix untrusted tenants or different compliance boundaries (e.g., PCI-DSS vs. public dev) on time-sliced GPUs.

#### 2. Hardware-Level Isolation (MIG Security)
MIG represents the gold standard for standard multi-tenancy. Because each partition has its own dedicated physical memory controller, it is impossible for code running on `mig-1` to read or write to memory registers on `mig-2`. This is enforced at the silicon level.

---

### 16.2 Network Policies for GPU Workloads

GPU pods running distributed training require extensive network communication. However, you must lock down non-essential traffic. For instance, an inference Pod serving public users should have zero network access to your internal data storage or databases.

#### Production NetworkPolicy for an Inference API
This policy allows the API to receive public traffic from the Ingress controller and communicate with the local Hugging Face proxy, but blocks all other egress.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: inference-security-policy
  namespace: serving
spec:
  podSelector:
    matchLabels:
      app: llama-inference
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow traffic ONLY from the Istio Ingress Gateway namespace
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: istio-system
      ports:
        - protocol: TCP
          port: 8000
  egress:
    # Allow DNS resolution
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
    # Allow outbound connections ONLY to Hugging Face Model Registry IP range
    - to:
        - ipBlock:
            cidr: 54.235.1.0/24
      ports:
        - protocol: TCP
          port: 443
```

---

### 16.3 GPU Workloads in Regulated Industries (Confidential Computing)

For healthcare, finance, or defense, standard encryption-at-rest and in-transit is insufficient. Data is highly vulnerable when it is decrypted in system RAM or GPU memory for active training and inference.

#### Hopper and Blackwell Confidential Computing (CC)
NVIDIA introduced native hardware **Confidential Computing** in Hopper (H100) and Blackwell.
* **Hardware-Rooted Trust**: The GPU hardware generates a cryptographic attestation report verified by a remote service (like NVIDIA Attestation Service) before loading keys.
* **Encrypted PCIe Bus**: All data transferred between the CPU and GPU over the PCIe bus is transparently encrypted at the hardware level using **AES-GCM-256**.
* **Protected VRAM (APM)**: Physical GPU memory is hardware-encrypted. If a bad actor physically probes the HBM chip pins on the motherboard, they will only see encrypted noise.

To enable this in Kubernetes, you must deploy the GPU Operator with Confidential Computing enabled, which configures secure guest VM environments (like AMD SEV-SNP or Intel TDX) to map direct encrypted pathways to the Hopper GPU.
```yaml
# Fragment in ClusterPolicy
spec:
  confidentialComputing:
    enabled: true
```
This configuration ensures that your model weights, training datasets, and end-user prompts remain fully encrypted and secure, even if the underlying physical host node or hypervisor is fully compromised.
