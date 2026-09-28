"""V27 exact non-spillover controls: metadata may be numeric; arbitrary training geometry may not."""
import copy,json,pathlib,pytest
from scripts.v5.v27_teacher_proposal_firewall import check
P=pathlib.Path(__file__).resolve().parents[1]/"docs/agent/JEPA_V27_PROSPECTIVE_TEACHER_TARGET_DECISION_DRAFT_20260926.json"
def original():return json.loads(P.read_text(encoding="utf-8"))
def test_unresolved_teacher_proposal_is_an_explicit_non_authorizing_draft():
    assert check(original()).startswith("PASS_NON_AUTHORIZING")
def test_replacing_null_with_old_synthetic_mask_must_fail():
    d=original();d["masking"]["mask_fraction"]=.40
    with pytest.raises(ValueError,match="STOP_IMPORTED_MASKING"):check(d)
def test_replacing_null_with_old_architecture_or_ema_fails():
    for k,v in (("provisional_width",32),("ema_half_life_accepted_presentations",500),("update_budget",40)):
        d=original();d["model_and_schedule"][k]=v
        with pytest.raises(ValueError,match="STOP_UNJUSTIFIED"):check(d)
def test_fake_train_permission_or_source_fails():
    d=original();d["training_authorized"]=True
    with pytest.raises(ValueError,match="STOP_FALSE_AUTHORITY"):check(d)
    d=original();d["full104_existing_metadata"]["fit_donors"]=94
    with pytest.raises(ValueError,match="STOP_DATASET_SCOPE_SPILLOVER"):check(d)
def test_unfrozen_training_donor_scope_cannot_claim_unseen_donor():
    d=original();d["weighting"]["actually_frozen_training_donors"]=104
    with pytest.raises(ValueError,match="STOP_UNAPPROVED_TRAINING_DONOR_SET"):check(d)
    d=original();d["weighting"]["unseen_donor_claim_permitted_for_all104_training"]=True
    with pytest.raises(ValueError,match="STOP_FAKE_HELDOUT"):check(d)
