# LLM Evaluation

This directory holds evaluation datasets and logic for the financial research assistant.

## Evaluation layers
- retrieval quality
- citation presence and correctness
- groundedness
- insufficient-evidence refusal behavior
- entitlement safety
- latency and token budget regression

## Release rule
A prompt, retriever, or model change is not promotion-ready unless it passes the required evaluation bundle for its risk tier.
