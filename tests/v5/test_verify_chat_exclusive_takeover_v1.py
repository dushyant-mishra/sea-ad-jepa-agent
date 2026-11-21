"""Hostile static custody tests: no physical rehash and no scientific promotion."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.v5.verify_chat_exclusive_takeover_v1 import (
    DATA, CAL, V1, V2, DOC, ROOT, validate_root, verify_record
)

def original():
    return (
        json.loads((ROOT/DATA).read_text()),
        json.loads((ROOT/CAL).read_text()),
        json.loads((ROOT/V1).read_text()),
        json.loads((ROOT/V2).read_text()),
        (ROOT/DOC).read_text(),
    )

def test_original_20_source_inventory_and_supersession_validate():
    validate_root(ROOT)
    inv,cal,v1,v2,doc=original()
    assert len(inv["files"])==20
    assert cal["physical_verification"]["verified_member_sha256_count"]==97
    assert v1["schema"]!=v2["schema"]
    assert v2["assessment"]=="INSUFFICIENT_TO_AUTHORIZE_AUTHENTIC_G7_E3"

@pytest.mark.parametrize("attack",[
    lambda a:a[0].update(current_authority="REAL_TRAINING_ON"),
    lambda a:a[0].update(archival_scope="BINARY_DATA_ALL_COPIED_TO_GITHUB"),
    lambda a:a[0]["files"].pop(),
    lambda a:a[0]["files"].append(deepcopy(a[0]["files"][0])),
    lambda a:a[0]["files"][0].update(sha256="0"*64),
    lambda a:next(x for x in a[0]["files"] if x["name"]=="expression.zip").update(custody="RAW_GITHUB_BYTES"),
    lambda a:a[1]["physical_verification"].update(verified_member_sha256_count=96),
    lambda a:a[1]["physical_verification"].update(historical_manifest_sha256="0"*64),
    lambda a:a[1]["ci"].update(synthetic_archive_hostile_cases_passed=100),
    lambda a:a[1]["ci"].update(real_source_reauthentication_by_ci=True),
    lambda a:a[1]["ci"].update(independent_scientific_acceptance=True),
    lambda a:a[1].update(authority="KNOWN_TRUTH_QUALIFIED"),
    lambda a:a[2].update(assessment="G7_SOURCE_PASS"),
    lambda a:a[3].update(assessment="G7_SOURCE_PASS"),
    lambda a:a[3]["expression_zip"].update(expression_read_before_freeze_is_selection_field=True),
    lambda a:a[3]["expression_zip"].pop("expression_read_before_freeze_column_present"),
])
def test_attempt_to_forge_source_or_corrected_authority_fails(attack):
    args=list(deepcopy(original()[:4]))+[original()[4]]
    attack(args)
    with pytest.raises(ValueError,match="CHAT_EXCLUSIVE_TAKEOVER_NO_PROMOTION_REFUSAL"):
        verify_record(*args)

def test_archived_binary_hashes_are_custody_not_recoverability():
    inv,cal,v1,v2,doc=original()
    entries={x["name"]:x for x in inv["files"]}
    assert "HASH_ONLY" in entries["FOUNDATION_CALIBRATION_BUNDLE_20260824.zip"]["custody"]
    assert "HASH_ONLY" in entries["t1_checkpoint_u0200.zip"]["custody"]
    assert cal["ci"]["real_source_reauthentication_by_ci"] is False
    assert "not copied to GitHub" in doc
