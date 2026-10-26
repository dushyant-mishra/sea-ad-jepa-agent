"""Macha first-pass hostile compatibility review of PR #444 at 28c2bf17.

Synthetic fixtures only.  No protected data, no model, no optimizer, no EMA
update, no subprocess.  Test names encode the expected outcome at 28c2bf17:

* ``test_defect_*``     -- expected to FAIL at 28c2bf17 (suspected defect at
                           the new integration boundary; message states why).
* ``test_boundary_*``   -- expected to PASS (boundary verified to hold).
* ``test_limitation_*`` -- expected to PASS (documents inherited/declared
                           behaviour; not a #444 defect).
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from scripts.v5.td_unified import post_td_fixture_bridge_v1 as bridge
from scripts.v5.td_unified.post_td_fixture_bridge_v1 import (
    FixtureBridgeError,
    stage_fixture_downstream,
)
from scripts.v5.td_unified.mode_equivalence_v1 import SCIENTIFIC_ROLES, FixtureStage
from scripts.v5 import jepa_post_td_harness_contract_v1 as H
from scripts.v5 import jepa_post_td_tournament_controller_v1 as T

ROOT = Path(__file__).resolve().parents[3]


def _h(s: bytes) -> str:
    return hashlib.sha256(s).hexdigest()


def _case(case_id: str = "PLANTED_FIT_ONLY", count: int = 0) -> dict:
    return {
        "schema": "KNOWN_TRUTH_CASEBUNDLE_V1",
        "case_id": case_id,
        "authority_scope": "FIXTURE_ONLY",
        "manifest_sha256": _h(b"dummy manifest"),
        "population_access_policy_sha256": _h(b"dummy policy"),
        "address_universe_sha256": _h(b"dummy universe"),
        "reader_partition": "reader_fit",
        "observations": [
            {"cell_id": "C1", "donor_id": "D1", "source_id": "SRC1",
             "operator_id": "OP1", "address_id": "ADDR1",
             "state": "MEASURED_SCALAR", "count": count, "library_size": 11,
             "evidence_right": "RNA:CORE"},
            {"cell_id": "C1", "donor_id": "D1", "source_id": "SRC1",
             "operator_id": "OP1", "address_id": "ADDR2",
             "state": "STRUCTURALLY_UNMEASURED", "count": None, "library_size": None,
             "evidence_right": "RNA:EXT"},
            {"cell_id": "C1", "donor_id": "D1", "source_id": "SRC1",
             "operator_id": "OP1", "address_id": "ADDR3",
             "state": "WITHHELD_BY_EVIDENCE_RIGHTS", "count": None, "library_size": None,
             "evidence_right": "RNA:CORE"},
        ],
    }


def _stage(label):
    def run(payload):
        return {"stage": label, "previous": _h(repr(payload).encode())}
    return run


def _stages():
    return tuple(FixtureStage(role, _stage(role)) for role in SCIENTIFIC_ROLES)


def _walk(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)


# --------------------------------------------------------------------------
# F1  fixture PASS label -> provenance-free TargetPortfolio once extracted
# --------------------------------------------------------------------------

def test_defect_F1_fixture_portfolio_is_indistinguishable_from_unbound_pass_portfolio():
    r = stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                 fixture_candidate="C1",
                                 fixture_qualifications={"C1": "PASS"})
    p = r["post_td_portfolio"]
    naked = H.build_target_portfolio(selected_candidate="C1", qualifications={"C1": "PASS"})
    other_case = stage_fixture_downstream(case_payload=_case("OTHER_CASE", count=3),
                                          stages=_stages(), fixture_candidate="C1",
                                          fixture_qualifications={"C1": "PASS"})
    assert p["portfolio_sha256"] != naked["portfolio_sha256"], (
        "bridge emits a JEPA_POST_TD_TARGET_PORTFOLIO_V1 whose bytes/hash are identical "
        "to a portfolio built from a bare 'PASS' with no fixture context: block "
        f"qualification_receipt={p['blocks'][0]['qualification_receipt']!r}, no fixture "
        "class, no casebundle binding (other case gives same hash: "
        f"{other_case['post_td_portfolio']['portfolio_sha256'] == p['portfolio_sha256']}). "
        "The FIXTURE_ONLY marker lives only on the discarded outer wrapper."
    )


def test_limitation_F1_impact_extracted_fixture_portfolio_reaches_existing_ready_receipts(tmp_path):
    """Impact evidence for F1 (passes): existing consumers accept the extract."""
    r = stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                 fixture_candidate="C1",
                                 fixture_qualifications={"C1": "PASS"})
    p, a = r["post_td_portfolio"], r["post_td_architecture_plan"]
    pre = H.build_synthetic_rehearsal_preflight(
        repo_root=ROOT, portfolio=p, architecture_plan=a,
        synthetic_package_sha256=_h(b"synthetic package"), output_root=tmp_path)
    assert pre["status"] == "READY_FOR_SYNTHETIC_REHEARSAL_ONLY"
    arm = T.ArchitectureArm("A0", "SHARED_TYPED_HEADS", "SHARED_TYPED_HEADS", "NONE", 256)
    cc = H.MatchedComputeContract(10, 1.0, 1.0, 10, 1, 1, 1.0, 1.0, "CPU")
    man = T.build_architecture_tournament_manifest(
        portfolio=p, arms=[arm], compute_contracts={"A0": cc},
        rare_preservation_required=True)
    assert man["status"] == "READY_FOR_AUTHORIZED_SYNTHETIC_ARCHITECTURE_REHEARSAL"
    assert all(v is False for v in pre["authority"].values())
    assert all(v is False for v in man["authority"].values())
    # At 28c2bf17 nothing in the extracted portfolio recorded that the target
    # came from a fixture (RED PR #450). After the F1 repair every block keeps
    # its fixture-label provenance, bound to the case bundle.
    for block in p["blocks"]:
        rec = block["qualification_receipt"]
        assert rec["receipt_class"] == bridge.FIXTURE_LABEL_RECEIPT_CLASS
        assert rec["biological_qualification"] is False
        assert rec["casebundle_sha256"] == r["casebundle_sha256"]


# --------------------------------------------------------------------------
# F2  TARGET_NONE is only a caller assertion; evidence-backed NONE refused
# --------------------------------------------------------------------------

def test_defect_F2_target_none_cannot_carry_its_own_fail_or_ne_evidence():
    evidence = {"C1": "FAIL", "C2": "NOT_ESTIMABLE", "C3": "FAIL"}
    try:
        r = stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                     fixture_candidate=None,
                                     fixture_qualifications=evidence)
    except FixtureBridgeError as exc:
        pytest.fail(
            "evidence-backed TARGET_NONE (no PASS anywhere) is refused with "
            f"{str(exc)!r}; NONE is reachable only as an evidence-free caller "
            "assertion, so 'TARGET_NONE_IS_LAWFUL' outcomes cannot be distinguished "
            "from a caller that simply passed None"
        )
    assert r["target_candidate_fixture"] == "NONE"
    assert r["post_td_portfolio"] is None


# --------------------------------------------------------------------------
# F3  arbitrary qualification KEYS are accepted and recorded verbatim
# --------------------------------------------------------------------------

def test_defect_F3_noncandidate_claim_keys_enter_portfolio_qualifications():
    q = {"C1": "PASS", "A7_SAME_CODE_PATH": "PASS", "BIOLOGICAL_TARGET_QUALIFIED": "PASS"}
    try:
        r = stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                     fixture_candidate="C1", fixture_qualifications=q)
    except FixtureBridgeError:
        return
    recorded = r["post_td_portfolio"]["qualifications"]
    pytest.fail(
        "bridge validates qualification VALUES but not KEYS; non-roster claim keys "
        f"were hashed into the portfolio: {sorted(set(recorded) - {'C1'})}"
    )


# --------------------------------------------------------------------------
# F4  EMA half-life type confusion passes through the bridge
# --------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [True, 256.9, "256"])
def test_defect_F4_non_integer_ema_half_life_is_coerced_not_refused(bad):
    try:
        r = stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                     fixture_candidate="C1",
                                     fixture_qualifications={"C1": "PASS"},
                                     ema_half_life_presentations=bad)
    except FixtureBridgeError:
        return
    pytest.fail(
        f"ema_half_life_presentations={bad!r} ({type(bad).__name__}) silently coerced to "
        f"{r['post_td_architecture_plan']['ema']['half_life_presentations']!r}; bridge "
        "type-checks candidate/qualifications exactly but not the EMA native unit"
    )


# --------------------------------------------------------------------------
# F5  mode-path receipt is a same-process self-comparison
# --------------------------------------------------------------------------

def test_defect_F5_mode_path_receipt_is_self_comparison(monkeypatch):
    calls = []
    real = bridge.trace_scientific_path

    def spy(**kwargs):
        calls.append(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(bridge, "trace_scientific_path", spy)
    r = stage_fixture_downstream(case_payload=_case(), stages=_stages())
    assert [c["mode"] for c in calls] == ["KNOWN_TRUTH", "HUMAN_SEALED"]
    assert calls[0]["stages"] is calls[1]["stages"]
    assert calls[0]["case_payload"] is calls[1]["case_payload"]
    assert r["mode_path_receipt"]["scientific_output_equivalence"] is not True, (
        "both 'modes' run the identical in-process stage tuple on the identical payload and "
        "handlers never see the mode, so equivalence is true by construction for any "
        "deterministic roster; the embedded A7-shaped receipt (producer/executor/validator "
        "identity sets) asserts scientific_output_equivalence=True without any independent "
        "HUMAN_SEALED execution"
    )


# --------------------------------------------------------------------------
# Boundaries verified to hold
# --------------------------------------------------------------------------

class _S(str):
    pass


class _D(dict):
    pass


@pytest.mark.parametrize("cand,q", [
    ("C1", {"C1": _S("PASS")}),
    ("C1", _D({"C1": "PASS"})),
    ("C1", {"C1": {"status": "PASS"}}),
    ("C1", {"C1": "pass"}),
    (_S("C1"), {"C1": "PASS"}),
    ("C1", {_S("C1"): "PASS"}),
    ("C5", {"C5": "PASS"}),
    ("c1", {"C1": "PASS"}),
])
def test_boundary_forged_pass_shapes_rejected(cand, q):
    with pytest.raises(FixtureBridgeError):
        stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                 fixture_candidate=cand, fixture_qualifications=q)


def test_boundary_no_output_claims_same_code_path_or_authority():
    outs = [
        stage_fixture_downstream(case_payload=_case(), stages=_stages()),
        stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                 fixture_candidate="C4",
                                 fixture_qualifications={k: "PASS" for k in
                                                         ("C1", "C2", "C3", "C4", "C6")}),
    ]
    for out in outs:
        for k, v in _walk(out):
            if "authoriz" in str(k).lower() or "authenticated" in str(k).lower():
                assert v is False, (k, v)
            assert not (isinstance(v, str) and "SAME_CODE_PATH" in v and "NO_AUTHORITY" not in v)
        assert out["authority_effect"] == "NONE"


def test_boundary_restored_modules_are_byte_identical_to_pr351_blobs():
    expected = {
        "scripts/v5/jepa_post_td_harness_contract_v1.py": "11b1b48e52883182db2889e78a75047011f23757",
        "scripts/v5/jepa_post_td_rehearsal_preflight_v1.py": "f4dc57cae1dbdd86ace1faec6e171eddde10c30f",
        "scripts/v5/jepa_post_td_tournament_controller_v1.py": "d4aee423902799cc5026c622217a701ac741ad48",
        "scripts/v5/jepa_post_td_presentation_ema_v1.py": "1e6126ce189f3ecdef799150541f3cc882c6eee7",
        "tests/v5/test_jepa_post_td_c4_requires_c6_v1.py": "2a03d268bc45a54001b915f52a10428b1f66aeda",
    }
    for rel, blob in expected.items():
        data = (ROOT / rel).read_bytes()
        got = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        assert got == blob, rel


_FORBIDDEN_IMPORTS = {"torch", "subprocess", "multiprocessing", "jax", "tensorflow", "pyro", "numpyro", "pymc"}
_FORBIDDEN_TOKENS = ("belief", "variational", "posterior", "negative_binomial", "nb_head",
                     "adaptive_cov", "elbo", "kl_div", "os.system", "popen", ".backward(")


@pytest.mark.parametrize("rel", [
    "scripts/v5/td_unified/post_td_fixture_bridge_v1.py",
    "scripts/v5/jepa_post_td_harness_contract_v1.py",
    "scripts/v5/jepa_post_td_rehearsal_preflight_v1.py",
    "scripts/v5/jepa_post_td_tournament_controller_v1.py",
    "scripts/v5/jepa_post_td_presentation_ema_v1.py",
])
def test_boundary_no_training_launch_or_bayesian_reentry(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").split(".")[0]]
        else:
            continue
        assert not (set(names) & _FORBIDDEN_IMPORTS), (rel, names)
    low = text.lower()
    assert not [t for t in _FORBIDDEN_TOKENS if t in low], rel


def test_boundary_bridge_never_imports_ema_or_runtime():
    src = (ROOT / "scripts/v5/td_unified/post_td_fixture_bridge_v1.py").read_text(encoding="utf-8")
    assert "presentation_ema" not in src and "src.sea_ad_jepa" not in src
    assert "advance_after_proved_optimizer_step" not in src


def test_boundary_teacher_evidence_existing_policy_preserved():
    measured, student, block, q = {1, 4, 5}, {1, 4}, {5}, 4
    assert H.derive_teacher_evidence_set(policy="SAME_EVIDENCE_CONTROL", measured_addresses=measured,
                                         student_visible_addresses=student, query_address=None,
                                         target_block_addresses=block) == frozenset(student)
    assert H.derive_teacher_evidence_set(policy="SAME_EVIDENCE_Q_BLIND_CONTROL",
                                         measured_addresses=measured, student_visible_addresses=student,
                                         query_address=q, target_block_addresses=block) == frozenset({1})
    assert 5 not in H.derive_teacher_evidence_set(policy="WHOLE_BLOCK_BLIND_CONDITIONAL",
                                                  measured_addresses=measured,
                                                  student_visible_addresses=student,
                                                  query_address=None, target_block_addresses=block)
    with pytest.raises(H.PostTDContractError):
        H.derive_teacher_evidence_set(policy="SAME_EVIDENCE_CONTROL", measured_addresses={1},
                                      student_visible_addresses={1, 2}, query_address=None,
                                      target_block_addresses=set())


def test_limitation_bridge_does_not_derive_teacher_evidence_from_case_support_states():
    """PR body says non-NONE cases 'exercise teacher ... policy'; only default policy
    NAMES are emitted.  No evidence set is derived from Task5 support states, so the
    WITHHELD_BY_EVIDENCE_RIGHTS / STRUCTURALLY_UNMEASURED exclusion is unexercised."""
    r = stage_fixture_downstream(case_payload=_case(), stages=_stages(),
                                 fixture_candidate="C1", fixture_qualifications={"C1": "PASS"})
    plan = r["post_td_architecture_plan"]
    assert plan["teacher_policies"] == {"C1_SHARED": "RICH_COMPLEMENTARY"}
    assert not any("ADDR" in repr(v) for _, v in _walk(r))


def test_limitation_c6_dependency_is_label_level_not_independent_receipt():
    shared = {"status": "PASS"}
    p = H.build_target_portfolio(selected_candidate="C4",
                                 qualifications={k: shared for k in ("C1", "C2", "C3", "C4", "C6")})
    assert p["fused_candidate"] == "C4"


def test_limitation_controller_has_no_typed_target_none_path():
    r = stage_fixture_downstream(case_payload=_case(), stages=_stages())
    with pytest.raises(AttributeError):
        T.build_zero_update_teacher_screen(r["post_td_portfolio"])


def test_boundary_new_integration_workflow_is_read_only():
    text = (ROOT / ".github/workflows/unified-task5-post-td-reuse-integration.yml").read_text(encoding="utf-8")
    low = text.lower()
    assert "permissions:\n  contents: read" in low
    for bad in ("contents: write", "write-all", "git push", "git commit",
                "create-pull-request", "pull_request_target"):
        assert bad not in low, bad
