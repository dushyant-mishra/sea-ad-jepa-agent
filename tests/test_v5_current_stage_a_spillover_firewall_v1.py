from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "src" / "sea_ad_jepa" / "v5"

# Current production-authority graph. Historical schemas may remain for provenance/tests,
# but they must not be labelled current or be reachable from this graph.
CURRENT_STAGE_A_SOURCE_PATHS = (
    "canonical_address_registry_authority_v1.py",
    "current_target_address_provider_authority_v1.py",
    "shared_address_query_provider_v1.py",
    "primary_representation_authority_v1.py",
    "support_estimability_authority_v1.py",
    "base_training_estimand_authority_v1.py",
    "base_training_estimand_recovery_v1.py",
    "target_evidence_budget_authority_v1.py",
    "precision_authority_v1.py",
    "outer_split_authority_v1.py",
    "target_panel_authority_v1.py",
    "address_universe_ladder_authority_v1.py",
    "masking_rng_replay_authority_v1.py",
    "masking_qualification_design_authority_v1.py",
    "masking_qualification_parameters_authority_v1.py",
    "masking_qualification_run_contract_v1.py",
    "masking_qualification_execution_authority_v2.py",
    "full104_masking_qualification_runner_v1.py",
    "full104_masking_streaming_executor_v1.py",
    "current_masking_policy_authority_v2.py",
    "target_construction_authority_v1.py",
    "remaining_rna_necessity_v1.py",
    "remaining_rna_execution_authority_v1.py",
    "teacher_target_semantics_authority_v2.py",
    "ema_presentation_v1.py",
    "ema_timescale_authority_v2.py",
    "measurement_robustness_authority_v2.py",
    "target_identity_shortcut_gate_authority_v1.py",
    "anti_cheat_authority_bundle_v2.py",
    "model_geometry_authority_v2.py",
    "geometry_memorization_qualification_authority_v1.py",
    "production_protected_registry_authority_v1.py",
    "critical_test_execution_authority_v1.py",
    "current_runtime_source_authority_v1.py",
    "current_authority_roots_v2.py",
    "current_authority_closure_v2.py",
    "current_trainer_preexecution_contract_v2.py",
    "current_teacher_target_receipt_v2.py",
    "current_training_authority_v1.py",
    "qualified_optimizer_guard_v3.py",
    "current_atomic_checkpoint_guard_v2.py",
)

# Historical/prototype/superseded helpers remain only for provenance and old regression
# fixtures. Any import from a current module into one of these is a fail-closed error.
QUARANTINED_V5_MODULES = frozenset(
    {
        "data_first_geometry",
        "inactive_update_reference",
        "keyed_dropout_prototype",
        "keyed_dropout_v2",
        "masking_authority_v1",
        "masking_qualification_execution_authority_v1",
        "proposal_horizon_v1",
        "proposal_policy_v1",
        "proposal_policy_v2",
        "target_address_query_authority_v1",
        "teacher_target_semantics_authority_v1",
        "teacher_student_data_first_v1",
        "teacher_student_integration_freeze",
        "teacher_student_integration_freeze_v2",
        "teacher_student_relational_v1",
        "unified_runtime_v1",
        "update_geometry_v3",
        "ema_timescale_authority_v1",
        "measurement_robustness_authority_v1",
        "anti_cheat_authority_bundle_v1",
        "model_geometry_authority_v1",
        "current_authority_roots_v1",
        "current_authority_closure_v1",
        "current_trainer_preexecution_contract_v1",
        "current_teacher_target_receipt_v1",
        "qualified_optimizer_guard_v2",
        "current_atomic_checkpoint_guard_v1",
    }
)

EAGER_SIDE_EFFECT_MODULES = (
    "sea_ad_jepa.v5.data_first_geometry",
    "sea_ad_jepa.v5.proposal_policy_v1",
)


_V5_PACKAGE = "sea_ad_jepa.v5"
_DYNAMIC_IMPORT_CALLS = frozenset({"import_module", "__import__"})


def _local_imports(path: Path) -> set[str]:
    """Return local-v5 module names reachable from explicit/dynamic imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module
            if module is None:
                if node.level > 0:
                    found.update(alias.name for alias in node.names)
            elif module == _V5_PACKAGE:
                found.update(alias.name for alias in node.names)
            elif module.startswith(_V5_PACKAGE + "."):
                found.add(module.rsplit(".", 1)[-1])
            elif node.level > 0:
                found.add(module.split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(_V5_PACKAGE + "."):
                    found.add(alias.name.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            if name in _DYNAMIC_IMPORT_CALLS and node.args:
                target = node.args[0]
                if isinstance(target, ast.Constant) and isinstance(target.value, str):
                    found.add(target.value.lstrip(".").rsplit(".", 1)[-1])
    return found


def _run_clean_python(script: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def test_current_stage_a_modules_do_not_import_quarantined_v5_modules() -> None:
    violations: dict[str, list[str]] = {}
    for filename in CURRENT_STAGE_A_SOURCE_PATHS:
        imports = _local_imports(V5 / filename)
        bad = sorted(imports & QUARANTINED_V5_MODULES)
        if bad:
            violations[filename] = bad
    assert violations == {}


def test_current_authority_import_does_not_eagerly_load_prospective_helpers() -> None:
    script = """
import sys
import sea_ad_jepa.v5.current_authority_roots_v2  # noqa: F401
for name in (
    'sea_ad_jepa.v5.data_first_geometry',
    'sea_ad_jepa.v5.proposal_policy_v1',
):
    if name in sys.modules:
        raise SystemExit(f'eager historical/prospective spillover: {name}')
"""
    result = _run_clean_python(script)
    assert result.returncode == 0, result.stdout


def test_compatibility_helpers_are_lazy_not_eager() -> None:
    script = """
import sys
import sea_ad_jepa.v5 as v5
assert 'sea_ad_jepa.v5.data_first_geometry' not in sys.modules
assert 'sea_ad_jepa.v5.proposal_policy_v1' not in sys.modules
assert v5.__all__ == []
_ = v5.PackedValidTokens
assert 'sea_ad_jepa.v5.data_first_geometry' in sys.modules
assert 'sea_ad_jepa.v5.proposal_policy_v1' not in sys.modules
_ = v5.DonorCapacity
assert 'sea_ad_jepa.v5.proposal_policy_v1' in sys.modules
"""
    result = _run_clean_python(script)
    assert result.returncode == 0, result.stdout
