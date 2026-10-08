from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_numerical_synthetic_recoverability_smoke():
    p=ROOT/"scripts/v64/privileged_recoverability_numerical_synthetic_smoke_v1.py"
    out=subprocess.check_output([sys.executable,str(p)],text=True,cwd=ROOT)
    j=json.loads(out)
    assert j["real_biology_used"] is False
    assert j["full"]["chosen_rank"]==16
    assert 0 < j["partial"]["chosen_rank"] < 16
    assert j["technical"]["chosen_rank"]==0
