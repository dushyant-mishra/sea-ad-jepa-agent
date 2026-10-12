"""Launch package for the one-shot TD G7 successor run at 8d41fb98 (external audit PR #296, review 5486851355).

These tests check the committed authority records, the fail-closed launch checks and the launcher text. They never
run G7 or G6, and they never read real expression or count data. The real-file pre-marker path is exercised
separately, by the launcher in QUALIFY mode.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKS_PATH = ROOT / "scripts" / "v5" / "td_g7_successor_launch_checks.py"
LAUNCHER = ROOT / "scripts" / "v5" / "run_td_g7_successor_once.sh"
AUTH = ROOT / "custody" / "owner_decisions" / "20261012"
OWNER = AUTH / "TD_G6G7_OWNER_DECISION_8d41fb98.json"
RUNTIME = AUTH / "TD_G6G7_RUNTIME_AUTHORIZATION_8d41fb98.json"
OPERATIONAL = AUTH / "TD_G7_OPERATIONAL_AUTHORIZATION_8d41fb98.json"
OLD_FIXTURES = ROOT / "tests" / "v5" / "fixtures" / "td_g7_successor"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = _load(CHECKS_PATH, "td_g7_successor_launch_checks_under_test")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rec(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def write(path: Path, payload: dict) -> Path:
    path.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return path


def validate(owner=OWNER, runtime=RUNTIME, operational=OPERATIONAL, expected=None, launcher=LAUNCHER):
    return C.validate_authority(owner, runtime, operational, expected_operational_sha=expected or sha(operational),
                                launcher=launcher, checks=CHECKS_PATH)


# ---------------------------------------------------------------------------------------- the committed records
def test_committed_records_pass_every_launch_check():
    out = validate()
    assert out["owner_decision"] == sha(OWNER) and out["operational_authorization"] == sha(OPERATIONAL)


def test_code_identity_constants_are_the_qualified_successor_at_8d41fb98():
    common = _load(ROOT / C.CODE_IDENTITY["common_entrypoint"], "common_for_identity")
    for key, rel in (("common_script_sha256", C.CODE_IDENTITY["common_entrypoint"]),
                     ("g6_script_sha256", C.CODE_IDENTITY["g6_entrypoint"]),
                     ("g7_script_sha256", C.CODE_IDENTITY["g7_entrypoint"])):
        blob = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{C.IMPLEMENTATION_COMMIT}:{rel}"])
        assert hashlib.sha256(blob.replace(b"\r\n", b"\n")).hexdigest() == C.CODE_IDENTITY[key], rel
        assert common.canonical_text_sha256(ROOT / rel) == C.CODE_IDENTITY[key], rel   # this tree carries the same code
    assert C.CODE_IDENTITY["g7_script_sha256"] == "275dad00c6bd37ef11a34a376c703b4433ed40eae8d087c4d8f9535f88170412"


def test_owner_record_passes_the_code_consumed_owner_parser():
    """The runtime-authorization parser needs the real PR #259 bytes and a clean HEAD at 8d41fb98; QUALIFY runs it."""
    common = _load(ROOT / C.CODE_IDENTITY["common_entrypoint"], "common_for_parsers")
    decision, physical = common.load_owner_decision(OWNER, implementation_commit_sha=C.IMPLEMENTATION_COMMIT)
    assert physical == sha(OWNER) and decision["g6_execution_authorized"] is False
    with pytest.raises(RuntimeError, match="qualified implementation commit"):
        common.load_owner_decision(OWNER, implementation_commit_sha="ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0")


# ------------------------------------------------------------------------------------------- R1 scope lock
@pytest.mark.parametrize("which", ["owner", "runtime", "operational"])
@pytest.mark.parametrize("change", ["missing", "true", "string_false"])
def test_r1_requires_an_explicit_boolean_g6_execution_false_in_every_record(which, change):
    validator = {"owner": lambda r: C.validate_owner_decision(r),
                 "runtime": lambda r: C.validate_runtime_authorization(r, sha(OWNER)),
                 "operational": lambda r: C.validate_operational_authorization(
                     r, owner_sha=sha(OWNER), runtime_sha=sha(RUNTIME), launcher_sha=sha(LAUNCHER),
                     checks_sha=sha(CHECKS_PATH))}[which]
    r = rec({"owner": OWNER, "runtime": RUNTIME, "operational": OPERATIONAL}[which])
    validator(copy.deepcopy(r))                                       # the committed record passes
    if change == "missing":
        r.pop("g6_execution_authorized")
    else:
        r["g6_execution_authorized"] = True if change == "true" else "false"
    with pytest.raises(SystemExit, match="R1 scope lock"):
        validator(r)


@pytest.mark.parametrize("key,value", [("g7_entrypoint_only", False), ("g6_rerun_permitted", True),
                                       ("training_authorized", True), ("td60_authorized", True),
                                       ("corrected_biological_replay_authorized", True), ("stage4_authorized", True),
                                       ("g6_reread_authorized", True)])
def test_operational_authorization_is_g7_only(key, value):
    r = rec(OPERATIONAL)
    r[key] = value
    with pytest.raises(SystemExit):
        C.validate_operational_authorization(r, owner_sha=sha(OWNER), runtime_sha=sha(RUNTIME),
                                             launcher_sha=sha(LAUNCHER), checks_sha=sha(CHECKS_PATH))


# ------------------------------------------------------------------------------------------------ bindings
@pytest.mark.parametrize("key,value", [("implementation_commit_sha", "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0"),
                                       ("g7_script_sha256", "f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe"),
                                       ("common_script_sha256", "0" * 64), ("g6_script_sha256", "0" * 64),
                                       ("g7_entrypoint", "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py")])
def test_runtime_and_operational_records_bind_the_exact_successor_code(key, value):
    rt, op = rec(RUNTIME), rec(OPERATIONAL)
    rt[key] = op[key] = value
    with pytest.raises(SystemExit, match=key):
        C.validate_runtime_authorization(rt, sha(OWNER))
    with pytest.raises(SystemExit, match=key):
        C.validate_operational_authorization(op, owner_sha=sha(OWNER), runtime_sha=sha(RUNTIME),
                                             launcher_sha=sha(LAUNCHER), checks_sha=sha(CHECKS_PATH))


def test_owner_decision_must_qualify_8d41fb98():
    r = rec(OWNER)
    r["qualified_implementation_commit_sha"] = "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0"
    with pytest.raises(SystemExit, match="qualified_implementation_commit_sha"):
        C.validate_owner_decision(r)


@pytest.mark.parametrize("key", ["g6_external_acceptance_sha256", "g6_artifact_sha256", "g6_producer_commit_sha",
                                 "g6_receipt_path", "fresh_g7_output_namespace", "prestart_requirements"])
def test_operational_authorization_pins_the_accepted_g6_and_the_fresh_namespace(key):
    r = rec(OPERATIONAL)
    r[key] = "tampered"
    with pytest.raises(SystemExit, match=key):
        C.validate_operational_authorization(r, owner_sha=sha(OWNER), runtime_sha=sha(RUNTIME),
                                             launcher_sha=sha(LAUNCHER), checks_sha=sha(CHECKS_PATH))


def test_audited_operational_sha_is_required(tmp_path):
    with pytest.raises(SystemExit, match="not the audited"):
        validate(expected="0" * 64)


def test_owner_and_runtime_shas_are_cross_bound(tmp_path):
    owner = write(tmp_path / "owner.json", {**rec(OWNER), "date": "2026-10-13"})   # a different, otherwise-valid decision
    with pytest.raises(SystemExit, match="owner_decision_sha256"):
        validate(owner=owner)


def test_launcher_and_checks_are_pinned_by_the_operational_authorization(tmp_path):
    launcher = tmp_path / "launcher.sh"
    launcher.write_bytes(LAUNCHER.read_bytes() + b"\n# edited\n")
    with pytest.raises(SystemExit, match="launcher_sha256"):
        validate(launcher=launcher)


def test_spent_ff4a21f9_authority_cannot_be_reused(tmp_path):
    with pytest.raises(SystemExit, match="spent ff4a21f9 authority"):
        validate(owner=OLD_FIXTURES / "TD_G6G7_OWNER_DECISION_ff4a21f9.json")
    with pytest.raises(SystemExit, match="spent ff4a21f9 authority"):
        validate(runtime=OLD_FIXTURES / "TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json")


# ------------------------------------------------------------------------------------------- launcher text
def _code_lines() -> list[str]:
    return [ln for ln in LAUNCHER.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def _bash() -> str:
    """Git Bash on Windows (a bare 'bash' there can resolve to WSL, which cannot see this path)."""
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    return str(git_bash) if git_bash.is_file() else "bash"


def test_launcher_is_valid_bash():
    subprocess.run([_bash(), "-n", str(LAUNCHER)], check=True)


def test_launcher_invokes_only_the_g7_entrypoint_and_never_g6():
    text = "\n".join(_code_lines())
    assert "materialize_td_relational_corrected_sampleA_v2" not in text
    entrypoints = set(re.findall(r"scripts/v5/([A-Za-z0-9_]+\.py)", text))
    assert entrypoints == {"audit_td_relational_g7_s174_overlap_v2.py", "td_g7_successor_launch_checks.py"}
    assert len(re.findall(r'CMD=\("\$PY" "\$EXEC/scripts/v5/audit_td_relational_g7_s174_overlap_v2\.py"', text)) == 1
    executed = [ln for ln in _code_lines() if ln.strip().startswith('"${CMD[@]}"')]
    assert len(executed) == 1                                       # the only execution; the printf merely records it


def test_launcher_text_orders_every_check_and_the_qualify_exit_before_g7():
    """Text order only; the control flow itself is exercised by the QUALIFY run."""
    lines = _code_lines()
    def first(pattern: str) -> int:
        return next(i for i, ln in enumerate(lines) if re.search(pattern, ln))
    g7 = first(r'^CMD=\(')
    assert first(r'pin "\$G7AUTH" "\$EXPECTED_OP_SHA"') < g7
    assert first(r'"\$CHECKS" authority') < g7
    assert first(r'"\$CHECKS" prestart') < g7
    assert first(r'QUALIFY_PASS__STOPPED_BEFORE_G7') < first(r'^\s*exit 0$') < g7
    assert first(r'git -C "\$LAUNCH_ROOT" rev-parse HEAD') < first(r'worktree add --detach "\$EXEC" "\$IMPL"') < g7
    assert first(r'for d in "\$ROOTDIR" "\$EXEC"') < first(r'mkdir -p "\$AUTH" "\$REC" "\$P"')


def test_launcher_path_arms_are_timestamped_and_disjoint():
    """Case-arm text only; the QUALIFY filesystem evidence is the real proof."""
    text = LAUNCHER.read_text(encoding="utf-8")
    arms = dict(re.findall(r"^\s*(QUALIFY|EXECUTE)\) (ROOTDIR=.*?);;", text, re.M))
    assert "launch_qualification_g7_${TAG}_$STAMP" in arms["QUALIFY"] and "launchqual_${TAG}_$STAMP" in arms["QUALIFY"]
    assert "launch_execute_g7_${TAG}_$STAMP" in arms["EXECUTE"] and "exec_${TAG}_$STAMP" in arms["EXECUTE"]
    assert "G7_OUT" not in arms["QUALIFY"] + arms["EXECUTE"]


def test_launcher_runs_pure_checks_before_any_filesystem_change():
    lines = _code_lines()

    def first(pattern: str) -> int:
        return next(i for i, ln in enumerate(lines) if re.search(pattern, ln))
    mk = first(r'mkdir -p "\$AUTH" "\$REC" "\$P"')
    for pattern in (r'rev-parse HEAD\)" = "\$AUTH_COMMIT"', r'status --porcelain --ignored\)" \] \|\| fail',
                    r'cat-file blob "\$AUTH_COMMIT:\$OPERATIONAL_REL"', r'cat-file blob "\$ACC_COMMIT:\$ACCEPTANCE_REL"',
                    r'G7 output namespace already exists', r'Python environment is not the qualified one'):
        assert first(pattern) < mk, pattern
    assert "STOP_CODE=64" in "\n".join(lines)


def test_launcher_repins_every_consumed_file_after_prestart_and_gates_execute_on_the_acceptance():
    lines = _code_lines()

    def idx(pattern: str) -> list:
        return [i for i, ln in enumerate(lines) if re.search(pattern, ln)]
    g7 = idx(r'^CMD=\(')[0]
    prestart = idx(r'"\$CHECKS" prestart')[0]
    assert any(prestart < i < g7 for i in idx(r'^pin_consumed$'))
    assert any(prestart < i < g7 for i in idx(r'^pin_g6$'))
    assert idx(r'"\$CHECKS" acceptance')[0] < prestart
    assert idx(r"^trap '")[0] < idx(r'^"\$\{CMD\[@\]\}"')[0]
    body = LAUNCHER.read_text(encoding="utf-8").split("pin_consumed() {")[1].split("\n}")[0]
    for needle in ('"$DEC" "$DEC_SHA"', '"$AUZ" "$AUZ_SHA"', '"$G7AUTH" "$EXPECTED_OP_SHA"', "PREFLIGHT_RESULT.json",
                   "TD_RELATIONAL_MAPPING_PREFLIGHT.json", "REPLAY_9216_MANIFEST.csv", "S174_REBUILD_FREEZE_V1.json",
                   '"$FREEZE"', '"$PROVENANCE"', '"$COLLISION"', "89932183"):
        assert needle in body, needle


# ------------------------------------------------------------------------------- launch-audit acceptance (EXECUTE)
def _acceptance(tmp_path, **changes) -> Path:
    base = {"schema": C.LAUNCH_ACCEPTANCE_SCHEMA, "disposition": C.LAUNCH_ACCEPTANCE_DISPOSITION,
            "implementation_commit_sha": C.IMPLEMENTATION_COMMIT, "authority_commit_sha": "c" * 40,
            "operational_authorization_sha256": sha(OPERATIONAL), "launcher_sha256": sha(LAUNCHER),
            "launch_checks_sha256": sha(CHECKS_PATH), "fresh_g7_output_namespace": C.G7_OUTPUT_NAMESPACE,
            "single_g7_attempt": True, "g6_execution_authorized": False, "corrected_biological_replay_authorized": False,
            "stage4_authorized": False, **{k: False for k in C.FALSE_FLAGS}}
    base.update(changes)
    return write(tmp_path / "acceptance.json", {k: v for k, v in base.items() if v is not None})


def _check_acceptance(path: Path, expected=None, commit="c" * 40):
    return C.validate_launch_acceptance(path, expected_sha=expected or sha(path), authority_commit=commit,
                                        operational=OPERATIONAL, launcher=LAUNCHER, checks=CHECKS_PATH)


def test_a_launch_acceptance_binding_this_exact_package_releases_execute(tmp_path):
    assert _check_acceptance(_acceptance(tmp_path))["launch_acceptance_check"] == "PASS"


@pytest.mark.parametrize("changes", [{"disposition": "REJECT"}, {"authority_commit_sha": "d" * 40},
                                     {"operational_authorization_sha256": "0" * 64}, {"launcher_sha256": "0" * 64},
                                     {"launch_checks_sha256": "0" * 64}, {"implementation_commit_sha": "f" * 40},
                                     {"single_g7_attempt": False}, {"g6_execution_authorized": None},
                                     {"g6_execution_authorized": True}, {"training_authorized": True},
                                     {"td60_authorized": True}, {"g6_rerun_authorized": True},
                                     {"fresh_g7_output_namespace": "D:/elsewhere"}])
def test_launch_acceptance_must_bind_the_exact_package_and_stay_g7_only(tmp_path, changes):
    with pytest.raises(SystemExit):
        _check_acceptance(_acceptance(tmp_path, **changes))


def test_launch_acceptance_sha_is_required(tmp_path):
    with pytest.raises(SystemExit, match="launch-audit acceptance SHA"):
        _check_acceptance(_acceptance(tmp_path), expected="0" * 64)


# ------------------------------------------------------------------------------------- R2 prestart stop branches
STUB_G7 = '''
import json
from pathlib import Path
import pandas as pd
CFG = json.loads((Path(__file__).parent / "stub_config.json").read_text())
def bind_execution(args):
    return {}, None, None, Path("g6.py"), Path(__file__)
def expected_authority_trace(args, auth, g6, g7):
    return dict(CFG["trace"])
def require_g6_producer_code_continuity(trace):
    return None
def load_inputs(args):
    sample = pd.DataFrame(CFG["sample_a"])
    prov = pd.DataFrame(CFG["provenance"])
    replay = pd.DataFrame({"molecular_address_index": [3]})
    return replay, sample, prov, None, {"matrices": CFG["matrices"]}
def load_accepted_g6_predecessor(receipt, acceptance, *, replay_addresses, sample_a):
    return {"g7_verified_g6_execution_sha256": {"receipt": CFG["g6_receipt"]}}
def load_g1b_authority_from_pass_commit(anchor):
    return {}, {"rebuilt_cache": {"shards": CFG["shards"]}}, "r", "f"
def verify_cache_hashes(cache, freeze):
    return CFG["verified"], {}
def load_s174_cell_index(meta_path, expected):
    cells = CFG["cells"].get(Path(meta_path).name, ["c1", "c2"])
    return cells, {c: i for i, c in enumerate(cells)}, expected
'''


def _prestart_world(tmp_path, monkeypatch, **override):
    """Two HVS/SEA matrices joined to two shards, with sources present at their frozen sizes."""
    monkeypatch.setattr(C, "N_S174_SHARDS", 2)
    monkeypatch.setattr(C, "N_HVS_SEA_MATRICES", 2)
    exec_root = tmp_path / "exec"
    g7 = exec_root / C.CODE_IDENTITY["g7_entrypoint"]
    g7.parent.mkdir(parents=True)
    g7.write_text(STUB_G7, encoding="utf-8")
    cache, src = tmp_path / "cache", tmp_path / "src"
    cache.mkdir()
    src.mkdir()
    for stem in ("s1", "s2"):
        (cache / f"{stem}.meta.npz").write_bytes(b"m")
        (cache / f"{stem}.counts.npz").write_bytes(b"c")
    for name in ("m1.h5ad", "m2.h5ad"):
        (src / name).write_bytes(b"12345")
    cfg = {"trace": dict(C.CODE_IDENTITY), "g6_receipt": C.G6_ARTIFACTS["G6_RECEIPT.json"],
           "sample_a": {"source": ["HVS", "SEA_AD", "NPH52"], "matrix_id": ["m1", "m2", "n1"]},
           "provenance": {"source_dataset_id": ["HVS_COMMON", "SEA_AD_COMMON"], "source_exact_ensembl_id": ["E1", "E1"]},
           "matrices": [{"matrix_id": "m1", "stem": "s1", "source": {"path": "m1.h5ad", "bytes": 5}},
                        {"matrix_id": "m2", "stem": "s2", "source": {"path": "m2.h5ad", "bytes": 5}}],
           "shards": {"s1": {"meta": "a"}, "s2": {"meta": "b"}}, "verified": 2, "cells": {}}
    for key, value in override.items():
        cfg[key] = value(cfg) if callable(value) else value
    (g7.parent / "stub_config.json").write_text(json.dumps(cfg), encoding="utf-8")
    args = argparse.Namespace(g6_receipt="r", g6_acceptance="a", s174_cache_root=str(cache), source_root=str(src))
    return exec_root, args


def test_prestart_passes_on_a_complete_join(tmp_path, monkeypatch):
    out = C.prestart(*_prestart_world(tmp_path, monkeypatch))
    assert (out["r2_prestart_replay"], out["s174_verified_shards"], out["hvs_sea_matrices_joined"]) == ("PASS", 2, 2)
    assert out["g7_marker_created"] is False


def _drop_matrix(cfg):
    return [m for m in cfg["matrices"] if m["matrix_id"] != "m2"]


def _resize(cfg):
    return [dict(m, source=dict(m["source"], bytes=6)) if m["matrix_id"] == "m1" else m for m in cfg["matrices"]]


def _restem(cfg):
    return [dict(m, stem="s9") if m["matrix_id"] == "m2" else m for m in cfg["matrices"]]


@pytest.mark.parametrize("override,message", [
    ({"trace": lambda cfg: dict(cfg["trace"], g7_script_sha256="0" * 64)}, "not the qualified successor"),
    ({"g6_receipt": "0" * 64}, "accepted G6 receipt"),
    ({"verified": 1}, "S174 shard count"),
    ({"shards": {"s1": {"meta": "a"}}}, "S174 shard count"),
    ({"matrices": _drop_matrix}, "matrix absent from Macha freeze"),
    ({"matrices": _restem, "shards": {"s1": {"meta": "a"}, "s9x": {"meta": "b"}}}, "absent from G1b authority"),
    ({"cells": {"s1.meta.npz": ["c1", "c1"]}}, "duplicate S174 cell_id"),
    ({"matrices": _resize}, "missing or resized"),
    ({"provenance": {"source_dataset_id": ["HVS_COMMON", "HVS_COMMON", "SEA_AD_COMMON"],
                     "source_exact_ensembl_id": ["E1", "E1", "E2"]}}, "provenance identifiers"),
    ({"sample_a": {"source": ["HVS", "NPH52"], "matrix_id": ["m1", "n1"]}}, "HVS/SEA matrix coverage"),
])
def test_prestart_stops_on_every_r2_failure(tmp_path, monkeypatch, override, message):
    exec_root, args = _prestart_world(tmp_path, monkeypatch, **override)
    with pytest.raises(SystemExit, match=message):
        C.prestart(exec_root, args)


def test_prestart_stops_when_a_counts_shard_is_missing(tmp_path, monkeypatch):
    exec_root, args = _prestart_world(tmp_path, monkeypatch)
    (Path(args.s174_cache_root) / "s2.counts.npz").unlink()
    with pytest.raises(SystemExit, match="counts shard missing"):
        C.prestart(exec_root, args)
