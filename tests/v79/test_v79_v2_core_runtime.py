from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import v79_v2_core_runtime_lock as RL  # noqa: E402


def test_runtime_package_lock_matches_frozen_environment_and_refuses_mismatch():
    locked = RL.load_locked_versions(ROOT)
    rec = RL.validate_runtime(ROOT, observed=locked, require_windows=False, required_cpu_devices=None)
    assert rec["environment_lock_sha256"] == RL.ENV_LOCK_SHA256
    assert rec["matched_packages"] == len(locked)
    bad = dict(locked); bad["numpy"] = "999.0.0"
    with pytest.raises(RL.RuntimeLockRefused, match="mismatch"):
        RL.validate_runtime(ROOT, observed=bad, require_windows=False, required_cpu_devices=None)


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
