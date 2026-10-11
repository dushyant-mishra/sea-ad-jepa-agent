"""Launch-authority semantics of the finalized V2_CORE qualification contract (PR #288 controller ruling 6114753697).

Only the final, immutable V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json may authorize world generation. The historical V1
contract (70edabb8...) and the V2 draft (cbfa332b...) must be refused by every world generator, as must any final
contract whose bytes, hash file, controller binding, evidence hashes, gate arithmetic, G, alpha or launch status
differ from what the controller accepted. The builder must regenerate both the final and the draft byte for byte.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
QDIR = ROOT / "results" / "v79" / "v2_core_qualification"
FINAL = QDIR / "V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
DRAFT = QDIR / "V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json"
V1 = QDIR / "V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json"
BUILDER = ROOT / "scripts" / "v79" / "build_v79_v2_core_contract.py"
Q11 = "Q11_OMITTED_OPERATOR"
APPROVED_LIMIT = {("Q01_WEAK_DONOR", "detection", "BIAS_DONOR_SD"), ("Q01_WEAK_DONOR", "positive", "BIAS_DONOR_SD"),
                  ("Q08_SPARSE_DETECTION", "positive", "BIAS_DONOR_SD"), ("Q09_POSITIVE_TAIL", "positive", "BIAS_DONOR_SD")}


@pytest.fixture()
def L():
    return importlib.import_module("v79_v2_core_launch")


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _write_as_final(tmp: Path, contract_bytes: bytes) -> Path:
    """Place bytes under the final contract's name with a matching .sha256 file (an attacker who rehashes)."""
    out = tmp / FINAL.name
    out.write_bytes(contract_bytes)
    out.with_suffix(".sha256").write_text(f"{hashlib.sha256(contract_bytes).hexdigest()}  {out.name}\n",
                                          encoding="utf-8")
    return out


# --------------------------------------------------------------------------------------------- A final accepted
def test_final_v2_contract_is_accepted_as_launch_authority(L):
    c = L.require_launch_authority(FINAL, root=ROOT)
    assert c["status"] == L.FINAL_STATUS == "FROZEN_PROSPECTIVE_LAUNCH_AUTHORITY__NO_QUALIFICATION_FIT_RUN"
    assert c["launch_authority"] is True
    assert c["controller_ruling"]["pr"] == 288 and c["controller_ruling"]["comment_id"] == "6114753697"
    assert c["controller_model_decision"] == "FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY"
    assert hashlib.sha256(FINAL.read_bytes()).hexdigest() == L.FINAL_CONTRACT_SHA256
    assert FINAL.with_suffix(".sha256").read_text(encoding="utf-8").split()[0] == L.FINAL_CONTRACT_SHA256


# ----------------------------------------------------------------------------------------- B/C history refused
@pytest.mark.parametrize("historical", [V1, DRAFT], ids=["V1", "V2_DRAFT"])
def test_historical_contracts_are_refused_as_launch_authority(L, historical):
    with pytest.raises(L.LaunchAuthorityRefused):
        L.require_launch_authority(historical, root=ROOT)
    with pytest.raises(L.LaunchAuthorityRefused):
        L.validate_launch_semantics(_load(historical))            # refused on content too, not only on name


@pytest.mark.parametrize("historical", [V1, DRAFT], ids=["V1", "V2_DRAFT"])
def test_a_historical_contract_renamed_as_final_is_refused(L, historical, tmp_path):
    fake = _write_as_final(tmp_path, historical.read_bytes())
    with pytest.raises(L.LaunchAuthorityRefused):
        L.require_launch_authority(fake)


def test_historical_contracts_keep_their_accepted_bytes_and_flags():
    assert hashlib.sha256(V1.read_bytes()).hexdigest() == \
        "70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540"
    assert hashlib.sha256(DRAFT.read_bytes()).hexdigest() == \
        "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"
    assert _load(V1).get("launch_authority", False) is False
    assert _load(DRAFT)["launch_authority"] is False
    assert _load(DRAFT)["status"] == "PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION"


# ----------------------------------------------------------------------------------------- D tampering refused
def test_tampered_final_bytes_are_refused(L, tmp_path):
    out = tmp_path / FINAL.name
    b = bytearray(FINAL.read_bytes())
    b[len(b) // 2] ^= 0x01
    out.write_bytes(bytes(b))
    shutil.copy(FINAL.with_suffix(".sha256"), out.with_suffix(".sha256"))
    with pytest.raises(L.LaunchAuthorityRefused):
        L.require_launch_authority(out)


def test_tampered_sha256_file_is_refused(L, tmp_path):
    out = tmp_path / FINAL.name
    shutil.copy(FINAL, out)
    out.with_suffix(".sha256").write_text("0" * 64 + f"  {out.name}\n", encoding="utf-8")
    with pytest.raises(L.LaunchAuthorityRefused):
        L.require_launch_authority(out)


def _q11_gate_to_limit(c):
    g = next(x for x in c["gates"]["list"] if x["world"] == Q11 and x["gate"] == "COVERAGE_DONOR_EFFECTS")
    g["verdict_class"] = "LIMIT"


def _extra_limit(c):
    g = next(x for x in c["gates"]["list"] if x["world"] == "Q00_BASELINE" and x["gate"] == "BIAS_DONOR_SD")
    g["verdict_class"] = "LIMIT"


MUTATIONS = {
    "controller_comment": lambda c: c["controller_ruling"].__setitem__("comment_id", "6114694791"),
    "controller_decision": lambda c: c.__setitem__("controller_model_decision", "REOPENED"),
    "masked_replay_hash": lambda c: c["accepted_evidence"]["masked_replay"].__setitem__("sha256", "0" * 64),
    "masking_audit_hash": lambda c: c["accepted_evidence"]["masking_audit"].__setitem__("sha256", "0" * 64),
    "support_mask_hash": lambda c: c["accepted_evidence"]["support_mask"].__setitem__("measured_op_gene_sha256", "0" * 64),
    "hard_statistical_gate_count": lambda c: c["gates"]["multiplicity"]["gate_counts"].__setitem__("hard_statistical", 264),
    "genes_per_world": lambda c: c["worlds"].__setitem__("genes_per_world", 45),
    "alpha": lambda c: c["gates"]["multiplicity"].__setitem__("alpha_per_gate", 0.05 / 264),
    "planned_fits": lambda c: c["resources"]["estimate"].__setitem__("n_fits", 1080),
    "launch_status": lambda c: c.__setitem__("status", "PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION"),
    "launch_authority_flag": lambda c: c.__setitem__("launch_authority", False),
    "q11_gate_downgraded": _q11_gate_to_limit,
    "extra_limit_gate": _extra_limit,
    "terminal_lock_removed": lambda c: c["terminal_logic"].pop("terminal_lock"),
    "worlds_generated": lambda c: c.__setitem__("qualification_worlds_generated", 1),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_rehashed_semantic_tampering_is_refused(L, name, tmp_path):
    c = copy.deepcopy(_load(FINAL))
    MUTATIONS[name](c)
    with pytest.raises(L.LaunchAuthorityRefused):                 # semantic layer, independent of any hash
        L.validate_launch_semantics(c)
    fake = _write_as_final(tmp_path, (json.dumps(c, indent=1) + "\n").encode("utf-8"))
    with pytest.raises(L.LaunchAuthorityRefused):                 # hash layer: the pinned final SHA-256
        L.require_launch_authority(fake)


def test_changed_evidence_files_on_disk_are_refused(L, tmp_path):
    c = _load(FINAL)
    rels = [v["path"] for v in c["inputs"].values()]
    for rel in rels:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, dst)
    L.require_launch_authority(FINAL, root=tmp_path)              # intact copies are accepted
    victim = tmp_path / c["inputs"]["masked_replay"]["path"]
    victim.write_bytes(victim.read_bytes() + b" ")
    with pytest.raises(L.LaunchAuthorityRefused):
        L.require_launch_authority(FINAL, root=tmp_path)


# ---------------------------------------------------------------------------- frozen arithmetic and semantics
def test_final_contract_keeps_the_accepted_arithmetic(L):
    c = L.require_launch_authority(FINAL, root=ROOT)
    m = c["gates"]["multiplicity"]
    assert len(c["worlds"]["world_list"]) == 12
    assert c["worlds"]["genes_per_world"] == 44
    assert c["resources"]["estimate"]["n_fits"] == 1056
    assert m["gate_counts"]["hard_statistical"] == 260
    assert m["gate_counts"]["hard_rule"] == 28
    assert m["gate_counts"]["limit_statistical"] == 4
    assert m["gate_counts"]["limit_rule"] == 0
    assert m["familywise_false_fail"] == 0.05
    assert m["alpha_per_gate"] == 0.05 / 260
    limit = {(g["world"], g["part"], g["gate"]) for g in c["gates"]["list"] if g["verdict_class"] == "LIMIT"}
    assert limit == APPROVED_LIMIT
    assert all(g["verdict_class"] == "FAIL" for g in c["gates"]["list"] if g["world"] == Q11)
    assert c["terminal_logic"]["post_terminal_label"] == "POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION"
    assert c["qualification_worlds_generated"] == 0 and c["qualification_fits_run"] == 0
    assert c["boundaries"]["training_authorized"] is False


def test_final_contract_binds_the_accepted_evidence_hashes(L):
    c = L.require_launch_authority(FINAL, root=ROOT)
    e = c["accepted_evidence"]
    assert e["masked_replay"]["sha256"] == "caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683"
    assert e["masking_audit"]["sha256"] == "6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41"
    assert e["support_mask"]["measured_op_gene_sha256"] == \
        "12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab"
    assert e["g500_cache"]["sha256"] == "2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62"
    assert e["structural_support_authority"]["sha256"] == \
        "ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa"
    assert e["contract_v1"]["sha256"] == "70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540"
    assert e["contract_v2_draft"]["sha256"] == "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"


def test_final_contract_states_the_narrowed_source_interpretation(L):
    c = L.require_launch_authority(FINAL, root=ROOT)
    s = c["source_term_interpretation"]
    assert s["term_status"] == "IN"
    assert "predictive/acquisition-source structure among estimable measured comparisons" in s["interpretation"]
    for forbidden in ("universal source biology", "causal source effect", "biological mechanism"):
        assert forbidden in s["not_claimed"]
    assert "UNDEFINED" in s["single_source_genes"]
    assert c["worlds"]["modification_semantics"]["operator=omitted_perturbation"].count("MILD") == 1


def test_final_differs_from_the_accepted_draft_only_in_finalization_fields():
    final, draft = _load(FINAL), _load(DRAFT)
    allowed_changed = {"status", "launch_authority", "launch_condition", "development_finding_structural_support"}
    allowed_new = {"launch_authority_scope", "controller_ruling", "controller_model_decision",
                   "source_term_interpretation", "accepted_evidence", "qualification_worlds_generated",
                   "qualification_fits_run", "finalization"}
    assert set(final) - set(draft) == allowed_new
    assert set(draft) - set(final) <= {"launch_condition"}
    for k in set(draft) & set(final):
        if k not in allowed_changed:
            assert final[k] == draft[k], k


def test_builder_regenerates_final_and_draft_byte_for_byte():
    r = subprocess.run([sys.executable, str(BUILDER), str(ROOT), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-3000:]
    assert hashlib.sha256(FINAL.read_bytes()).hexdigest() in r.stdout
    assert hashlib.sha256(DRAFT.read_bytes()).hexdigest() in r.stdout


def test_no_qualification_world_artifacts_exist():
    allowed = {"V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json", "V79_V2_CORE_QUALIFICATION_CONTRACT_V1.sha256",
               "V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json", "V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.sha256",
               "V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json", "V79_V2_CORE_QUALIFICATION_CONTRACT_V2.sha256",
               "inputs", "finalization"}
    assert {p.name for p in QDIR.iterdir()} <= allowed
