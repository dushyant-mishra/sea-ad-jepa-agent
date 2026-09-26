"""V29 independent science proposal controls; positive control and 12 targeted mutants."""
import copy
import json
from pathlib import Path
import pytest
from scripts.v5.v29_teacher_decision_firewall import check
PATH=Path(__file__).resolve().parents[1]/"docs/agent/JEPA_V29_TEACHER_DECISION_REQUEST_20260926.json"
def good():return json.loads(PATH.read_text())
def mutation(fn):
    x=good();fn(x)
    with pytest.raises(ValueError,match="STOP_V29_"):check(x)
def test_complete_original_proposal_is_non_authorizing_positive_control():
    assert check(good()).startswith("PASS_NONAUTHORIZING")
def test_old94_population_cannot_replace_true104():
    mutation(lambda x:x["authenticated_metadata"].update(total_reader_fit_donors=94))
def test_wrong_library_parent_digest_rejected():
    mutation(lambda x:x["authenticated_metadata"].update(calibration_zip_sha256="0"*64))
def test_false_real_level4_scan_rejected():
    mutation(lambda x:x["authenticated_metadata"].update(no_all8915_raw_block_scan_qualification=False))
def test_hidden_scalar_objective_cannot_replace_latent_target():
    mutation(lambda x:x["teacher_state"].update(objective="DIRECT_QUERY_SCALAR_REGRESSION"))
def test_student_query_scalar_must_be_withheld_before_mixing():
    mutation(lambda x:x["teacher_state"].update(student_query_scalar="HIDDEN_ONLY_AFTER_MIXING"))
def test_unapproved_synthetic_mask_fraction_does_not_spill_over():
    mutation(lambda x:x["masking"].update(burden_fraction=.40))
def test_unapproved_synthetic_width_does_not_spill_over():
    mutation(lambda x:x["resource_bounded_instrument"].update(model_width=32))
def test_old_ema_momentum_cannot_replace_presentation_half_life():
    mutation(lambda x:x["resource_bounded_instrument"].update(ema_half_life_in_successful_scientific_presentations=249))
def test_heldout_after_all104_training_not_unseen():
    mutation(lambda x:x["split_and_scientific_weight"].update(all104_trained_cannot_be_called_unseen_donor=False))
def test_wrong_D1_equal_operator_weight_cannot_be_base():
    mutation(lambda x:x["split_and_scientific_weight"].update(base_jepa_training_cell_probability="1/(D_train*O_d*n_do)"))
def test_missing_identity_only_negative_control_fails():
    def change(x):x["prospective_evaluation"]["negative_controls"].remove("QUERY_IDENTITY_ONLY")
    mutation(change)
def test_protected_or_B1_training_authority_cannot_be_issued_by_draft():
    mutation(lambda x:x["authority_dependencies"].update(B1_frozen_named_training_contract_issued=True))
def test_own_schema_six_cannot_be_promoted_to_closed():
    mutation(lambda x:x["authority_dependencies"].update(fully_closed_roots=6))
def test_reviving_retracted_S9_or_vacuous_gradient_claim_fails():
    mutation(lambda x:x["governance"].update(s9="BROKEN_BLAS_RECHECK_ALL"))
    mutation(lambda x:x["governance"].update(prior_40of40_counter="PASS"))
