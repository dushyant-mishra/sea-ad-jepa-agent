# Discovery Atlas Lightweight Checks

## Summary

- Pass: 8
- Fail: 0
- Heavy model inference: not run
- Baseline and manifold audit outputs: not regenerated
- Discovery logic tests: imported and called by function name
- Open-validation alignment tests: direct synthetic runner

## Checks

| check | status | return_code | command |
| --- | --- | --- | --- |
| compile::discovery_atlas/audit_discovery_atlas_final_state.py | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe -m py_compile discovery_atlas/audit_discovery_atlas_final_state.py` |
| compile::discovery_atlas/internal_robustness_stability_v1.py | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe -m py_compile discovery_atlas/internal_robustness_stability_v1.py` |
| compile::discovery_atlas/build_internal_evidence_scorecard_v1.py | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe -m py_compile discovery_atlas/build_internal_evidence_scorecard_v1.py` |
| compile::discovery_atlas/ablation_artifact_readiness_v1.py | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe -m py_compile discovery_atlas/ablation_artifact_readiness_v1.py` |
| compile::open_validation/align_to_graph_jepa.py | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe -m py_compile open_validation/align_to_graph_jepa.py` |
| final_state_audit | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe discovery_atlas/audit_discovery_atlas_final_state.py` |
| discovery_logic_direct_tests | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe -c import tests.test_discovery_atlas_logic as t; tests=[getattr(t,n) for n in sorted(dir(t)) if n.startswith('test_') and callable(getattr(t,n))]; [test() for test in tests]; print(f'{len(tests)} discovery logic tests passed')` |
| open_validation_alignment_direct_tests | pass | 0 | `C:\Users\dushy\anaconda3\envs\sea-ad-jepa\python.exe tests/test_open_validation_alignment.py` |

## Output tails

### compile::discovery_atlas/audit_discovery_atlas_final_state.py

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
(empty)
```

Stderr tail:

```text
(empty)
```

### compile::discovery_atlas/internal_robustness_stability_v1.py

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
(empty)
```

Stderr tail:

```text
(empty)
```

### compile::discovery_atlas/build_internal_evidence_scorecard_v1.py

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
(empty)
```

Stderr tail:

```text
(empty)
```

### compile::discovery_atlas/ablation_artifact_readiness_v1.py

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
(empty)
```

Stderr tail:

```text
(empty)
```

### compile::open_validation/align_to_graph_jepa.py

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
(empty)
```

Stderr tail:

```text
(empty)
```

### final_state_audit

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
status
pass    38
Wrote results\tables\discovery_atlas_final_state_audit.csv
Wrote results\reports\discovery_atlas_final_state_audit.md
```

Stderr tail:

```text
(empty)
```

### discovery_logic_direct_tests

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
4 discovery logic tests passed
```

Stderr tail:

```text
(empty)
```

### open_validation_alignment_direct_tests

- Status: `pass`
- Return code: `0`

Stdout tail:

```text
8 open-validation alignment tests passed
```

Stderr tail:

```text
(empty)
```
