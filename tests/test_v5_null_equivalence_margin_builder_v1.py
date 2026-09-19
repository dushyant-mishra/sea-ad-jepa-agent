import json
from pathlib import Path
import shutil
import subprocess
import sys


SCRIPT = Path("scripts/agent/build_full104_null_equivalence_margin_authority_v1_20260918.py")
HISTORICAL = Path(
    "analysis/v5_masking_successor_spike_20260917/reports/"
    "JEPA_MASKING_SCALE_STRESS_FOLLOWUP_20260917.md"
)


def test_null_margin_builder_is_fixed_and_has_no_free_numeric_cli():
    source = SCRIPT.read_text(encoding="utf-8")
    compile(source, str(SCRIPT), "exec")
    assert "NullEquivalenceMarginAuthorityV1" in source
    assert "HISTORICAL_SCALE_CONTEXT_SHA256" in source
    assert "Within-donor shuffled negative: mean delta -0.000240" in source
    assert "0.0030 to 0.0116" in source
    assert "--margin" not in source
    assert "--null-equivalence-margin-numerator" not in source
    assert "--null-equivalence-margin-denominator" not in source
    for forbidden in (
        "stage81",
        "t1_checkpoint",
        "X_common6000",
        "terminal_masking_policy_outcomes",
    ):
        assert forbidden.lower() not in source.lower()


def test_builder_executes_against_exact_frozen_scale_context(tmp_path):
    out = tmp_path / "margin.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            ".",
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "V5_NULL_EQUIVALENCE_MARGIN_AUTHORITY_V1"
    assert payload["margin_numerator"] == 1
    assert payload["margin_denominator"] == 1000
    assert payload["margin"] == 0.001
    assert payload["terminal_outcomes_inspected_before_freeze"] is False
    assert payload["training_authorized"] is False
    assert "TARGETS" in payload["does_not_authorize"]
    assert "FOLDS" in payload["does_not_authorize"]
    assert "BURDEN" in payload["does_not_authorize"]
    assert "SEED" in payload["does_not_authorize"]
    assert "ROW_CAP" in payload["does_not_authorize"]
    assert "POLICY_SELECTION" in payload["does_not_authorize"]


def test_builder_fails_closed_on_historical_scale_context_byte_drift(tmp_path):
    fake_repo = tmp_path / "repo"
    target = fake_repo / HISTORICAL
    target.parent.mkdir(parents=True)
    shutil.copyfile(HISTORICAL, target)
    target.write_text(
        target.read_text(encoding="utf-8") + "\nTAMPER\n",
        encoding="utf-8",
    )
    out = tmp_path / "should-not-exist.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(fake_repo),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "byte drift" in (completed.stdout + completed.stderr)
    assert not out.exists()
