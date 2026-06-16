# Training Pipeline Reference

## Production training flow
```text
data readiness check
  -> immutable snapshot validation
  -> SageMaker training job
  -> evaluation on replay-aligned validation set
  -> threshold calibration
  -> model registration
  -> stage deployment trigger
```

## Required lineage fields
- training snapshot URI
- feature bundle version
- label definition version
- training image digest
- inference image digest
- evaluation report URI
- threshold calibration artifact URI

## Why this matters
A fraud model is only deployable if engineering, evaluation, and decision-threshold artifacts all move together in a controlled way.
