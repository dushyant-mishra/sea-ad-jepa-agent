import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/v4/derive_contextual_target_f1_hc3_replication_frontier_v3.py"
spec = importlib.util.spec_from_file_location("replication_v3", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_frontier_contains_all_70_and_35_nph_free_rows():
    ids = mod.frontier_identities()
    assert len(ids) == 70
    assert len(set(ids)) == 70
    assert sum(r_nph == 0 for _, r_nph, _ in ids) == 35
    assert ids[0] == (0, 0, 0)
    assert ids[-1] == (6, 1, 4)


def test_svd_and_qr_leverage_agree_on_hand_full_rank_matrix():
    x = np.array([[1., 0.], [1., 1.], [1., 2.], [1., 4.]])
    svd = mod.svd_geometry(x)
    qr = mod.qr_geometry(x)
    assert svd["rank"] == qr["rank"] == 2
    assert np.max(np.abs(svd["leverage"] - qr["leverage"])) <= mod.tolerance(len(x))
    assert abs(np.sum(svd["leverage"]) - 2.) <= mod.tolerance(len(x))


def test_nonreplicated_row_is_classified_and_does_not_truncate_identities():
    reasons, admissible = mod.classify_geometry(
        full_column_rank=True,
        df=96,
        finite=True,
        loo_stable=False,
        hc3_estimable=False,
    )
    assert admissible is False
    assert reasons == ["NONREPLICATED_NUISANCE_DIRECTION", "HC3_LEVERAGE_BOUNDARY"]
    assert len(mod.frontier_identities()) == 70


def test_pass_reason_is_the_only_reason_for_admissible_geometry():
    reasons, admissible = mod.classify_geometry(True, 97, True, True, True)
    assert admissible is True
    assert reasons == ["PASS_DONOR_REPLICATED_HC3"]


def test_validator_positive_check_map_does_not_treat_audited_absence_as_failure():
    validator_path = SCRIPT.with_name("validate_contextual_target_f1_hc3_replication_frontier_v3.py")
    validator_spec = importlib.util.spec_from_file_location("replication_validator_v3", validator_path)
    validator = importlib.util.module_from_spec(validator_spec)
    validator_spec.loader.exec_module(validator)
    assert validator.all_checks_pass({"authenticated_inputs": True, "no_forbidden_data_access": True})


def test_finalizer_requires_the_complete_12_artifact_contract():
    finalizer_path = SCRIPT.with_name("finalize_contextual_target_f1_hc3_replication_frontier_v3.py")
    finalizer_spec = importlib.util.spec_from_file_location("replication_finalizer_v3", finalizer_path)
    finalizer = importlib.util.module_from_spec(finalizer_spec)
    finalizer_spec.loader.exec_module(finalizer)
    assert finalizer.REQUIRED_ARTIFACTS == (
        "F1_HC3_15A4_AUTHORITY.json",
        "F1_HC3_REUSABLE_NUISANCE_ADMISSIBILITY_CONTRACT.md",
        "F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv",
        "F1_HC3_SOURCE_PREFIX_REPLICATION.csv",
        "F1_HC3_LEVERAGE_SVD_QR_CROSSCHECK.json",
        "F1_HC3_NPH52_DONOR_INDISPENSABILITY.json",
        "F1_HC3_NPH_FREE_FRONTIER_SUMMARY.json",
        "F1_HC3_15A4_INDEPENDENT_VALIDATION.json",
        "F1_HC3_15A4_MULTIAGENT.md",
        "F1_HC3_15A4_SOURCE_MANIFEST.csv",
        "F1_HC3_15A4_MANIFEST.csv",
        "F1_HC3_15A4_EXTERNAL_REVIEW_HANDOFF.md",
    )
    assert finalizer.snapshot_manifest_path("derive.py") == "source_snapshot/derive.py"
