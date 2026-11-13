#!/usr/bin/env python3
"""Fail-closed non-stepping pytest inventories for three original V5 CI lanes.

Never expand a filename wildcard into an executable test suite. Candidate
matching patterns are used ONLY to detect unreviewed additions and refuse
collection. Every test filename executed must be explicitly reviewed here.
NO optimizer/backward/EMA is invoked by this verifier.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha1
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
NO_TRAINING_TEST_INVENTORY = {
    "full": (
        "tests/test_jepa_v5_dev2048_pilot_preflight_v1_macha.py",
        "tests/test_jepa_v5_full_state_readonly_audit_v1.py",
        "tests/test_jepa_v5_full_state_readonly_audit_v1_teacher_macha_red.py",
        "tests/test_jepa_v5_journal_integration_macha_v1.py",
        "tests/test_jepa_v5_live_model_u0_journal_connector_v1.py",
        "tests/test_jepa_v5_live_model_u0_journal_connector_v1_macha_review_red.py",
        "tests/test_jepa_v5_pipeline_identity_contract_v1_macha.py",
        "tests/test_jepa_v5_pipeline_identity_contract_v1_macha_teacher_inputs.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1_macha_584_closure.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1_macha_584_review_controls.py",
        "tests/test_jepa_v5_source_data_custody_gate_v1_macha_584_review_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_controls.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_structure_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_sol_optimizer_identity_red.py",
        "tests/test_jepa_synth2048_atomic_checkpoint_bytes_v1.py",
        "tests/test_jepa_synth2048_attempt_journal_v2.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_fork_writer_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_incremental_io_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_sol_reconcile_review_red.py",
        "tests/test_jepa_synth2048_checkpoint_capture_prefreeze_v1.py",
        "tests/test_jepa_synth2048_checkpoint_failed_attempt_macha_red.py",
        "tests/test_jepa_synth2048_collapse_sentinel_v1.py",
        "tests/test_jepa_synth2048_collapse_state_after_step_successor_v2.py",
        "tests/test_jepa_synth2048_collapse_state_vs_attempt_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_atomic_journal_v1.py",
        "tests/test_jepa_synth2048_failed_onset_cause_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_cause_successor_v1.py",
        "tests/test_jepa_synth2048_failed_onset_journal_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_repair_sol_v1.py",
        "tests/test_jepa_synth2048_forensic_prefix_e2_successor_v1.py",
        "tests/test_jepa_synth2048_last_healthy_recoverability_macha_red.py",
        "tests/test_jepa_synth2048_typed_onset_disk_integration_v2.py",
        "tests/test_jepa_synth2048_v5_readiness.py",
        "tests/test_jepa_synth2048_write_intent_e1_scoped_v1.py",
    ),
    "integration": (
        "tests/test_jepa_synth2048_atomic_checkpoint_bytes_v1.py",
        "tests/test_jepa_synth2048_attempt_journal_v2.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_fork_writer_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_incremental_io_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_sol_reconcile_review_red.py",
        "tests/test_jepa_synth2048_checkpoint_capture_prefreeze_v1.py",
        "tests/test_jepa_synth2048_checkpoint_failed_attempt_macha_red.py",
        "tests/test_jepa_synth2048_collapse_sentinel_v1.py",
        "tests/test_jepa_synth2048_collapse_state_after_step_successor_v2.py",
        "tests/test_jepa_synth2048_collapse_state_vs_attempt_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_atomic_journal_v1.py",
        "tests/test_jepa_synth2048_failed_onset_cause_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_cause_successor_v1.py",
        "tests/test_jepa_synth2048_failed_onset_journal_macha_red.py",
        "tests/test_jepa_synth2048_failed_onset_repair_sol_v1.py",
        "tests/test_jepa_synth2048_forensic_prefix_e2_successor_v1.py",
        "tests/test_jepa_synth2048_last_healthy_recoverability_macha_red.py",
        "tests/test_jepa_synth2048_typed_onset_disk_integration_v2.py",
        "tests/test_jepa_synth2048_v5_readiness.py",
        "tests/test_jepa_synth2048_write_intent_e1_scoped_v1.py",
        "tests/test_jepa_v5_full_state_readonly_audit_v1.py",
        "tests/test_jepa_v5_full_state_readonly_audit_v1_teacher_macha_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_controls.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_583_review_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_macha_structure_red.py",
        "tests/test_jepa_v5_structured_journal_preflight_v1_sol_optimizer_identity_red.py",
    ),
    "thread": (
        "tests/test_jepa_synth2048_attempt_journal_v2.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_fork_writer_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_incremental_io_sol_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_579_review_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_controls.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_macha_red.py",
        "tests/test_jepa_synth2048_attempt_journal_v2_sol_reconcile_review_red.py",
    ),
}
INVENTORY_SCOPES = {
    "full": ("test_jepa_v5_*.py", "test_jepa_synth2048_*.py"),
    "integration": (
        "test_jepa_synth2048_*.py",
        "test_jepa_v5_full_state_readonly_audit_v1*.py",
        "test_jepa_v5_structured_journal_preflight_v1*.py",
    ),
    "thread": ("test_jepa_synth2048_attempt_journal_v2*.py",),
}
# Direct optimizer, backward, autograd and EMA entrypoints are forbidden.
# This is a deliberately conservative static gate, not an authorization for
# neural execution or a claim to secure arbitrary transitive import effects.
FORBIDDEN_CALL_NAMES = frozenset({
    "step", "backward", "zero_grad", "run_ema", "update_ema", "apply_ema",
    "ema_update", "run_guarded_inactive_reference_update",
    "run_inactive_reference_update", "optimizer_step", "run_training",
    "fit_model", "train_model", "pytest_main",
})


def _refuse(message: str) -> None:
    raise RuntimeError("REFUSE_UNSAFE_NO_TRAINING_TEST_INVENTORY__" + message)


# Macha review of #592: a modified approved test could alias a step without
# a direct ``x.step()`` call (``s = opt.step; s()``, ``getattr(opt, "step")()``,
# ``methodcaller("step")``, ``from torch.autograd import grad``). None of the
# 40 approved files reads these attributes, so refusing them costs nothing.
# Calls into project helpers that step internally remain out of scope: this
# gate prevents accidental collection, it is not a transitive attestation.
ALIASABLE_MUTATORS = frozenset({"step", "backward", "zero_grad"})


def _check_references(tree: ast.AST, filename: str) -> None:
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and node.attr in ALIASABLE_MUTATORS
                and isinstance(node.ctx, ast.Load)):
            _refuse(f"FORBIDDEN_REFERENCE:{filename}:{node.lineno}:{node.attr}")
        if (isinstance(node, ast.Call)
                and getattr(node.func, "id", getattr(node.func, "attr", None))
                in ("getattr", "methodcaller", "attrgetter")
                and any(isinstance(a, ast.Constant)
                        and a.value in FORBIDDEN_CALL_NAMES | {"grad"}
                        for a in node.args)):
            _refuse(f"FORBIDDEN_DYNAMIC_LOOKUP:{filename}:{node.lineno}")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = {alias.name.rsplit(".", 1)[-1] for alias in node.names}
            module = getattr(node, "module", None) or ""
            if names & FORBIDDEN_CALL_NAMES or (
                    module.startswith("torch") and names & {"grad", "backward"}):
                _refuse(f"FORBIDDEN_IMPORT:{filename}:{node.lineno}")


def _check_ast(source: str, filename: str) -> None:
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name) else None)
        if name in FORBIDDEN_CALL_NAMES or (
                isinstance(func, ast.Name) and name in ("eval", "exec", "compile")):
            # Builtin eval() is dynamic execution, but nn.Module.eval()
            # merely switches frozen teacher evaluation mode at U0.
            _refuse(f"FORBIDDEN_CALL:{filename}:{node.lineno}:{name}")
        if (name == "grad" and isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "autograd"):
            _refuse(f"FORBIDDEN_AUTOGRAD:{filename}:{node.lineno}")
        if (name == "main" and isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in ("pytest", "unittest")):
            _refuse(f"FORBIDDEN_DYNAMIC_TEST_DISCOVERY:{filename}:{node.lineno}")
    # Direct calls keep their original reasons; aliases are refused after.
    _check_references(tree, filename)


PYTEST_CONFIG_SECTIONS = {
    "pytest.ini": "[pytest]", ".pytest.ini": "[pytest]", "tox.ini": "[pytest]",
    "setup.cfg": "[tool:pytest]", "pyproject.toml": "[tool.pytest",
}


def _refuse_implicit_collection_inputs(repo_root: Path) -> None:
    """Macha review of #592: pytest also runs conftest.py files and ini
    ``addopts``/plugins that no explicit argv lists. Refuse both.
    Macha review of #595: include hidden ``.pytest.ini`` and config files in
    tests/, which pytest finds first when the explicit paths live there."""
    for directory in (repo_root, repo_root / "tests"):
        if (directory / "conftest.py").exists():
            _refuse("IMPLICIT_CONFTEST_NOT_REVIEWED:" +
                    (directory / "conftest.py").relative_to(repo_root).as_posix())
        for name, marker in PYTEST_CONFIG_SECTIONS.items():
            path = directory / name
            if path.is_file() and (name.endswith("pytest.ini") or
                                   marker in path.read_text(encoding="utf-8")):
                _refuse("IMPLICIT_PYTEST_CONFIG_NOT_REVIEWED:" +
                        path.relative_to(repo_root).as_posix())


# Preserve exactly the archived D1 CI definition as historical evidence.
# Its old branch/manual route must NOT be dispatched without separate approval.
# Other workflows (including push/main and pull_request/main) are examined,
# regardless of whether they contain a branches: filter.
LEGACY_HISTORICAL_WORKFLOW_BLOBS = {
    "d1-independent-closure-ci.yml": "a0e3fb2622992630ce705467bfcb3aad7aa1001e",
}


def _exact_unchanged_legacy_workflow(workflow: Path, raw: bytes) -> bool:
    expected = LEGACY_HISTORICAL_WORKFLOW_BLOBS.get(workflow.name)
    return (expected is not None
            and sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0"
                     + raw).hexdigest() == expected)


# Macha review of #595: refusing known-bad argv shapes missed `pytest -q`,
# `pytest .`, `pytest tests/v5` and `--pyargs`, each of which collects whole
# directories. Every pytest invocation must instead name explicit test files.
_PYTEST_CALL = re.compile(r"(?:^|[\s;&|(])(?:python3?\s+-m\s+pytest|py\.test|pytest)(?=\s|$)")
_VALUE_OPTIONS = frozenset({
    "-k", "-m", "-p", "-c", "-o", "-r", "-W", "--rootdir", "--basetemp",
    "--config-file", "--confcutdir", "--deselect", "--ignore", "--junitxml",
    "--tb", "--maxfail", "--durations", "--import-mode", "--log-level"})
_EXPLICIT_TEST = re.compile(r"tests/[A-Za-z0-9_./-]+\.py(?:::[A-Za-z0-9_\[\].-]+)*")


def _logical_run_lines(jobs: str) -> list[str]:
    """Each shell line of every ``run:`` step; backslash continuations joined."""
    lines, out, i = jobs.splitlines(), [], 0
    while i < len(lines):
        found = re.match(r"^(\s*)(?:-\s+)?run:\s*(.*)$", lines[i])
        i += 1
        if not found:
            continue
        indent, value = len(found.group(1)), found.group(2).strip()
        block = [value]
        if value[:1] in ("|", ">"):
            block = []
            while i < len(lines) and (not lines[i].strip() or
                                      len(lines[i]) - len(lines[i].lstrip()) > indent):
                block.append(lines[i].strip())
                i += 1
        if value[:1] == ">":  # YAML folded block: one shell line per paragraph
            block = " ".join(line if line else "\n" for line in block).split("\n")
        current = ""
        for line in block:
            line = line.strip()
            if line.endswith("\\"):
                current += line[:-1] + " "
                continue
            out.append(current + line)
            current = ""
        if current:
            out.append(current)
    return [line for line in out if line.strip()]


def _require_explicit_pytest_argv(line: str, workflow: str) -> None:
    for segment in re.split(r"\s*(?:;|&&|\|\||\||>)\s*", line):
        if re.search(r"\bpip3?\s+install\b", segment):
            continue  # installing the pytest package is not a test route
        call = _PYTEST_CALL.search(segment)
        if call is None:
            continue
        tokens, paths, skip = segment[call.end():].split(), [], False
        for token in tokens:
            if skip:
                skip = False
                continue
            if token in _VALUE_OPTIONS:
                skip = True
            elif token == "--pyargs":
                _refuse("PACKAGE_COLLECTION_PYTEST_ROUTE:" + workflow)
            elif not token.startswith("-"):
                paths.append(token)
        if not paths or any(_EXPLICIT_TEST.fullmatch(p) is None or
                            re.search(r"[*?\[]", p.split("::")[0]) for p in paths):
            _refuse("WILDCARD_OR_DIRECTORY_PYTEST_ROUTE:" + workflow)


def verify_no_wildcard_pytest_routes(repo_root: Path = ROOT) -> list[str]:
    """No automatically triggered workflow may let pytest collect anything
    but explicitly named test files: no glob, directory, package, bare
    invocation or shell expansion. Only the byte-identical archived D1
    workflow is reported instead of examined (and must not be dispatched)."""
    scoped = []
    for workflow in sorted((repo_root / ".github/workflows").glob("*.y*ml")):
        raw = workflow.read_bytes()
        if _exact_unchanged_legacy_workflow(workflow, raw):
            scoped.append(workflow.name)
            continue
        text = raw.decode("utf-8")
        _, _, jobs = text.partition("\njobs:")
        for line in _logical_run_lines(jobs):
            if re.search(r"unittest\s+discover", line):
                _refuse("DISCOVERY_TEST_ROUTE:" + workflow.name)
            if _PYTEST_CALL.search(line) and ("$(" in line or "`" in line):
                _refuse("WILDCARD_OR_DIRECTORY_PYTEST_ROUTE:" + workflow.name)
            _require_explicit_pytest_argv(line, workflow.name)
    return scoped


def verify_inventory(suite: str, repo_root: Path = ROOT) -> tuple[str, ...]:
    if suite not in NO_TRAINING_TEST_INVENTORY:
        _refuse("UNKNOWN_SUITE")
    _refuse_implicit_collection_inputs(repo_root)
    verify_no_wildcard_pytest_routes(repo_root)
    paths = NO_TRAINING_TEST_INVENTORY[suite]
    if not paths or len(paths) != len(set(paths)):
        _refuse("EMPTY_OR_DUPLICATED_ALLOWLIST")
    if not all(p.startswith("tests/") and p.endswith(".py")
               and not Path(p).is_absolute()
               and ".." not in Path(p).parts for p in paths):
        _refuse("UNSAFE_EXPLICIT_PATH")
    # Globs never become test execution arguments; they are detection-only.
    discovered = {
        p.relative_to(repo_root).as_posix()
        for pattern in INVENTORY_SCOPES[suite]
        for p in (repo_root / "tests").glob(pattern)
        if p.is_file()
    }
    expected = set(paths)
    if discovered != expected:
        _refuse("UNREVIEWED_TEST_FILE_ADDED_OR_MISSING:" +
                str(sorted(discovered ^ expected)))
    for name in paths:
        path = repo_root / name
        if not path.is_file() or path.is_symlink():
            _refuse("UNSAFE_TEST_FILE:" + name)
        _check_ast(path.read_text(encoding="utf-8"), name)
    print(f"NO_TRAINING_TEST_INVENTORY_VERIFIED:{suite}:{len(paths)}",
          flush=True)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=sorted(NO_TRAINING_TEST_INVENTORY),
                        required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--verify", action="store_true")
    action.add_argument("--pytest", action="store_true")
    args = parser.parse_args()
    paths = verify_inventory(args.suite)
    if args.verify:
        return 0
    # Fixed, reviewed argv only, and the complete static check just ran.
    # No shells and no test globs; pytest receives explicit path literals.
    # --noconftest and no plugin autoload: only the reviewed files run.
    # PYTEST_ADDOPTS injects extra test argv; PYTEST_PLUGINS explicitly loads
    # plugins even when automatic entrypoint discovery is disabled. Clear both.
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               PYTEST_ADDOPTS="", PYTEST_PLUGINS="")
    # Macha review of #595: pytest searches upward from the test paths for an
    # ini file, so a pytest.ini/.pytest.ini outside the reviewed tree could
    # still add tests. Pin an empty reviewed config and the rootdir.
    with tempfile.TemporaryDirectory() as reviewed:
        config = Path(reviewed) / "pytest.ini"
        config.write_text("[pytest]\n", encoding="ascii")
        subprocess.run([sys.executable, "-m", "pytest", "-q", "--noconftest",
                        "-c", str(config), "--rootdir", str(ROOT), *paths],
                       cwd=ROOT, check=True, env=env)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
