from pathlib import Path
import importlib.util


def test_v5_reference_loss_declares_mechanics_only_not_scientific_target_authority():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "src/sea_ad_jepa/v5/inactive_update_reference.py"
    spec = importlib.util.spec_from_file_location("v5_update_reference_semantics", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert getattr(module, "SCIENTIFIC_TARGET_SEMANTICS_AUTHORIZED", None) is False, (
        "the runtime mechanics harness does not explicitly disclaim scientific target authority"
    )
    assert getattr(module, "REFERENCE_LOSS_ROLE", None) == (
        "MECHANICS_FIXTURE_ONLY__NOT_TARGET_AUTHORITY"
    ), "deterministic teacher-block loss is not explicitly classified as mechanics-only"
    assert getattr(module, "FULL_RICH_TEACHER_REALIZATION_MATCHING_AUTHORIZED", None) is False, (
        "runtime must not imply that partial RNA can point-predict arbitrary teacher-private evidence"
    )
