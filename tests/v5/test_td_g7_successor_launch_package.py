"""Launch package for the one-shot TD G7 successor run at 8d41fb98 (external audit PR #296, review 5486851355).

These tests check the committed authority records, the fail-closed launch checks and the launcher text. They never
run G7 or G6, and they never read real expression or count data. The real-file pre-marker path is exercised
separately, by the launcher in QUALIFY mode.
"""
from __future__ import annotations

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


def test_records_pass_the_code_consumed_owner_and_authorization_parsers():
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


def test_launcher_order_puts_every_check_and_the_qualify_exit_before_g7():
    lines = _code_lines()
    def first(pattern: str) -> int:
        return next(i for i, ln in enumerate(lines) if re.search(pattern, ln))
    g7 = first(r'^CMD=\(')
    assert first(r'pin "\$G7AUTH" "\$EXPECTED_OP_SHA"') < g7
    assert first(r'"\$CHECKS" authority') < g7
    assert first(r'"\$CHECKS" prestart') < g7
    assert first(r'QUALIFY_PASS__STOPPED_BEFORE_G7') < first(r'^\s*exit 0$') < g7
    assert first(r'git -C "\$LAUNCH_ROOT" rev-parse HEAD') < first(r'worktree add --detach "\$EXEC" "\$IMPL"') < g7
    assert first(r'for d in "\$AUTH" "\$REC" "\$P" "\$EXEC"') < first(r'mkdir -p "\$AUTH" "\$REC" "\$P"')


def test_launcher_qualify_mode_never_uses_the_execute_paths():
    text = LAUNCHER.read_text(encoding="utf-8")
    qualify = re.search(r"QUALIFY\)(.*?);;", text, re.S).group(1)
    assert "launch_qualification_g7_" in qualify and "launchqual" in qualify
    assert "authority_g7_$TAG" not in qualify and "run_record_g7_$TAG" not in qualify and "G7_OUT" not in qualify
