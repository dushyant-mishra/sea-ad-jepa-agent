from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import finalize_v79_v2_core_contract as F  # noqa: E402
import validate_v79_v2_core_launch_contract as V  # noqa: E402

FINAL = ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
FINAL_SHA = FINAL.with_suffix(".sha256")
V1 = ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json"
DRAFT = ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json"


def test_finalizer_targets_controller_ratified_authority():
    assert F.FINAL_REL.endswith("V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json")
    assert F.FINAL_STATUS == "FROZEN_PROSPECTIVE_LAUNCH_AUTHORITY__NO_QUALIFICATION_FIT_RUN"
    assert F.CONTROLLER_RULING_COMMENT == 6114753697
    assert F.CONTROLLER_MODEL_DECISION == "FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY"


def test_final_contract_is_exact_regeneration_and_launch_authority():
    expected = F.serialize_contract(F.build_final_contract(ROOT))
    assert FINAL.read_bytes() == expected
    digest = hashlib.sha256(expected).hexdigest()
    assert FINAL_SHA.read_text(encoding="utf-8").strip() == f"{digest}  {FINAL.name}"
    c = V.validate_launch_contract(FINAL, FINAL_SHA, ROOT)
    assert c["launch_authority"] is True
    assert c["world_generation_authorized"] is False
    assert c["qualification_fits_run"] == 0
    assert c["controller_authority"]["ruling_comment"] == 6114753697
    assert c["controller_authority"]["model_decision"] == "FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY"


def test_historical_v1_and_v2_draft_are_rejected_as_launch_authority():
    for p in (V1, DRAFT):
        with pytest.raises(SystemExit):
            V.validate_launch_contract(p, p.with_suffix(".sha256"), ROOT)


def test_final_contract_freeze_arithmetic_and_evidence_binding():
    c = json.loads(FINAL.read_text(encoding="utf-8"))
    a = c["accepted_qualification_arithmetic"]
    assert a["hard_statistical_gates"] == 260
    assert a["hard_rule_gates"] == 28
    assert a["limit_statistical_gates"] == 4
    assert a["alpha_per_gate"] == pytest.approx(0.05 / 260.0)
    assert a["worlds"] == 12
    assert a["genes_per_world"] == 44
    assert a["planned_fits"] == 1056
    assert c["required_inputs"]["masked_replay"]["sha256"] == "caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683"
    assert c["required_inputs"]["masking_audit"]["sha256"] == "6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41"
    assert c["required_inputs"]["structural_support_mask_sha256"] == "12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab"


def test_tamper_is_rejected(tmp_path: Path):
    raw = json.loads(FINAL.read_text(encoding="utf-8"))
    raw["accepted_qualification_arithmetic"]["hard_statistical_gates"] = 259
    tampered = tmp_path / FINAL.name
    tampered.write_text(json.dumps(raw, indent=1) + "\n", encoding="utf-8")
    tampered_sha = tampered.with_suffix(".sha256")
    digest = hashlib.sha256(tampered.read_bytes()).hexdigest()
    tampered_sha.write_text(f"{digest}  {tampered.name}\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        V.validate_launch_contract(tampered, tampered_sha, ROOT)
