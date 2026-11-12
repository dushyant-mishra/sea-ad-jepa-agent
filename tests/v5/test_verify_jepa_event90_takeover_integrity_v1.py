"""Event90 source continuity and no-promotion hostile tests (NO NETWORK/TRAINING)."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.v5 import verify_jepa_event90_takeover_integrity_v1 as v

ROOT = Path(__file__).resolve().parents[2]


def original():
    obj = json.loads((ROOT / v.MAP).read_text(encoding="utf-8"))
    human = (ROOT / v.HUMAN).read_bytes()
    return obj, human


def test_unmodified_shared_event90_human_machine_scope():
    doc, human = original()
    result = v.validate_manifest(doc, human)
    assert result["source_paths_reachable_at_historical_refs"] == 55
    assert result["source_paths_known_bad"] == 1
    assert result["owner_only_unverified"] == 4
    assert result["training_authorized"] is False
    assert result["biological_qualification_proved"] is False


@pytest.mark.parametrize("change,expected", [
    (lambda x: x.update(authority="REAL_TRAINING_ON"), "AUTHORITY_CHANGED"),
    (lambda x: x["branch_contract"]["canonical_audit"].update(pr=999),
     "AUDIT_BRANCH_CHANGED"),
    (lambda x: x["branch_contract"]["active_handoff"].update(pr=999),
     "HANDOFF_BRANCH_CHANGED"),
    (lambda x: x["historical_scope"]["locator_counts"].update(
        found_at_recorded_ref=56), "HISTORICAL_60_LOCATOR_COUNTS"),
    (lambda x: x["extra_finding"].update(legacy_path="some-other-file"),
     "BAD_OR_MISSING_SOURCE_ERRATUM"),
    (lambda x: x["data_and_expiry"]["v80_controller_owner_only"].update(
        verified_private_vault=True), "PRIVATE_CONTROLLER_BOUNDARY_MISSING"),
    (lambda x: x["data_and_expiry"]["v80_controller_owner_only"].update(
        expires_at_utc="2029-01-01T00:00:00Z"),
     "PRIVATE_CONTROLLER_BOUNDARY_MISSING"),
    (lambda x: x["data_and_expiry"]["synthetic_dev2048_fit"].update(
        scope="REAL_HUMAN_RNA_ALLOWED"), "SYNTHETIC_FIT_EXPIRY_OR_SCOPE"),
    (lambda x: x["macha_original_red_immutable"][0].update(blob="0"*40),
     "ORIGINAL_MACHA_RED_DRIFT"),
    (lambda x: x["newest_ci"].update(independent_scoped_acceptance="ACCEPTED"),
     "AUTHOR_CI_MISLABELED_ACCEPTED"),
    (lambda x: x["implementation_heads_20261105"][13].update(head="0"*40),
     "IMPLEMENTATION_HEAD_CHANGED"),
    (lambda x: x["permanent_two_branch_rule"].update(next_event_id=1),
     "FUTURE_HANDOFF_PROTOCOL_MISSING"),
])
def test_false_custody_or_scientific_promotion_refuses(change, expected):
    source, human = original()
    doc = deepcopy(source)
    change(doc)
    with pytest.raises(ValueError, match=expected):
        v.validate_manifest(doc, human)


def test_changing_handoff_text_breaks_exact_mirror_sha():
    doc, human = original()
    with pytest.raises(ValueError, match="MIRRORED_HUMAN_BLOB_CHANGED"):
        v.validate_manifest(doc, human + b"\nFALSE_NEW_AUTHORITY\n")


def test_exact_roles_refuse_unknown_others():
    with pytest.raises(ValueError, match="UNSUPPORTED_REPOSITORY_ROLE"):
        v.validate_repository(ROOT, role="production")


def test_historic_source_names_never_path_traverse():
    for x in ("../secrets.txt", "/tmp/private", "./file", ""):
        with pytest.raises(ValueError):
            v._relative(x)


def test_event90_machine_has_no_sealed_controller_bytes():
    source, human = original()
    assert b"CONTROLLER_PRIVATE_OWNED" not in human
    assert source["data_and_expiry"]["v80_controller_owner_only"][
        "verified_private_vault"] is False
    assert source["data_and_expiry"]["v80_controller_owner_only"][
        "original_artifact_id"] == 11866917064



def _current_or_isolated_first_read():
    """On #322, use a static sample; only #460 owns the live first-read file."""
    actual = ROOT / v.HANDOFF
    if actual.is_file():
        return actual.read_text(encoding="utf-8")
    return (
        "# READ FIRST — EVENT107 (synthetic test fixture)\\n\\n"
        "**Canonical historical audit [#322](https://github.com/dushyant-mishra/"
        "sea-ad-jepa-agent/pull/322) exact head "
        "`aed40a3deb98932758b64785a328dd8f161ef39b`.** "
        "[Active handoff #460](https://github.com/dushyant-mishra/"
        "sea-ad-jepa-agent/pull/460). "
        "Read Event90 and retain the source record. " + v.AUTHORITY +
        "\\n\\n---\\n"
    )


def test_live_event107_first_read_has_exact_audit_head_and_original_event90():
    pointer = _current_or_isolated_first_read()
    current = v.verify_latest_first_read(pointer)
    assert current["latest_event"] >= 107
    assert len(current["audit_head"]) == 40
    if (ROOT / v.HANDOFF).is_file():
        report = v.validate_repository(ROOT, role="handoff")
        assert report["role"] == "handoff"


def test_latest_first_read_refuses_invalid_canonical_head():
    pointer = _current_or_isolated_first_read()
    current = v.verify_latest_first_read(pointer)
    changed = pointer.replace(current["audit_head"], "INVALID_SHA", 1)
    with pytest.raises(ValueError, match="HANDOFF_EXACT_AUDIT_HEAD_MISSING"):
        v.verify_latest_first_read(changed)


def test_latest_first_read_refuses_erased_original_event90_reference():
    pointer = _current_or_isolated_first_read()
    top = pointer.split("\\n---\\n", 1)[0].replace("Event90", "Obliterated90")
    with pytest.raises(ValueError, match="HANDOFF_NEW_FIRST_READ_INCOMPLETE"):
        v.verify_latest_first_read(top)
