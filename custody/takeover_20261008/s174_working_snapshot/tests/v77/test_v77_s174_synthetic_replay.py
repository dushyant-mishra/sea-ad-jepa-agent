"""S174 synthetic replay: each corrected receipt changed only the universe, each runner reproduced its
committed receipt exactly on the old universe first, and the committed summary is what the committed
code produces from the committed receipts."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v77" / "summarize_s174_synthetic_replay.py"
NEW = ROOT / "results" / "v77" / "s174_replay"
REC = NEW / "S174_SYNTHETIC_REPLAY_V1.json"
MD = ROOT / "docs" / "agent" / "S174_SYNTHETIC_REPLAY.md"
REPRO = NEW / "repro_old_universe"
spec = importlib.util.spec_from_file_location("s174_synth", SCRIPT)
S = importlib.util.module_from_spec(spec)
sys.modules["s174_synth"] = S
spec.loader.exec_module(S)
VARYING = ("--universe", "--out", "--universe-name")


def _rec() -> dict:
    return json.loads(REC.read_text(encoding="utf-8"))


def _fixed_args(command: str) -> list[str]:
    """The command without the arguments a replay is allowed to change."""
    toks, out, skip = command.split(), [], False
    for t in toks:
        if skip:
            skip = False
            continue
        if t in VARYING:
            skip = True
            continue
        out.append(t)
    return out


def test_each_runner_reproduced_its_committed_receipt_exactly_on_the_old_universe():
    for name, repro in S.REPLAYS.items():
        r = S.reproduction(ROOT / "results" / "v77" / name, REPRO / repro)
        assert r["exact"] and r["numeric_leaves"] > 50, (name, r["differing"])


def test_each_replay_changed_only_the_universe():
    n_corrected = json.loads((NEW / "V77_FROZEN_EVALUATION_UNIVERSE_V1.json").read_text(encoding="utf-8"))["n_genes"]
    for name in S.REPLAYS:
        old = json.loads((ROOT / "results" / "v77" / name).read_text(encoding="utf-8"))
        new = json.loads((NEW / name).read_text(encoding="utf-8"))
        assert _fixed_args(old["command"]) == _fixed_args(new["command"]), name
        assert "s174_replay" in new["command"] and "s174_replay" not in old["command"], name
        assert new["provenance_status"] == "CLEAN_COMMITTED_HEAD", name
    iso = json.loads((NEW / "V77_REALIZATION_ISOLATION_RECEIPT_V2.json").read_text(encoding="utf-8"))
    assert iso["evaluation_universe"]["n_genes"] == n_corrected


def test_committed_summary_and_rendering_are_reproduced_by_committed_code(tmp_path):
    rec = _rec()
    assert rec["code_sha256"] == S.sha(SCRIPT)
    fresh = json.loads(json.dumps(S.build(REPRO, tmp_path / "x.json")))
    assert {k: v for k, v in fresh.items() if k != "record_path"} == \
           {k: v for k, v in rec.items() if k != "record_path"}
    assert MD.read_text(encoding="utf-8") == S.markdown(rec)
