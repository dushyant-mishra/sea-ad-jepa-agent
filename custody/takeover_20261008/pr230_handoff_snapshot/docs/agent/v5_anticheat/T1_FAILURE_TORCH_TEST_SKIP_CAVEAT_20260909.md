# T1 failure torch-dependent test skip caveat — 2026-09-09

Status: `ADOPTION_RISK_RECORDED__NO_TRAINING_AUTHORITY`

The C2 mandatory-gradient-gate package language must not be summarized as simply:

```text
Thirteen adversarial tests pass.
```

On a checkout without `torch`, the observed result was:

```text
9 passed, 4 skipped — could not import 'torch'
```

The skipped tests include the live-tensor subnormal/norm-defect case, which is one of the most important checks in the file. This matters because one historical verifier defect came from computing norms on live tensors: fp32's smallest subnormal can square below representable range and appear dead. The repaired gate therefore must avoid live-tensor norm checks and must reject exact-zero protected gradients/moments against the frozen 48-tensor registry.

## Required adoption rule

Any future adoption of the C2 mandatory-gradient gate must prove:

```text
TORCH_DEPENDENT_TESTS_EXECUTED = true
SKIPPED_TORCH_DEPENDENT_TESTS = 0
LIVE_TENSOR_SUBNORMAL_TEST_EXECUTED = true
FROZEN_48_TENSOR_REGISTRY_CHECK_EXECUTED = true
```

A green suite with skipped torch-dependent tests is not sufficient for production trainer adoption.
