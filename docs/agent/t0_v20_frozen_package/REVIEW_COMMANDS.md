# T0 V20 external-review commands

Run from a clean extraction with repository root as current directory.

```bash
set -euo pipefail

# Compile all current Python.
python - <<'PY'
from pathlib import Path
files=sorted(Path('current/code').glob('*.py'))+sorted(Path('current/tests').glob('*.py'))
for p in files: compile(p.read_bytes(),str(p),'exec')
print('compiled',len(files))
PY

# Static authority/contract equivalence.
PYTHONPATH=current/code python current/code/audit_t0_v20_execution_authority_equivalence.py

# Exact collection.
PYTHONPATH=current/code pytest --collect-only -q current/tests

# STOP-ground A first.
PYTHONPATH=current/code pytest -q \
  current/tests/test_t0_inference_safe_v1.py \
  current/tests/test_t0_studentized_fl_v1.py

# Execution-input binding attacks.
PYTHONPATH=current/code pytest -q current/tests/test_t0_execution_input_authority_v1.py

# V20 governance.
PYTHONPATH=current/code pytest -q \
  current/tests/test_t0_public_api_authority_map_v3.py \
  current/tests/test_t0_v20_active_test_manifest.py \
  current/tests/test_t0_v20_contract_equivalence.py

# Full suite; this terminal is required separately from the static audit.
PYTHONPATH=current/code pytest -q current/tests
```

Also independently inspect that malformed float/shape/range permutations raise before alias/HC3 estimability and that no superseded registry `active_path` exists under `current/`.
