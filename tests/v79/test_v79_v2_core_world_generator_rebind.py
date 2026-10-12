"""Canonical rebind and pre-realization scientific audit of the V2_CORE world generator.

Controller rebind ruling 6115340528, takeover audit V79_V2_CORE_WORLD_GENERATOR_CONTROLLER_AUDIT_20261011 (PR #291
312bb302), and world-generation authorizations 6115053096 and 6115121455.

- The sole authority is canonical Contract V2 57e19295..., obtained only through PR #290's
  v79_v2_core_launch.require_launch_authority(). The obsolete 8be47cb2... contract is refused everywhere.
- The Q10/Q11 pairing amendment is regenerated against the canonical contract with unchanged semantics.
- Donor-strength worlds rescale the realized donor-effect arrays: Q01/Q02 rescale, Q07 sets them to exactly zero.
- The detection intercept is solved after each world's modifications and support mask, over measured cells only.
- Source codes come from canonical metadata, not an assumed order.
- No competing finalization layer remains in the tree, no world artifact exists, and realize_worlds() stays closed.

Integrated world-truth tests use a TEST seed root on in-memory copies of the payload. The qualification root
(31000000) is never realized here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import generate_v79_v2_core_worlds as G  # noqa: E402
import v79_v2_core_launch as L  # noqa: E402

CANONICAL = "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
OBSOLETE = "8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d"
PAYLOAD_SHA = "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"
OLD_AMENDMENT_SHA = "09f60d91817a041badaa4fc5108125f02a02d1ebbe8242a0f012aa6978d56f7c"
TEST_ROOT = 4242
QDIR = ROOT / "results" / "v79" / "v2_core_qualification"
CAL = json.loads((ROOT / "results/v79/development/v2_core_planting_calibration/"
                         "V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json").read_text(encoding="utf-8"))
# The paired-counterfactual semantics frozen by controller comment 6114906562 (PR #291 amendment 09f60d91...),
# copied verbatim so the regenerated amendment can be checked for unchanged semantics.
FROZEN_PAIRING = {
    "parent_world": {"name": "Q10_S174_DESIGN_IMBALANCE", "world_index": 10},
    "child_world": {"name": "Q11_OMITTED_OPERATOR", "world_index": 11},
    "q11_inherits_q10_exactly": ["design", "structural_support_mask", "all_non_operator_planted_core_parameters",
                                 "donor_effects_and_shared_donor_factor", "factor_loading_assignment",
                                 "base_detection_observation_noise", "base_positive_observation_noise",
                                 "heldout_same_donor_base_noise", "new_donor_base_effects_and_noise"],
    "q11_new_randomness_only": {"operator_offsets_detection": 22, "operator_offsets_positive": 23},
    "effective_seed_parent_rule": "For Q11, every stream except 22 and 23 uses world_index=10; streams 22/23 retain world_index=11.",
    "common_random_numbers": True,
    "operator_offsets": {"distribution": "Normal(0, (0.5 x that gene donor SD)^2)", "centering": "unweighted within source",
                         "fitted": False},
    "truth_hash_rule": "Q10 and Q11 non-operator truth components must hash identically; only operator-offset fields may differ.",
    "all_q11_gates_remain": "HARD_FAIL",
}
FROZEN_AUTHORIZATION_FLAGS = {"world_realization": False, "benchmark": False, "qualification_fitting": False,
                              "real_train_posterior": False, "factorial_science": False, "training": False}


@pytest.fixture(scope="module")
def launch():
    return G.load_launch_contract(ROOT)


@pytest.fixture(scope="module")
def test_payload(launch):
    _, payload = launch
    p = copy.deepcopy(payload)
    p["seeds"]["root"] = TEST_ROOT                  # in-memory test copy only; the authority is never modified
    return p


@pytest.fixture(scope="module")
def designs(test_payload):
    return G.build_world_designs(ROOT, test_payload)


@pytest.fixture(scope="module")
def truths(test_payload, designs):
    amendment = G.load_pairing_amendment(ROOT)
    return {w["name"]: G.build_world_truth(test_payload, CAL, designs, w, amendment)
            for w in test_payload["worlds"]["world_list"]}


# ------------------------------------------------------------------------------------ canonical authority rebind
def test_generator_obtains_the_canonical_contract_only_through_the_launch_gate(launch):
    contract, payload = launch
    assert G.FINAL_CONTRACT_SHA256 == L.FINAL_CONTRACT_SHA256 == CANONICAL
    assert hashlib.sha256((QDIR / L.FINAL_CONTRACT_NAME).read_bytes()).hexdigest() == CANONICAL
    assert contract["status"] == L.FINAL_STATUS and contract["launch_authority"] is True
    assert G.QUALIFICATION_PAYLOAD_SHA256 == PAYLOAD_SHA
    assert contract["accepted_evidence"]["contract_v2_draft"]["sha256"] == PAYLOAD_SHA
    for key in ("worlds", "seeds", "gates", "priors", "model"):
        assert payload[key] == contract[key]
    src = (ROOT / "scripts" / "v79" / "generate_v79_v2_core_worlds.py").read_text(encoding="utf-8")
    assert "require_launch_authority" in src
    assert [ln for ln in src.splitlines() if OBSOLETE in ln] == \
        [ln for ln in src.splitlines() if ln.startswith("OBSOLETE_CONTRACT_SHA256")]


def test_obsolete_contract_is_refused_as_authority_everywhere(tmp_path):
    old = {"schema": "V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1", "controller_comment": 6114906562,
           "rebind_controller_comment": 6115340528, "final_contract_sha256": OBSOLETE,
           "qualification_payload_sha256": PAYLOAD_SHA, "worlds_generated_at_freeze": 0,
           "qualification_fits_at_freeze": 0, "paired_counterfactual": FROZEN_PAIRING,
           "authorization": FROZEN_AUTHORIZATION_FLAGS}
    with pytest.raises(SystemExit):
        G.validate_pairing_amendment_content(old)
    auth = {"schema": G.REALIZATION_AUTH_SCHEMA, "final_contract_sha256": OBSOLETE,
            "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256, "world_generation_authorized": True,
            "qualification_fitting_authorized": False, "generator_code_head": "0" * 40,
            "generator_green_ci": {"passed": True}}
    with pytest.raises(SystemExit):
        G.validate_realization_authorization(auth)
    with pytest.raises(SystemExit):
        G.build_manifest(world_name="Q00_BASELINE", world_index=0, truth={"x": 1}, final_contract_sha=OBSOLETE,
                         payload_sha=PAYLOAD_SHA, generated_files={})
    fake = tmp_path / L.FINAL_CONTRACT_NAME                       # an obsolete-contract file under the final name
    fake.write_bytes(b'{"schema": "obsolete"}\n')
    fake.with_suffix(".sha256").write_text(f"{hashlib.sha256(fake.read_bytes()).hexdigest()}  {fake.name}\n")
    with pytest.raises(L.LaunchAuthorityRefused):
        L.require_launch_authority(fake)


def test_pairing_amendment_is_regenerated_against_the_canonical_contract_with_unchanged_semantics():
    a = G.load_pairing_amendment(ROOT)
    assert a["schema"] == "V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1"
    assert a["final_contract_sha256"] == CANONICAL
    assert a["qualification_payload_sha256"] == PAYLOAD_SHA
    assert a["controller_comment"] == 6114906562 and a["rebind_controller_comment"] == 6115340528
    assert a["paired_counterfactual"] == FROZEN_PAIRING
    assert a["authorization"] == FROZEN_AUTHORIZATION_FLAGS
    assert a["supersedes"] == {"amendment_sha256": OLD_AMENDMENT_SHA, "bound_final_contract_sha256": OBSOLETE,
                               "reason": "bound to the non-canonical PR #289 contract line; semantics unchanged"}
    assert a["worlds_generated_at_freeze"] == 0 and a["qualification_fits_at_freeze"] == 0
    path = ROOT / G.PAIRING_AMENDMENT_REL
    assert hashlib.sha256(path.read_bytes()).hexdigest() == G.PAIRING_AMENDMENT_SHA256 != OLD_AMENDMENT_SHA


def test_pairing_amendment_builder_regenerates_byte_for_byte():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "v79" / "build_v79_v2_core_pairing_amendment.py"),
                        str(ROOT), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    assert G.PAIRING_AMENDMENT_SHA256 in r.stdout


# ------------------------------------------------------------------------------------------ source code mapping
def test_source_codes_match_canonical_design_metadata():
    assert G.source_code_mapping(ROOT) == G.SOURCE_CODES == {"HVS": 0, "NPH52": 1, "SEA_AD": 2}


# ---------------------------------------------------------------------------------------- donor-effect rescaling
def test_baseline_donor_effects_use_the_canonical_latent_field(truths):
    for part in ("detection", "positive"):
        t = truths["Q00_BASELINE"][part]
        assert np.allclose(t["donor_effects"], t["donor_raw_centered"] * t["donor_sd"][None, :], atol=0, rtol=0)


@pytest.mark.parametrize("world,key", [("Q01_WEAK_DONOR", "weak_donor_sd"), ("Q02_STRONG_DONOR", "strong_donor_sd")])
def test_donor_strength_worlds_rescale_the_realized_effects(test_payload, truths, world, key):
    fm = test_payload["worlds"]["planting_magnitudes"]["fixed_magnitudes"][key]
    base = truths["Q00_BASELINE"]
    for part in ("detection", "positive"):
        t = truths[world][part]
        assert np.all(t["donor_sd"] == fm[part])
        assert np.array_equal(t["donor_effects"], t["donor_raw_centered"] * fm[part])
        assert np.array_equal(t["donor_raw_centered"], base[part]["donor_raw_centered"])   # same latent draws
        ratio = t["donor_effects"].std(axis=0) / base[part]["donor_effects"].std(axis=0)
        assert np.allclose(ratio, fm[part] / base[part]["donor_sd"], rtol=1e-12)
    assert not np.allclose(truths[world]["detection"]["donor_effects"], base["detection"]["donor_effects"])


def test_donor_absent_world_has_exactly_zero_donor_effects(truths):
    for part in ("detection", "positive"):
        t = truths["Q07_DONOR_ABSENT"][part]
        assert np.all(t["donor_sd"] == 0) and np.count_nonzero(t["donor_effects"]) == 0


def test_rescale_refuses_a_truth_object_without_the_canonical_latent_field(test_payload):
    w = {x["name"]: x for x in test_payload["worlds"]["world_list"]}["Q01_WEAK_DONOR"]
    part = {"donor_sd": np.ones(3), "donor_effects": np.ones((4, 3))}
    truth = {"detection": dict(part), "positive": dict(part, sigma=np.ones(3))}
    with pytest.raises(SystemExit):
        G.apply_world_modifications(truth, w, test_payload)


# --------------------------------------------------------------------------- per-world detection intercept solve
def test_every_world_hits_its_planted_prevalence_over_measured_cells(designs, truths):
    for name, t in truths.items():
        d = designs[name]
        nonint = G.detection_nonintercept_predictor(d, t["detection"])
        p = 1.0 / (1.0 + np.exp(-np.clip(t["detection"]["intercept"][None, :] + nonint, -40, 40)))
        achieved = np.array([p[t["support"][:, g], g].mean() for g in range(p.shape[1])])
        assert np.all(np.abs(achieved - t["detection"]["prevalence"]) < 1e-10), name


def test_sparse_world_realizes_its_sparse_prevalence(truths):
    t = truths["Q08_SPARSE_DETECTION"]["detection"]
    assert np.all((t["prevalence"] >= 0.005) & (t["prevalence"] <= 0.05))
    assert np.all(t["intercept"] < truths["Q00_BASELINE"]["detection"]["intercept"].max())


def test_intercepts_are_solved_after_modifications(truths):
    q00, q04 = truths["Q00_BASELINE"]["detection"], truths["Q04_SOURCE_ABSENT"]["detection"]
    assert np.array_equal(q04["prevalence"], q00["prevalence"])      # same planted target, different predictor
    assert not np.allclose(q04["intercept"], q00["intercept"])


def test_unmeasured_cells_never_enter_the_intercept_solve(designs, truths):
    d, t = designs["Q00_BASELINE"], truths["Q00_BASELINE"]
    g = int(np.where(~t["support"].all(axis=0))[0][0])
    nonint = G.detection_nonintercept_predictor(d, t["detection"])[:, g]
    a1 = G.solve_detection_intercept_for_gene(nonint, t["support"][:, g], t["detection"]["prevalence"][g])
    poisoned = nonint.copy(); poisoned[~t["support"][:, g]] = 37.0
    a2 = G.solve_detection_intercept_for_gene(poisoned, t["support"][:, g], t["detection"]["prevalence"][g])
    assert a1 == a2 == t["detection"]["intercept"][g]


# ------------------------------------------------------------------------------------- structural support + Q11
def test_structural_support_composition_in_every_world(truths, designs):
    for name, t in truths.items():
        s, src = t["support"], designs[name]["src"]
        affected = np.where(~s.all(axis=0))[0]
        assert len(affected) == 5, name
        kinds = []
        for g in affected:
            measured = [bool(s[src == c, g].any()) for c in range(3)]
            full = [bool(s[src == c, g].all()) for c in range(3)]
            kinds.append("single" if sum(measured) == 1 else "absent" if sum(full) == 2 and sum(measured) == 2
                         else "partial")
        assert sorted(kinds) == ["absent", "absent", "absent", "partial", "single"], name


def test_q11_inherits_q10_except_operator_offsets(truths):
    q10, q11 = truths["Q10_S174_DESIGN_IMBALANCE"], truths["Q11_OMITTED_OPERATOR"]
    assert np.array_equal(q10["support"], q11["support"])
    for part in ("detection", "positive"):
        for k, v in q10[part].items():
            assert np.array_equal(np.asarray(v), np.asarray(q11[part][k])), (part, k)
    assert q10["operator_offsets"] is None and q11["operator_offsets"] is not None
    assert G.non_operator_truth_sha(q10) == G.non_operator_truth_sha(q11)


# --------------------------------------------------------------------------------------- firewalls on this head
def test_no_competing_finalization_layer_remains():
    for rel in ("scripts/v79/finalize_v79_v2_core_contract.py", "scripts/v79/validate_v79_v2_core_launch_contract.py",
                "tests/v79/test_v79_v2_core_contract_finalization.py",
                ".github/workflows/v79-v2-core-contract-finalization.yml"):
        assert not (ROOT / rel).exists(), rel
    for rel in ("scripts/v79/v79_v2_core_launch.py", "tests/v79/test_v79_v2_core_launch_authority.py",
                "results/v79/v2_core_qualification/finalization/FINALIZATION_RECEIPT.json",
                "results/v79/v2_core_qualification/finalization/LAUNCH_AUTHORITY_VALIDATION_RECEIPT.json"):
        assert (ROOT / rel).is_file(), rel


def test_no_world_artifacts_exist():
    assert not list((ROOT / "results" / "v79").glob("v2_core_worlds*"))
    for pattern in ("**/WORLD_DATA*", "**/TRUTH*.json", "**/*_WORLD_MANIFEST*"):
        assert not list((ROOT / "results" / "v79").glob(pattern)), pattern


def test_realization_stays_disabled_even_with_a_canonical_authorization(test_payload, designs):
    auth = {"schema": G.REALIZATION_AUTH_SCHEMA, "final_contract_sha256": CANONICAL,
            "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256, "world_generation_authorized": True,
            "qualification_fitting_authorized": False, "generator_code_head": "0" * 40,
            "generator_green_ci": {"passed": True}}
    with pytest.raises(SystemExit, match="not yet controller-audited"):
        G.realize_worlds(test_payload, designs["Q00_BASELINE"], Path("unused"), auth)
