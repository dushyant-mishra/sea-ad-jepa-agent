"""A successor binding must be harder to obtain than the digest it replaces.

The failure this mechanism answers is real: a Phase-IV bound input drifted and
the regression suite went red. The tempting repair - edit the recorded digest -
would turn a working integrity signal into a false pass, which is exactly what a
freeze exists to prevent.

So the successor is deliberately narrow. These tests enumerate the ways it must
refuse. The first test is the POSITIVE CONTROL: the real, shipped record must
actually resolve the real, observed drift. Without it, every refusal below could
be firing for an unrelated reason and the suite would look healthy while
authorizing nothing.

Nothing here opens an Audit-B N1 burden outcome, a terminal masking result,
D_shared, G5, pathology or DEV/SEALED data, and nothing authorizes training.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import sea_ad_jepa.v5.audit_b_bound_input_successor_v2 as S
from sea_ad_jepa.v5.audit_b_execution_contract_v1 import PHASE_IV_SAMPLE_FREEZE_DIGEST
from sea_ad_jepa.v5.audit_b_execution_preflight_v1 import verify_phase_iv_sample_freeze

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/"
    "AUDIT_B_FROZEN_TARGET_SAMPLE.json"
)
PLANNER_REL = "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py"
FROZEN_PLANNER_SHA = "143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d"


@pytest.fixture()
def record() -> dict:
    return json.loads(S.SUCCESSOR_RECORD_PATH.read_text(encoding="utf-8"))


def rewrite(tmp_path: Path, payload: dict, *, name: str = "successor.json") -> Path:
    """Persist a mutated record with a self-consistent internal digest.

    The internal digest is recomputed on purpose: otherwise every negative test
    below would be caught by the digest check and none of the specific contract
    rules would ever be exercised.
    """
    payload = copy.deepcopy(payload)
    payload["successor_digest"] = S.canonical_digest(payload)
    out = tmp_path / name
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return out


def load(path: Path, **kwargs):
    kwargs.setdefault("require_pinned_digest", False)
    return S.load_successor(path, repo_root=ROOT, **kwargs)


# --------------------------------------------------------------------------- #
# POSITIVE CONTROL
# --------------------------------------------------------------------------- #


def test_the_real_record_resolves_the_real_drift() -> None:
    """Without this, every refusal below could be firing for the wrong reason."""
    successor = S.load_successor(S.SUCCESSOR_RECORD_PATH, repo_root=ROOT)
    observed = verify_phase_iv_sample_freeze(
        SAMPLE, repo_root=ROOT, successor=successor
    )
    assert len(observed) == 7
    assert observed["planner_source"] == (
        "de2f019e28675e3258cfeede65f77557210f5fcd083f94ae09f97b1c8629f9f8"
    )


def test_the_same_check_without_the_record_still_refuses() -> None:
    """The original gate is preserved. A successor is a key, not a removal."""
    with pytest.raises(ValueError, match="bound input drift for planner_source"):
        verify_phase_iv_sample_freeze(SAMPLE, repo_root=ROOT)


def test_the_record_supersedes_exactly_one_role(record) -> None:
    assert sorted(record["superseded_bindings"]) == ["planner_source"]
    assert len(record["unchanged_bindings"]) == 6


def test_the_record_authorizes_nothing_else(record) -> None:
    assert record["execution_authorized"] is False
    assert record["training_authorized"] is False
    assert record["terminal_masking_outcomes_inspected"] is False
    assert record["audit_b_n1_burden_outcomes_opened"] is False
    assert "Audit-B N1 execution" in record["does_not_authorize"]


def test_the_record_descends_from_the_pinned_parent_freeze(record) -> None:
    assert record["parent_freeze_digest"] == PHASE_IV_SAMPLE_FREEZE_DIGEST
    assert record["parent_freeze_path"].endswith("AUDIT_B_FROZEN_TARGET_SAMPLE.json")


def test_the_parent_freeze_still_records_the_original_digest() -> None:
    """The original frozen value is preserved, not overwritten."""
    parent = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert parent["bound_inputs"]["planner_source"]["sha256"] == FROZEN_PLANNER_SHA
    assert parent["frozen_before_any_burden_was_computed"] is True


def test_the_record_pins_the_planner_execution_mode(record) -> None:
    """A byte digest alone no longer pins behaviour, so the mode is pinned too."""
    mode = record["required_execution_mode"]
    assert mode["g3_fit_objective"] == "MUST_BE_ABSENT__HISTORICAL_DEFAULT_PATH_ONLY"
    assert "run_all_primary_folds_streaming" in mode["planner_entrypoints"]


# --------------------------------------------------------------------------- #
# The sample itself must be provably the same sample
# --------------------------------------------------------------------------- #


def test_a_rerolled_sample_can_never_be_rescued(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["sample_identity"]["rederived_samples_digest"] = "b" * 64
    with pytest.raises(ValueError, match="sample was re-rolled"):
        load(rewrite(tmp_path, bad))


def test_an_unattested_sample_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["sample_identity"]["sample_is_unchanged"] = False
    with pytest.raises(ValueError, match="unchanged target sample"):
        load(rewrite(tmp_path, bad))


def test_an_unrederived_sample_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["sample_identity"]["rederived_from_parent_salt_and_universe"] = False
    with pytest.raises(ValueError, match="re-derive the sample"):
        load(rewrite(tmp_path, bad))


def test_a_missing_sample_identity_block_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["sample_identity"] = "attested"
    with pytest.raises(ValueError, match="sample-identity attestation"):
        load(rewrite(tmp_path, bad))


def test_a_malformed_sample_digest_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["sample_identity"]["parent_samples_digest"] = "short"
    bad["sample_identity"]["rederived_samples_digest"] = "short"
    with pytest.raises(ValueError, match="sample-identity digest is malformed"):
        load(rewrite(tmp_path, bad))


# --------------------------------------------------------------------------- #
# Immutability of the parent
# --------------------------------------------------------------------------- #


def test_a_modified_parent_freeze_is_detected(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["parent_freeze_artifact_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="parent Phase-IV freeze artifact has been modified"):
        load(rewrite(tmp_path, bad))


def test_a_foreign_parent_freeze_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["parent_freeze_digest"] = "d" * 64
    with pytest.raises(ValueError, match="does not descend from the pinned"):
        load(rewrite(tmp_path, bad))


def test_a_parent_path_outside_the_repo_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["parent_freeze_path"] = "../outside.json"
    with pytest.raises(ValueError, match="escapes repo_root"):
        load(rewrite(tmp_path, bad))


def test_an_absolute_parent_path_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["parent_freeze_path"] = str(SAMPLE)
    with pytest.raises(ValueError, match="must be a relative repo path"):
        load(rewrite(tmp_path, bad))


# --------------------------------------------------------------------------- #
# The record cannot grant itself authority
# --------------------------------------------------------------------------- #


def test_an_unpinned_record_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["source_pull_request"] = 999
    path = rewrite(tmp_path, bad)
    with pytest.raises(ValueError, match="different bound-input successor record"):
        S.load_successor(path, repo_root=ROOT)


def test_a_tampered_internal_digest_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["successor_digest"] = "e" * 64
    out = tmp_path / "tampered.json"
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(bad, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="internal digest mismatch"):
        load(out)


def test_the_shipped_record_matches_its_pinned_digest() -> None:
    payload = json.loads(S.SUCCESSOR_RECORD_PATH.read_text(encoding="utf-8"))
    assert S.canonical_digest(payload) == S.AUDIT_B_BOUND_INPUT_SUCCESSOR_V2_DIGEST
    assert payload["successor_digest"] == S.AUDIT_B_BOUND_INPUT_SUCCESSOR_V2_DIGEST


def test_a_missing_record_is_refused(tmp_path) -> None:
    with pytest.raises(ValueError, match="successor record is missing"):
        load(tmp_path / "absent.json")


def test_a_foreign_schema_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["schema"] = "SOMETHING_ELSE_V9"
    with pytest.raises(ValueError, match="schema mismatch"):
        load(rewrite(tmp_path, bad))


# --------------------------------------------------------------------------- #
# Only a legitimate version change continues a binding
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("classification", S.NON_AUTHORIZING_CLASSIFICATIONS)
def test_a_non_authorizing_classification_records_but_refuses(
    tmp_path, record, classification
) -> None:
    """SEMANTIC_CHANGE and UNINTENDED_MODIFICATION are explanations, not permissions."""
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["classification"] = classification
    successor = load(rewrite(tmp_path, bad))
    with pytest.raises(ValueError, match="does not continue the binding"):
        S.resolve_drift(
            "planner_source",
            recorded=FROZEN_PLANNER_SHA,
            observed=record["superseded_bindings"]["planner_source"]["to_sha256"],
            successor=successor,
        )


def test_an_unknown_classification_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["classification"] = "PROBABLY_FINE"
    with pytest.raises(ValueError, match="unknown classification"):
        load(rewrite(tmp_path, bad))


def test_a_label_is_not_a_rationale(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["rationale"] = "looks fine"
    with pytest.raises(ValueError, match="written rationale, not a label"):
        load(rewrite(tmp_path, bad))


# --------------------------------------------------------------------------- #
# The waiver is pinned to one exact transition
# --------------------------------------------------------------------------- #


def test_a_waiver_for_a_different_origin_is_refused(record) -> None:
    successor = S.load_successor(S.SUCCESSOR_RECORD_PATH, repo_root=ROOT)
    with pytest.raises(ValueError, match="but the frozen record says"):
        S.resolve_drift(
            "planner_source",
            recorded="f" * 64,
            observed=record["superseded_bindings"]["planner_source"]["to_sha256"],
            successor=successor,
        )


def test_a_waiver_for_a_different_destination_is_refused() -> None:
    """If the planner moves again, the waiver expires immediately."""
    successor = S.load_successor(S.SUCCESSOR_RECORD_PATH, repo_root=ROOT)
    with pytest.raises(ValueError, match="but the checkout contains"):
        S.resolve_drift(
            "planner_source",
            recorded=FROZEN_PLANNER_SHA,
            observed="a" * 64,
            successor=successor,
        )


def test_a_role_the_record_does_not_cover_is_refused() -> None:
    successor = S.load_successor(S.SUCCESSOR_RECORD_PATH, repo_root=ROOT)
    with pytest.raises(ValueError, match="does not cover this role"):
        S.resolve_drift(
            "qualification_runner",
            recorded="1" * 64,
            observed="2" * 64,
            successor=successor,
        )


def test_no_successor_at_all_is_the_fail_closed_default() -> None:
    with pytest.raises(ValueError, match="bound input drift for planner_source"):
        S.resolve_drift(
            "planner_source",
            recorded=FROZEN_PLANNER_SHA,
            observed="3" * 64,
            successor=None,
        )


def test_a_self_supersession_is_refused(tmp_path, record) -> None:
    """A successor must record an actual change, never rubber-stamp the status quo."""
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["to_sha256"] = FROZEN_PLANNER_SHA
    with pytest.raises(ValueError, match="supersedes a digest with itself"):
        load(rewrite(tmp_path, bad))


def test_a_preauthorized_future_change_is_refused() -> None:
    """A waiver may only respond to an observed drift, never anticipate one."""
    successor = S.load_successor(S.SUCCESSOR_RECORD_PATH, repo_root=ROOT)
    with pytest.raises(ValueError, match="may not pre-authorize a future change"):
        S.assert_no_uncovered_supersessions(successor=successor, drifted_roles={})


def test_a_role_listed_as_both_superseded_and_unchanged_is_refused(
    tmp_path, record
) -> None:
    bad = copy.deepcopy(record)
    bad["unchanged_bindings"]["planner_source"] = FROZEN_PLANNER_SHA
    with pytest.raises(ValueError, match="both superseded and unchanged"):
        load(rewrite(tmp_path, bad))


def test_an_empty_supersession_set_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"] = {}
    with pytest.raises(ValueError, match="must supersede at least one binding"):
        load(rewrite(tmp_path, bad))


@pytest.mark.parametrize("field", S._REQUIRED_BINDING_FIELDS)
def test_every_required_binding_field_is_mandatory(tmp_path, record, field) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"].pop(field)
    with pytest.raises(ValueError, match="missing fields"):
        load(rewrite(tmp_path, bad))


@pytest.mark.parametrize("field", ("from_sha256", "to_sha256"))
def test_a_malformed_transition_digest_is_refused(tmp_path, record, field) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"][field] = "NOTAHASH"
    with pytest.raises(ValueError, match="malformed digest"):
        load(rewrite(tmp_path, bad))


# --------------------------------------------------------------------------- #
# The cited evidence must exist, match, and have passed
# --------------------------------------------------------------------------- #


def test_a_drifted_equivalence_receipt_is_detected(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["equivalence_receipt_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="equivalence receipt drifted"):
        load(rewrite(tmp_path, bad))


def test_a_failed_equivalence_receipt_cannot_authorize(tmp_path, record) -> None:
    receipt_rel = record["superseded_bindings"]["planner_source"][
        "equivalence_receipt_path"
    ]
    receipt = json.loads((ROOT / receipt_rel).read_text(encoding="utf-8"))
    receipt["equivalent"] = False
    fake_dir = tmp_path / "fake_repo"
    (fake_dir / Path(receipt_rel).parent).mkdir(parents=True, exist_ok=True)
    fake_receipt = fake_dir / receipt_rel
    with fake_receipt.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    # mirror the parent freeze so the earlier checks pass and this one is reached
    (fake_dir / Path(record["parent_freeze_path"]).parent).mkdir(
        parents=True, exist_ok=True
    )
    (fake_dir / record["parent_freeze_path"]).write_bytes(SAMPLE.read_bytes())

    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["equivalence_receipt_sha256"] = (
        S.sha256_file(fake_receipt)
    )
    path = rewrite(tmp_path, bad)
    with pytest.raises(ValueError, match="receipt that did not pass"):
        S.load_successor(path, repo_root=fake_dir, require_pinned_digest=False)


def test_a_receipt_about_different_bytes_cannot_authorize(tmp_path, record) -> None:
    receipt_rel = record["superseded_bindings"]["planner_source"][
        "equivalence_receipt_path"
    ]
    receipt = json.loads((ROOT / receipt_rel).read_text(encoding="utf-8"))
    receipt["frozen_planner_sha256"] = "9" * 64
    fake_dir = tmp_path / "wrong_bytes_repo"
    (fake_dir / Path(receipt_rel).parent).mkdir(parents=True, exist_ok=True)
    fake_receipt = fake_dir / receipt_rel
    with fake_receipt.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    (fake_dir / Path(record["parent_freeze_path"]).parent).mkdir(
        parents=True, exist_ok=True
    )
    (fake_dir / record["parent_freeze_path"]).write_bytes(SAMPLE.read_bytes())

    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["equivalence_receipt_sha256"] = (
        S.sha256_file(fake_receipt)
    )
    path = rewrite(tmp_path, bad)
    with pytest.raises(ValueError, match="does not compare the recorded old bytes"):
        S.load_successor(path, repo_root=fake_dir, require_pinned_digest=False)


def test_a_receipt_path_escaping_the_repo_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"]["equivalence_receipt_path"] = (
        "../elsewhere.json"
    )
    with pytest.raises(ValueError, match="escapes repo_root"):
        load(rewrite(tmp_path, bad))


# --------------------------------------------------------------------------- #
# Degenerate and dangerous flag states
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("flag", "value", "pattern"),
    (
        ("execution_authorized", True, "authorizes execution"),
        ("terminal_masking_outcomes_inspected", True, "terminal masking outcomes"),
        ("training_authorized", True, "authorizes training"),
        ("execution_authorized", None, "authorizes execution"),
        ("training_authorized", "no", "authorizes training"),
    ),
)
def test_a_dangerous_flag_state_is_refused(tmp_path, record, flag, value, pattern) -> None:
    bad = copy.deepcopy(record)
    bad[flag] = value
    with pytest.raises(ValueError, match=pattern):
        load(rewrite(tmp_path, bad))


def test_a_record_that_does_not_precede_burden_computation_is_refused(
    tmp_path, record
) -> None:
    bad = copy.deepcopy(record)
    bad["frozen_before_any_burden_was_computed"] = False
    with pytest.raises(ValueError, match="precedes any burden computation"):
        load(rewrite(tmp_path, bad))


def test_a_missing_execution_mode_pin_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["required_execution_mode"] = {}
    with pytest.raises(ValueError, match="pin the execution mode"):
        load(rewrite(tmp_path, bad))


def test_a_missing_unchanged_binding_map_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["unchanged_bindings"] = None
    with pytest.raises(ValueError, match="bindings it does not supersede"):
        load(rewrite(tmp_path, bad))


def test_a_malformed_binding_entry_is_refused(tmp_path, record) -> None:
    bad = copy.deepcopy(record)
    bad["superseded_bindings"]["planner_source"] = "LEGITIMATE"
    with pytest.raises(ValueError, match="is malformed"):
        load(rewrite(tmp_path, bad))
