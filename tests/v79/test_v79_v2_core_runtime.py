from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_runtime_configures_four_cpu_devices_before_jax_import():
    code = r'''
import json, os, sys
from pathlib import Path
root=Path(sys.argv[1])
sys.path.insert(0,str(root/'scripts/v79'))
import v79_v2_core_runtime as R
c=json.loads((root/'results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json').read_text())
n=R.configure_before_jax_import(c)
assert n == c['inference']['chains'] == c['resources']['xla_host_devices']
assert os.environ['JAX_PLATFORMS'] == 'cpu'
assert f"--xla_force_host_platform_device_count={n}" in os.environ['XLA_FLAGS']
import v79_v2_core_fit_model
rec=R.validate_imported_jax(c)
assert rec['jax_device_count'] == n
assert rec['jax_platform'] == 'cpu'
print('RUNTIME_OK')
'''
    env = dict(os.environ)
    env.pop("JAX_PLATFORMS", None); env.pop("XLA_FLAGS", None)
    r = subprocess.run([sys.executable, "-c", code, str(ROOT)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "RUNTIME_OK" in r.stdout
