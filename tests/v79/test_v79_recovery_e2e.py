"""End-to-end recovery smoke test through the real entrypoint (run_v79_recovery.py) for one likelihood family:
all six worlds S0-S5 (including the S2 class-permutation and S5 donor-removal paths) at tiny size, then the combine
step. Checks the frozen configuration identity, snapshot identity, attempt records and output schema in every part,
that no expression counts are loaded, and that combine produces one receipt. Statistical values are meaningless at
this size and are not checked. Local only (NumPyro, real design metadata): set V79_E2E=1 and V79_E2E_LIK.
Run it from a snapshot (snapshot_v79.sh) so code_snapshot is a commit."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "scripts" / "v79" / "run_v79_recovery.py"
WORLDS = ("S1_present", "S0_class_absent", "S2_class_permuted", "S3_donor_only", "S4_operator_only",
          "S5_labels_removed")
EXPECTED = {"gaussian": "GAUSSIAN_NC_DK_V1", "bernoulli": "DETECTION_V2_NC_ALL", "ztnb": "ZTNB_NC_DONOR_DK_V1",
            "lognormal": "LOGNORMAL_NC_ALL_V1"}
pytestmark = pytest.mark.skipif(os.environ.get("V79_E2E") != "1", reason="local end-to-end test; set V79_E2E=1")


def test_recovery_suite_end_to_end(tmp_path):
    lik = os.environ.get("V79_E2E_LIK", "bernoulli")
    py = os.environ.get("V79_E2E_PYTHON", sys.executable)
    env = dict(os.environ, XLA_FLAGS="--xla_force_host_platform_device_count=4 --xla_cpu_multi_thread_eigen=false")
    parts = []
    for w in WORLDS:
        out = tmp_path / f"part_{lik}_{w}.json"
        r = subprocess.run([py, str(RUN), "--likelihood", lik, "--fits", w, "--genes", "3", "--warmup", "8",
                            "--draws", "8", "--max-tree-depth", "2", "--out", str(out)],
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0 and out.exists(), (w, r.stderr[-2000:])
        rec = json.loads(out.read_text(encoding="utf-8"))
        assert rec["schema"] == "V79_SIMULATION_RECOVERY_V2" and rec["likelihood"] == lik
        assert rec["sampler_config"]["name"] == EXPECTED[lik] and len(rec["sampler_config"]["sha256"]) == 64
        assert rec["sampler_rules"]["version"] == "A5_V2_DIVERGENT_EXTENSION_ESCALATES"
        assert rec["counts_loaded"] is False and rec["code_snapshot"]
        f = rec["fits"][w]
        assert f["diagnostics"]["attempts"] and "per_site" in f["diagnostics"]
        assert "divergence_location" in f["diagnostics"]
        for a in f["diagnostics"]["attempts"]:  # self-audit 53: every divergent attempt is located
            assert "divergence_location" in a
            assert (a["divergence_location"] is not None) == (sum(a["divergences"]) > 0), a
        if w == "S5_labels_removed":
            assert f["components"] == ["cls", "src", "op"]
        if w == "S2_class_permuted":
            assert f["modification"] == "permute_class"
        parts.append(out)
    receipt = tmp_path / f"V79_SIMULATION_RECOVERY_{lik}.json"
    r = subprocess.run([py, str(RUN), "--combine", str(receipt), *map(str, parts)], capture_output=True, text=True,
                       env=env)
    assert r.returncode == 0 and receipt.exists(), r.stderr[-2000:]
    rec = json.loads(receipt.read_text(encoding="utf-8"))
    assert rec["schema"] == "V79_RECOVERY_SUITE_RECEIPT_V1" and rec["missing_worlds"] == []
    assert rec["terminal"] in ("PASS", "FAIL") and set(rec["parts"]) == {p.name for p in parts}
