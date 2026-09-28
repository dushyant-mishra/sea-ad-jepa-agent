import json
import subprocess
import sys
from pathlib import Path


def test_lane_r2_mut5_exercises_exact_recovered_producer(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts" / "lane_r2" / "laneR2_mut5_producer_path_regression_v2.py"
    out = tmp_path / "out"
    scratch = tmp_path / "scratch"
    proc = subprocess.run(
        [sys.executable, str(script), "--scratch", str(scratch), "--out-dir", str(out)],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    report = json.loads((out / "laneR2_mut5_producer_path_regression_v2.json").read_text())
    assert report["verdict"] == "PASS_PRODUCER_DEGENERACY_PATH_EXERCISED"
    assert all(report["checks"].values())
