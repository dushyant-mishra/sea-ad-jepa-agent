"""Hostile custody tests for production synthetic V3.1.1 Task 2.

Each test is an attack the custody layer must refuse: integer-offset seed
namespaces, seed replacement/discard/shopping, re-emission, early or mismatched
reveal, easier post-exposure successors (E1) including changed frozen
components, laundering through unexposed intermediates, use of superseded
versions, a withheld commitment not bound to the qualification nonce (E2),
withheld plaintext in public config, unique withheld-only public code paths
(N3), echoing of supplied names, and hand-forged ledgers.

All secrets are DUMMY values generated in-test; nothing here is a production
secret. Files are written only under pytest ``tmp_path``.
"""
import hashlib
import secrets

import numpy as np
import pytest

import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
from scripts.production_synthetic.custody_v1 import CustodyError

QUAL = "SYNTH_QUALIFICATION"
DEBUG = "SYNTH_DEBUG"
WTAG = "SYNTH_QUALIFICATION_WITHHELD"
ENTRY_FORMAT = "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-ENTRY-V1"
LEDGER_FORMAT = "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-V1"
E1_COMPONENTS = [
    "generator_source", "transitive_dependencies", "parameter_distributions", "mechanism_mixture",
    "observation_calibration_distributions", "stress_regimes", "applicability_control_matrix", "registries",
    "serialization_contract", "realization_budgets",
]

DUMMY_WITHHELD_SPEC = {
    "DUMMY_family": {"composition": "DUMMY_pair_of_shared_programs", "weight": 0.125},
    "DUMMY_scoring_rule": "DUMMY",
    "DUMMY_budget": 2,
}


def _h(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# DUMMY method identities: content digests of fixture methods' frozen code + configuration
METHOD = _h("DUMMY fixture method: code + configuration")
METHOD_A = _h("DUMMY method A: code + configuration")
METHOD_A_RENAMED = _h("DUMMY method A, relabelled v2: code + configuration")
METHOD_B = _h("DUMMY method B: code + configuration")


def dummy_nonce():
    """DUMMY 256-bit nonce, freshly generated per call; never a production secret."""
    return secrets.token_bytes(32)


def _chain_text(exc):
    """Every message a traceback of ``exc`` would display (cause/context chain included)."""
    out = []
    e = exc
    while e is not None:
        out.append(f"{type(e).__name__}: {e}")
        e = e.__cause__ if e.__cause__ is not None else (None if e.__suppress_context__ else e.__context__)
    return "\n".join(out)


def base_spec():
    return {
        "generator_source": {"scripts/production_synthetic/fixture_generator.py": _h("fixture-src")},
        "transitive_dependencies": {"numpy==2.4.6": _h("numpy-wheel")},
        "parameter_distributions": {"library_size": {"law": "lognormal", "mu": 8.0, "sigma": 0.5}},
        "mechanism_mixture": {"weights": {"program_a": 0.4, "program_b": 0.4, "novelty_program": 0.2}},
        "observation_calibration_distributions": {"dropout": {"law": "beta", "a": 2.0, "b": 5.0}},
        "difficulty_grid": {
            "signal_to_noise": {"level": 0.5, "harder_direction": "decreasing"},
            "rare_state_fraction": {"level": 0.01, "harder_direction": "decreasing"},
            "confounding_strength": {"level": 2, "harder_direction": "increasing"},
        },
        "stress_regimes": {"depth_collapse": {"depth_scale": 0.25}, "batch_shift": {"shift": 1.5}},
        "challenge_families": {
            "adverse_regimes": ["depth_collapse", "batch_shift"],
            "control_families": ["label_permutation", "matched_null"],
            "support_challenges": ["structural_unmeasured_block"],
            "population_imbalance_challenges": ["rare_state_1pct"],
            "novelty_regimes": ["out_of_basis_program"],
            "measurement_challenges": ["collision_unresolved"],
        },
        "applicability_control_matrix": {"matched_null": ["all_targets", "rare_targets"]},
        "registries": {"address_registry": _h("addr"), "modality_namespace_registry": _h("mod")},
        "serialization_contract": {"canonical_module": "canonical_v1", "format_version": 1},
        "realization_budgets": {DEBUG: 3, QUAL: 4},
    }


def make_world(edit=None, withheld=DUMMY_WITHHELD_SPEC, commitment_nonce=None):
    """Freeze a fixture generator; the E2 commitment uses the returned SYNTH_QUALIFICATION nonce."""
    spec = base_spec()
    if edit is not None:
        edit(spec)
    qnonce = dummy_nonce()
    pre = CU.generator_precommitment_semantic_hash(spec)
    spec["withheld_family_commitment"] = CU.withheld_family_commitment(
        commitment_nonce if commitment_nonce is not None else qnonce, withheld, pre, WTAG)
    return CU.freeze_generator_version(spec), qnonce


def make_tree(tmp_path, name="tree"):
    tree = tmp_path / name
    (tree / "scripts").mkdir(parents=True)
    (tree / "scripts" / "public_mechanism.py").write_bytes(b"def shared_kernel(x):\n    return x\n")
    return tree


def code_path_attestation():
    return CU.attest_no_unique_withheld_code_path(
        withheld_exercised_paths={"m.py::shared_kernel"},
        development_exercised_paths={"m.py::shared_kernel", "m.py::dev_only"},
        public_code_paths={"m.py::shared_kernel", "m.py::dev_only"},
    )


def emit(root, class_tag, budget):
    rows = []
    for rid in CU.authorized_realization_ids(root, class_tag, budget):
        rng = CU.derive_stream(root, ("world_id", rid), ("purpose_tag", "fixture_content"))
        rows.append({"realization_id": rid, "content_sha256": C.raw_sha256(rng.bytes(32))})
    return rows


def commit_withheld(freeze, qnonce, ledger, tree, change=None):
    scans = [CU.require_secret_absence(tree, qnonce)]
    CU.record_withheld_commitment(freeze, ledger, withheld_class_tag=WTAG, nonce_commitment=CU.nonce_commitment(qnonce),
                                  secret_absence_attestations=scans, code_path_attestation=code_path_attestation(),
                                  withheld_family_change=change)


def commit_and_attest(freeze, qnonce, ledger, tree, attest=True, change=None):
    nonces = {DEBUG: dummy_nonce(), QUAL: qnonce}
    for tag in (DEBUG, QUAL):
        CU.record_nonce_commitment(freeze, ledger, class_tag=tag, nonce_commitment=CU.nonce_commitment(nonces[tag]))
    commit_withheld(freeze, qnonce, ledger, tree, change)
    out = {}
    for tag in (DEBUG, QUAL):
        budget = freeze.realization_budget(tag)
        root = CU.sealed_root(nonces[tag], freeze.generator_semantic_hash, tag, budget)
        out[tag] = (nonces[tag], root)
        if attest:
            CU.attest_realization_set(root, tag, budget, emit(root, tag, budget), ledger, freeze=freeze)
    return out


def prepare(freeze, qnonce, ledger, tree, attest=True):
    CU.record_generator_freeze(freeze, ledger)
    return commit_and_attest(freeze, qnonce, ledger, tree, attest)


def expose(freeze, ledger, class_tag=DEBUG, exposure_id="exp-1"):
    return CU.record_exposure(
        freeze, {"exposure_id": exposure_id, "method_id": METHOD, "realization_class": class_tag}, ledger
    )


def successor(parent, child, ledger, defect_record=None):
    return CU.validate_successor_version(
        parent, child, parent_exposure_state=CU.exposure_state(parent, ledger), ledger=ledger,
        defect_record=defect_record,
    )


def defect(parent, child, affected=(), components=(), **over):
    rec = {
        "parent_generator_semantic_hash": parent.generator_semantic_hash,
        "child_generator_semantic_hash": child.generator_semantic_hash,
        "defect_description": "DUMMY: fixture generator violated its frozen design contract",
        "affected_dimensions": list(affected),
        "affected_components": list(components),
        "generator_side_evidence_sha256": _h("DUMMY generator-side evidence"),
        "justification_source": "GENERATOR_DEFECT_AGAINST_FROZEN_SPEC",
        "incomparable": False,
    }
    rec.update(over)
    return rec


def set_snr(level):
    def edit(spec):
        spec["difficulty_grid"]["signal_to_noise"]["level"] = level  # decreasing is harder
    return edit


@pytest.fixture
def exposed_parent(tmp_path):
    parent, qnonce = make_world()
    led = CU.CustodyLedger()
    prepare(parent, qnonce, led, make_tree(tmp_path))
    expose(parent, led)
    return parent, led


@pytest.fixture
def committed(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    roots = prepare(fr, qnonce, led, make_tree(tmp_path), attest=False)
    return fr, led, roots, qnonce


@pytest.fixture
def exposed_qual(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    roots = prepare(fr, qnonce, led, make_tree(tmp_path))
    expose(fr, led, QUAL)
    return fr, led, roots, qnonce


# ------------------------------------------------- integer seed namespaces

@pytest.mark.parametrize("root", [
    12345,
    np.uint64(7),
    "00" * 32,
    b"\x00" * 32,
    (42).to_bytes(32, "big"),
    (2**200 + 5).to_bytes(32, "big"),
    bytes(31) + b"\x01",
    secrets.token_bytes(31),
    secrets.token_bytes(33),
    bytearray(secrets.token_bytes(32)),
    None,
])
def test_stream_root_rejects_integer_seeds_and_non_root_forms(root):
    with pytest.raises(CustodyError):
        CU.derive_stream(root, ("world_id", "w0"), ("purpose_tag", "noise"))


@pytest.mark.parametrize("part", [
    ("cell_id", 7),
    ("cell_id", np.int64(7)),
    ("cell_id", True),
    ("cell_id", 7.0),
    ("cell_id", ""),
    ("cell_id", b"c1"),
    ("cell_id", None),
    ("seed", "1"),
    ("seed_offset", "1"),
    ("offset", "3"),
    ("index", "0"),
    ("CELL_ID", "c1"),
    ("cell_id",),
    ("cell_id", "c1", "extra"),
    "cell_id=c1",
    ("cell_id", "c\r1"),
    ("cell_id", "c\n1"),
])
def test_stream_identity_rejects_integer_offsets_and_unknown_keys(part):
    with pytest.raises(CustodyError):
        CU.derive_stream(secrets.token_bytes(32), ("world_id", "w0"), ("purpose_tag", "noise"), part)


def test_stream_identity_rejects_duplicate_keys():
    root = secrets.token_bytes(32)
    with pytest.raises(CustodyError):
        CU.derive_stream(root, ("world_id", "w0"), ("purpose_tag", "a"), ("purpose_tag", "b"))
    with pytest.raises(CustodyError):
        CU.derive_stream(root, ("world_id", "w0"), ("purpose_tag", "a"), ("cell_id", "c1"), ("cell_id", "c1"))


@pytest.mark.parametrize("tag", ["DEV", "SEALED", "SYNTH_SEALED", "SYNTH_DEV", "synth_qualification", "QUAL", ""])
def test_class_tags_reject_real_partition_names(tag):
    with pytest.raises(CustodyError):
        CU.sealed_root(dummy_nonce(), _h("g"), tag, 4)


# ------------------------------------------------ seed replacement and reuse

def test_committed_nonce_cannot_be_replaced(committed):
    fr, led, _, _ = committed
    with pytest.raises(CustodyError):
        CU.record_nonce_commitment(fr, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(dummy_nonce()))
    with pytest.raises(CustodyError):
        CU.record_nonce_commitment(fr, led, class_tag=DEBUG, nonce_commitment=CU.nonce_commitment(dummy_nonce()))


def test_nonce_cannot_be_reused_across_classes():
    fr, _ = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(fr, led)
    n = dummy_nonce()
    CU.record_nonce_commitment(fr, led, class_tag=DEBUG, nonce_commitment=CU.nonce_commitment(n))
    with pytest.raises(CustodyError):
        CU.record_nonce_commitment(fr, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(n))


def test_nonce_cannot_be_reused_by_a_successor_version(exposed_parent):
    parent, led = exposed_parent
    child, _ = make_world(set_snr(0.3))
    successor(parent, child, led)
    CU.record_generator_freeze(child, led)
    reused = [e["payload"]["nonce_commitment"] for e in led.entries() if e["kind"] == "NONCE_COMMITTED"][0]
    with pytest.raises(CustodyError):
        CU.record_nonce_commitment(child, led, class_tag=QUAL, nonce_commitment=reused)


def test_nonce_commitment_after_exposure_is_refused(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(fr, led)
    CU.record_nonce_commitment(fr, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(qnonce))
    commit_withheld(fr, qnonce, led, make_tree(tmp_path))
    rq = CU.sealed_root(qnonce, fr.generator_semantic_hash, QUAL, 4)
    CU.attest_realization_set(rq, QUAL, 4, emit(rq, QUAL, 4), led, freeze=fr)
    expose(fr, led, QUAL)
    with pytest.raises(CustodyError):
        CU.record_nonce_commitment(fr, led, class_tag=DEBUG, nonce_commitment=CU.nonce_commitment(dummy_nonce()))


# ------------------------------------- discard, seed shopping, re-emission

def test_discarded_realization_is_refused(committed):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    with pytest.raises(CustodyError, match="discard"):
        CU.attest_realization_set(root, QUAL, 4, emit(root, QUAL, 4)[:-1], led, freeze=fr)


def test_seed_shopped_extra_or_replaced_realization_is_refused(committed):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    rows = emit(root, QUAL, 4)
    extra = emit(root, QUAL, 5)[4]
    with pytest.raises(CustodyError, match="seed shopping"):
        CU.attest_realization_set(root, QUAL, 4, rows + [extra], led, freeze=fr)
    shopped = emit(secrets.token_bytes(32), QUAL, 1)[0]
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, rows[:-1] + [shopped], led, freeze=fr)


def test_duplicate_realization_id_or_copied_content_is_refused(committed):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    rows = emit(root, QUAL, 4)
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, rows + [rows[0]], led, freeze=fr)
    copied = [dict(r) for r in rows]
    copied[3]["content_sha256"] = copied[2]["content_sha256"]  # failed world replaced by a copy
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, copied, led, freeze=fr)


@pytest.mark.parametrize("budget", [3, 5])
def test_budget_must_equal_the_frozen_budget(committed, budget):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, budget, emit(root, QUAL, budget), led, freeze=fr)


def test_re_emission_after_attestation_is_refused(committed):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    rows = emit(root, QUAL, 4)
    CU.attest_realization_set(root, QUAL, 4, rows, led, freeze=fr)
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, rows, led, freeze=fr)
    replacement = [dict(r, content_sha256=_h("re-drawn " + r["realization_id"])) for r in rows]
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, replacement, led, freeze=fr)
    other_root = CU.sealed_root(dummy_nonce(), fr.generator_semantic_hash, QUAL, 4)
    with pytest.raises(CustodyError, match="re-emission"):
        CU.attest_realization_set(other_root, QUAL, 4, emit(other_root, QUAL, 4), led, freeze=fr)


def test_one_root_cannot_back_two_classes(committed):
    fr, led, roots, _ = committed
    root = roots[DEBUG][1]
    CU.attest_realization_set(root, DEBUG, 3, emit(root, DEBUG, 3), led, freeze=fr)
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, emit(root, QUAL, 4), led, freeze=fr)


def test_attestation_requires_committed_nonce():
    fr, _ = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(fr, led)
    root = CU.sealed_root(dummy_nonce(), fr.generator_semantic_hash, QUAL, 4)
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, emit(root, QUAL, 4), led, freeze=fr)


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(extra="x"),
    lambda r: r.pop("content_sha256"),
    lambda r: r.update(content_sha256="not-hex"),
    lambda r: r.update(realization_id=7),
])
def test_emitted_row_shape_is_strict(committed, mutate):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    rows = emit(root, QUAL, 4)
    mutate(rows[1])
    with pytest.raises(CustodyError):
        CU.attest_realization_set(root, QUAL, 4, rows, led, freeze=fr)


def test_seed_shopping_with_an_uncommitted_nonce_is_caught_at_reveal(committed):
    fr, led, roots, _ = committed
    committed_nonce = roots[QUAL][0]
    shopped_nonce = dummy_nonce()
    shopped_root = CU.sealed_root(shopped_nonce, fr.generator_semantic_hash, QUAL, 4)
    CU.attest_realization_set(shopped_root, QUAL, 4, emit(shopped_root, QUAL, 4), led, freeze=fr)
    expose(fr, led, QUAL)
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit"))
    with pytest.raises(CustodyError):
        CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=committed_nonce)
    with pytest.raises(CustodyError):
        CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=shopped_nonce)


# ------------------------------------------------------------ reveal custody

def test_reveal_before_fit_output_frozen_is_refused(exposed_qual):
    fr, led, roots, qnonce = exposed_qual
    with pytest.raises(CustodyError):
        CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=qnonce)
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce, withheld_class_tag=WTAG)


def test_fit_output_cannot_be_frozen_before_exposure(committed):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    CU.attest_realization_set(root, QUAL, 4, emit(root, QUAL, 4), led, freeze=fr)
    with pytest.raises(CustodyError):
        CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit"))


def test_fit_output_is_frozen_once(exposed_qual):
    fr, led, _, _ = exposed_qual
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit"))
    with pytest.raises(CustodyError):
        CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("refit"))


def test_reveal_mismatch_and_alternative_withheld_draw_are_hard_failures(exposed_qual):
    fr, led, roots, qnonce = exposed_qual
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit"))
    with pytest.raises(CustodyError):
        CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=dummy_nonce())
    alternative = dict(DUMMY_WITHHELD_SPEC, DUMMY_budget=3)
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=alternative, nonce=qnonce, withheld_class_tag=WTAG)
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=dummy_nonce(),
                                  withheld_class_tag=WTAG)
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce,
                                  withheld_class_tag="SYNTH_QUALIFICATION_OTHER")
    CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=qnonce)
    CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce, withheld_class_tag=WTAG)
    with pytest.raises(CustodyError):
        CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=qnonce)
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce, withheld_class_tag=WTAG)


def test_withheld_reveal_requires_the_qualification_fit_to_be_frozen(exposed_qual):
    fr, led, roots, qnonce = exposed_qual
    expose(fr, led, DEBUG, "exp-debug")
    CU.record_fit_output_frozen(fr, led, class_tag=DEBUG, fit_output_sha256=_h("debug fit"))
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce, withheld_class_tag=WTAG)


def test_no_qualification_exposure_after_reveal(exposed_qual):
    fr, led, roots, qnonce = exposed_qual
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit"))
    CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=qnonce)
    with pytest.raises(CustodyError):
        expose(fr, led, QUAL, "exp-after-reveal")


# ------------------------------- B3 / E2: withheld nonce = qualification nonce

def test_withheld_commitment_requires_and_binds_the_prior_qualification_nonce(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    tree = make_tree(tmp_path)
    CU.record_generator_freeze(fr, led)
    with pytest.raises(CustodyError):
        commit_withheld(fr, qnonce, led, tree)  # qualification nonce not yet committed
    dnonce = dummy_nonce()
    CU.record_nonce_commitment(fr, led, class_tag=DEBUG, nonce_commitment=CU.nonce_commitment(dnonce))
    with pytest.raises(CustodyError):
        commit_withheld(fr, dnonce, led, tree)  # only a debug nonce exists
    CU.record_nonce_commitment(fr, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(qnonce))
    with pytest.raises(CustodyError):
        commit_withheld(fr, dnonce, led, tree)  # declares the debug nonce
    commit_withheld(fr, qnonce, led, tree)
    payload = [e["payload"] for e in led.entries() if e["kind"] == "WITHHELD_COMMITTED"][0]
    assert payload["nonce_commitment"] == CU.nonce_commitment(qnonce)


def test_withheld_commitment_built_with_the_debug_nonce_is_rejected(tmp_path):
    debug_nonce = dummy_nonce()
    fr, qnonce = make_world(commitment_nonce=debug_nonce)  # P3: commitment uses the debug nonce
    led = CU.CustodyLedger()
    tree = make_tree(tmp_path)
    CU.record_generator_freeze(fr, led)
    CU.record_nonce_commitment(fr, led, class_tag=DEBUG, nonce_commitment=CU.nonce_commitment(debug_nonce))
    CU.record_nonce_commitment(fr, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(qnonce))
    with pytest.raises(CustodyError):
        commit_withheld(fr, debug_nonce, led, tree)  # its true nonce is not the qualification nonce
    commit_withheld(fr, qnonce, led, tree)  # a false declaration passes the commit check ...
    for tag, n in ((DEBUG, debug_nonce), (QUAL, qnonce)):
        budget = fr.realization_budget(tag)
        root = CU.sealed_root(n, fr.generator_semantic_hash, tag, budget)
        CU.attest_realization_set(root, tag, budget, emit(root, tag, budget), led, freeze=fr)
        expose(fr, led, tag, "exp-" + tag)
        CU.record_fit_output_frozen(fr, led, class_tag=tag, fit_output_sha256=_h("fit " + tag))
    CU.reveal_class_nonce(fr, led, class_tag=DEBUG, nonce=debug_nonce)  # a debug reveal opens nothing withheld
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=debug_nonce,
                                  withheld_class_tag=WTAG)
    with pytest.raises(CustodyError):  # ... and the commitment can never be opened: hard failure
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce, withheld_class_tag=WTAG)


def test_qualification_nonce_cannot_leak_through_another_reveal_path(exposed_qual):
    fr, led, roots, qnonce = exposed_qual
    expose(fr, led, DEBUG, "exp-debug")
    CU.record_fit_output_frozen(fr, led, class_tag=DEBUG, fit_output_sha256=_h("debug fit"))
    with pytest.raises(CustodyError):
        CU.reveal_class_nonce(fr, led, class_tag=DEBUG, nonce=qnonce)
    with pytest.raises(CustodyError):
        CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce, withheld_class_tag=WTAG)
    assert not any(e["kind"] == "REVEALED" for e in led.entries())


# ---------------------------------------------- E1: easier exposed successors

EASIER_EDITS = {
    "level_relaxed": lambda s: s["difficulty_grid"]["confounding_strength"].update(level=1),
    "dimension_removed": lambda s: s["difficulty_grid"].pop("rare_state_fraction"),
    "direction_flipped": lambda s: s["difficulty_grid"]["signal_to_noise"].update(harder_direction="increasing"),
    "adverse_regime_removed": lambda s: s["challenge_families"]["adverse_regimes"].remove("batch_shift"),
    "control_family_removed": lambda s: s["challenge_families"]["control_families"].remove("matched_null"),
    "support_challenge_removed": lambda s: s["challenge_families"]["support_challenges"].clear(),
    "imbalance_challenge_removed": lambda s: s["challenge_families"]["population_imbalance_challenges"].clear(),
    "novelty_regime_removed": lambda s: s["challenge_families"]["novelty_regimes"].clear(),
    "measurement_challenge_removed": lambda s: s["challenge_families"]["measurement_challenges"].clear(),
}

COMPONENT_PROBES = {
    "novelty_weight_zero": (
        "mechanism_mixture", lambda s: s["mechanism_mixture"]["weights"].update(novelty_program=0.0)),
    "dropout_beta_2_5_to_1_50": (
        "observation_calibration_distributions",
        lambda s: s["observation_calibration_distributions"]["dropout"].update(a=1.0, b=50.0)),
    "control_matrix_shrunk": (
        "applicability_control_matrix",
        lambda s: s["applicability_control_matrix"]["matched_null"].remove("rare_targets")),
    "library_sigma_0_5_to_0_01": (
        "parameter_distributions", lambda s: s["parameter_distributions"]["library_size"].update(sigma=0.01)),
    "qualification_budget_4_to_1": ("realization_budgets", lambda s: s["realization_budgets"].update({QUAL: 1})),
    "debug_budget_removed": ("realization_budgets", lambda s: s["realization_budgets"].pop(DEBUG)),
    "generator_source_changed": (
        "generator_source",
        lambda s: s["generator_source"].update({"scripts/production_synthetic/fixture_generator.py": _h("edited")})),
    "dependency_added": (
        "transitive_dependencies", lambda s: s["transitive_dependencies"].update({"scipy==1.14.1": _h("scipy")})),
    "registry_changed": ("registries", lambda s: s["registries"].update(address_registry=_h("addr-v2"))),
    "serialization_changed": ("serialization_contract", lambda s: s["serialization_contract"].update(format_version=2)),
    "stress_regime_added": ("stress_regimes", lambda s: s["stress_regimes"].update(new_regime={"x": 1})),
    "stress_regime_relaxed": (
        "stress_regimes", lambda s: s["stress_regimes"]["depth_collapse"].update(depth_scale=0.9)),
    "stress_regime_removed": ("stress_regimes", lambda s: s["stress_regimes"].pop("batch_shift")),
}


@pytest.mark.parametrize("name", list(EASIER_EDITS))
def test_easier_exposed_successor_without_defect_record_is_refused(exposed_parent, name):
    parent, led = exposed_parent
    child, _ = make_world(EASIER_EDITS[name])
    n_before = len(led)
    with pytest.raises(CustodyError):
        successor(parent, child, led)
    assert len(led) == n_before  # nothing was recorded
    with pytest.raises(CustodyError):
        CU.record_generator_freeze(child, led)


@pytest.mark.parametrize("probe", list(COMPONENT_PROBES))
def test_changed_frozen_component_after_exposure_requires_a_covering_defect_record(exposed_parent, probe):
    component, edit = COMPONENT_PROBES[probe]
    parent, led = exposed_parent
    child, _ = make_world(edit)
    n_before = len(led)
    with pytest.raises(CustodyError):
        successor(parent, child, led)  # would otherwise read as SUCCESSOR_NOT_EASIER
    with pytest.raises(CustodyError):
        successor(parent, child, led, defect(parent, child, components=[c for c in E1_COMPONENTS if c != component]))
    assert len(led) == n_before
    disp = successor(parent, child, led, defect(parent, child, components=[component]))
    assert disp.disposition == "POST_EXPOSURE_VERSION"
    assert disp.changed_components == (component,)
    assert disp.inherits_qualification is False and disp.requires_realism_rerun is True


@pytest.mark.parametrize("source", ["DOWNSTREAM_METHOD_FAILURE", "METHOD_PERFORMANCE",
                                    "REGIME_IMPLICATED_IN_METHOD_FAILURE", "", None])
def test_defect_record_justified_by_method_failure_is_refused(exposed_parent, source):
    parent, led = exposed_parent
    child, _ = make_world(set_snr(0.9))
    rec = defect(parent, child, ["difficulty_grid/signal_to_noise"], justification_source=source)
    with pytest.raises(CustodyError):
        successor(parent, child, led, rec)


def test_defect_record_with_downstream_fields_is_refused(exposed_parent):
    parent, led = exposed_parent
    child, _ = make_world(set_snr(0.9))
    rec = defect(parent, child, ["difficulty_grid/signal_to_noise"])
    rec["downstream_metric"] = 0.41
    with pytest.raises(CustodyError):
        successor(parent, child, led, rec)


def test_defect_record_must_name_exact_hashes_and_cover_every_change(exposed_parent):
    parent, led = exposed_parent

    def two_easier(spec):
        spec["difficulty_grid"]["signal_to_noise"]["level"] = 0.9
        spec["challenge_families"]["control_families"].remove("matched_null")
        spec["parameter_distributions"]["library_size"]["sigma"] = 0.01

    child, _ = make_world(two_easier)
    easier = ["difficulty_grid/signal_to_noise", "challenge_families/control_families/matched_null"]
    comps = ["parameter_distributions"]
    for rec in (
        defect(parent, child, easier, comps, parent_generator_semantic_hash=_h("other")),
        defect(parent, child, easier, comps, child_generator_semantic_hash=parent.generator_semantic_hash),
        defect(parent, child, easier[:1], comps),
        defect(parent, child, easier, []),
        defect(parent, child, [], []),
        defect(parent, child, easier, comps + ["not_a_component"]),
        defect(parent, child, easier, comps + comps),
        defect(parent, child, easier, comps, defect_description="   "),
        defect(parent, child, easier, comps, generator_side_evidence_sha256="see attached"),
        defect(parent, child, easier, comps, incomparable="no"),
        {k: v for k, v in defect(parent, child, easier, comps).items() if k != "affected_components"},
    ):
        with pytest.raises(CustodyError):
            successor(parent, child, led, rec)
    assert successor(parent, child, led, defect(parent, child, easier, comps)).disposition == "POST_EXPOSURE_VERSION"


def test_defect_record_naming_nothing_is_refused_even_for_a_harder_child(exposed_parent):
    parent, led = exposed_parent
    child, _ = make_world(set_snr(0.3))  # nothing easier, nothing changed
    with pytest.raises(CustodyError):
        successor(parent, child, led, defect(parent, child, [], []))
    disp = successor(parent, child, led, defect(parent, child, ["difficulty_grid/signal_to_noise"]))
    assert disp.disposition == "POST_EXPOSURE_VERSION"


def test_documented_defect_yields_post_exposure_version_without_inherited_qualification(exposed_parent):
    parent, led = exposed_parent
    child, _ = make_world(set_snr(0.9))
    rec = defect(parent, child, ["difficulty_grid/signal_to_noise"])
    disp = successor(parent, child, led, rec)
    assert disp.disposition == "POST_EXPOSURE_VERSION"
    assert disp.inherits_qualification is False
    assert disp.requires_realism_rerun is True and disp.requires_withheld_check is True
    assert disp.easier_dimensions == ("difficulty_grid/signal_to_noise",)
    assert disp.defect_record_sha256 == C.semantic_sha256(rec)
    assert disp.parent_generator_semantic_hash == parent.generator_semantic_hash
    assert disp.child_generator_semantic_hash == child.generator_semantic_hash
    last = led.entries()[-1]
    assert last["kind"] == "SUCCESSOR_RECORDED" and last["payload"]["defect_record"] == rec
    CU.record_generator_freeze(child, led)
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


def test_incomparable_defect_correction_is_a_new_scientific_testbed(exposed_parent):
    parent, led = exposed_parent
    child, _ = make_world(EASIER_EDITS["direction_flipped"])
    rec = defect(parent, child, ["difficulty_grid/signal_to_noise"], incomparable=True)
    disp = successor(parent, child, led, rec)
    assert disp.disposition == "NEW_SCIENTIFIC_TESTBED"
    assert disp.inherits_qualification is False


def test_laundering_through_an_unexposed_harder_intermediate_is_refused(exposed_parent):
    p0, led = exposed_parent
    p1, _ = make_world(set_snr(0.3))  # harder, never exposed
    assert successor(p0, p1, led).disposition == "SUCCESSOR_NOT_EASIER"
    CU.record_generator_freeze(p1, led)
    p2_easier, _ = make_world(set_snr(0.9))  # easier than exposed p0
    with pytest.raises(CustodyError):
        successor(p1, p2_easier, led)
    p2_exact_rollback, _ = make_world(set_snr(0.5))  # identical to exposed p0: a reroll of p0 (W2)
    with pytest.raises(CustodyError, match="reroll"):
        successor(p1, p2_exact_rollback, led)
    p2_rollback, _ = make_world(set_snr(0.4))  # rolling back part of never-exposed hardening is lawful
    disp = successor(p1, p2_rollback, led)
    assert disp.disposition == "SUCCESSOR_NOT_EASIER"
    assert disp.floor_generator_semantic_hash == p0.generator_semantic_hash


def test_post_exposure_version_is_a_floor_for_further_relaxation(exposed_parent):
    p0, led = exposed_parent
    p1, _ = make_world(set_snr(0.7))
    successor(p0, p1, led, defect(p0, p1, ["difficulty_grid/signal_to_noise"]))
    CU.record_generator_freeze(p1, led)
    p2, _ = make_world(set_snr(0.9))
    with pytest.raises(CustodyError):
        successor(p1, p2, led)
    p2_same, _ = make_world(set_snr(0.7))  # identical to its parent: a reroll (W2)
    with pytest.raises(CustodyError, match="reroll"):
        successor(p1, p2_same, led)
    p2_harder, _ = make_world(set_snr(0.6))
    disp = successor(p1, p2_harder, led)
    assert disp.disposition == "SUCCESSOR_NOT_EASIER"
    assert disp.floor_generator_semantic_hash == p1.generator_semantic_hash


def test_successor_must_descend_from_the_lineage_head(exposed_parent):
    p0, led = exposed_parent
    p1, _ = make_world(set_snr(0.3))
    successor(p0, p1, led)
    CU.record_generator_freeze(p1, led)
    p2, _ = make_world(set_snr(0.4))
    with pytest.raises(CustodyError):
        successor(p0, p2, led)  # skips the head p1
    unfrozen, _ = make_world(set_snr(0.2))
    with pytest.raises(CustodyError):
        CU.validate_successor_version(unfrozen, p2, parent_exposure_state=CU.exposure_state(p1, led), ledger=led)


def test_forged_exposure_state_is_refused(exposed_parent):
    p0, led = exposed_parent
    child, _ = make_world(set_snr(0.3))  # harder: the forged state is the only reason to refuse
    forged = CU.ExposureState(generator_semantic_hash=p0.generator_semantic_hash, exposed=False,
                              exposure_count=0, ledger_head=led.head)
    with pytest.raises(CustodyError):
        CU.validate_successor_version(p0, child, parent_exposure_state=forged, ledger=led)
    other = CU.ExposureState(generator_semantic_hash=child.generator_semantic_hash, exposed=True,
                             exposure_count=1, ledger_head=led.head)
    with pytest.raises(CustodyError):
        CU.validate_successor_version(p0, child, parent_exposure_state=other, ledger=led)


def test_stale_exposure_state_is_refused(exposed_parent):
    p0, led = exposed_parent
    stale = CU.exposure_state(p0, led)
    # advance the ledger without changing the exposure count: only the head check can catch this
    CU.record_fit_output_frozen(p0, led, class_tag=DEBUG, fit_output_sha256=_h("debug fit"))
    child, _ = make_world(set_snr(0.3))
    with pytest.raises(CustodyError):
        CU.validate_successor_version(p0, child, parent_exposure_state=stale, ledger=led)
    CU.validate_successor_version(p0, child, parent_exposure_state=CU.exposure_state(p0, led), ledger=led)


def test_record_exposure_checks_the_expected_ledger_head(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    prepare(fr, qnonce, led, make_tree(tmp_path))
    good = {"exposure_id": "e", "method_id": METHOD, "realization_class": DEBUG}
    with pytest.raises(CustodyError):
        CU.record_exposure(fr, good, led, expected_ledger_head=_h("some other head"))
    CU.record_exposure(fr, good, led, expected_ledger_head=led.head)


def test_new_version_cannot_skip_successor_validation(exposed_parent):
    p0, led = exposed_parent
    child, _ = make_world(set_snr(0.3))
    with pytest.raises(CustodyError):
        CU.record_generator_freeze(child, led)
    with pytest.raises(CustodyError):
        successor(p0, p0, led)  # identical version is not a successor
    successor(p0, child, led)
    with pytest.raises(CustodyError):
        successor(p0, child, led)  # one validation per child; no re-validation shopping
    CU.record_generator_freeze(child, led)
    with pytest.raises(CustodyError):
        CU.record_generator_freeze(child, led)


# -------------------------------------------- B2: strictly linear lineage

def test_superseded_version_cannot_be_committed():
    v1, q1 = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(v1, led)
    v2, _ = make_world(set_snr(0.9))  # easier, validated before any exposure
    assert successor(v1, v2, led).disposition == "PRE_EXPOSURE_REVISION"
    with pytest.raises(CustodyError):
        CU.record_nonce_commitment(v1, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(q1))
    with pytest.raises(CustodyError):
        CU.record_nonce_commitment(v1, led, class_tag=DEBUG, nonce_commitment=CU.nonce_commitment(dummy_nonce()))


def test_superseded_version_cannot_receive_a_withheld_commitment(tmp_path):
    v1, q1 = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(v1, led)
    CU.record_nonce_commitment(v1, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(q1))
    v2, _ = make_world(set_snr(0.9))
    successor(v1, v2, led)
    with pytest.raises(CustodyError):
        commit_withheld(v1, q1, led, make_tree(tmp_path))


def test_superseded_version_cannot_be_attested_or_exposed(tmp_path):
    v1, q1 = make_world()
    led = CU.CustodyLedger()
    roots = prepare(v1, q1, led, make_tree(tmp_path), attest=False)
    rd = roots[DEBUG][1]
    CU.attest_realization_set(rd, DEBUG, 3, emit(rd, DEBUG, 3), led, freeze=v1)
    v2, _ = make_world(set_snr(0.9))
    assert successor(v1, v2, led).disposition == "PRE_EXPOSURE_REVISION"
    rq = roots[QUAL][1]
    with pytest.raises(CustodyError):
        CU.attest_realization_set(rq, QUAL, 4, emit(rq, QUAL, 4), led, freeze=v1)
    with pytest.raises(CustodyError):
        expose(v1, led, DEBUG)  # P2: the easier pre-exposure successor cannot be bypassed by exposing V1


def test_second_successor_of_the_same_parent_is_refused():
    v1, _ = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(v1, led)
    v2, _ = make_world(set_snr(0.3))
    v3, _ = make_world(set_snr(0.4))
    successor(v1, v2, led)
    with pytest.raises(CustodyError):
        successor(v1, v3, led)


# --------------------------------- W2: a no-change successor is a reroll

def test_w2_no_change_successors_are_refused_as_rerolls(exposed_parent):
    p0, led = exposed_parent
    n_before = len(led)
    for _ in range(3):  # three consecutive attempts at fresh sealed draws of the same generator
        child, _ = make_world()
        with pytest.raises(CustodyError, match="reroll"):
            successor(p0, child, led)
    assert len(led) == n_before
    child, _ = make_world()
    with pytest.raises(CustodyError, match="reroll"):  # a defect record naming an unchanged component
        successor(p0, child, led, defect(p0, child, components=["mechanism_mixture"]))


def test_w2_reroll_of_an_exposed_ancestor_or_the_parent_is_refused(exposed_parent):
    p0, led = exposed_parent
    p1, _ = make_world(set_snr(0.3))
    successor(p0, p1, led)
    CU.record_generator_freeze(p1, led)
    for level in (0.3, 0.5):  # identical to the parent p1; identical to the exposed ancestor p0
        again, _ = make_world(set_snr(level))
        with pytest.raises(CustodyError, match="reroll"):
            successor(p1, again, led)
    assert successor(p1, make_world(set_snr(0.4))[0], led).disposition == "SUCCESSOR_NOT_EASIER"


def test_w2_identical_revision_before_any_exposure_is_not_a_reroll():
    v1, _ = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(v1, led)
    v2, _ = make_world()
    assert successor(v1, v2, led).disposition == "PRE_EXPOSURE_REVISION"


# ------------------------------ W1: the withheld family is frozen per lineage

EASIER_WITHHELD_SPEC = dict(DUMMY_WITHHELD_SPEC, DUMMY_family={"composition": "DUMMY_single_program", "weight": 0.5})


def qualify_and_reveal(freeze, qnonce, ledger, withheld=DUMMY_WITHHELD_SPEC, exposure_id="exp-q"):
    expose(freeze, ledger, QUAL, exposure_id)
    CU.record_fit_output_frozen(freeze, ledger, class_tag=QUAL, fit_output_sha256=_h("fit " + exposure_id))
    CU.reveal_withheld_family(freeze, ledger, withheld_spec=withheld, nonce=qnonce, withheld_class_tag=WTAG)


def _qualified_parent_and_child(tmp_path, child_withheld, reveal_parent=True, change="UNCHANGED", defect_components=()):
    p0, q0 = make_world()
    led = CU.CustodyLedger()
    prepare(p0, q0, led, make_tree(tmp_path))
    if reveal_parent:
        qualify_and_reveal(p0, q0, led, exposure_id="exp-p0")
    else:
        expose(p0, led, QUAL, "exp-p0")  # parent's sealed run left open and unrevealed
    child, q1 = make_world(set_snr(0.3), withheld=child_withheld)
    rec = defect(p0, child, ["difficulty_grid/signal_to_noise"], defect_components) if defect_components else None
    successor(p0, child, led, rec)
    CU.record_generator_freeze(child, led)
    commit_and_attest(child, q1, led, make_tree(tmp_path, "tree_child"), change=change)
    if defect_components:
        CU.record_requalification_prerequisites(child, led, realism_rerun_receipt_sha256=_h("realism"),
                                                withheld_check_plan_sha256=_h("plan"))
    expose(child, led, QUAL, "exp-child")
    CU.record_fit_output_frozen(child, led, class_tag=QUAL, fit_output_sha256=_h("child fit"))
    return p0, q0, child, q1, led


def test_w1_unchanged_successor_with_an_easier_withheld_family_fails_at_reveal(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(tmp_path, EASIER_WITHHELD_SPEC)
    with pytest.raises(CustodyError, match="hard custody failure"):
        CU.reveal_withheld_family(child, led, withheld_spec=EASIER_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)


def test_w1_unchanged_successor_with_the_same_withheld_family_reveals(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(tmp_path, DUMMY_WITHHELD_SPEC)
    CU.reveal_withheld_family(child, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


def test_w1b_successor_reveal_waits_for_the_parent_reveal_then_fails_on_mismatch(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(tmp_path, EASIER_WITHHELD_SPEC, reveal_parent=False)
    with pytest.raises(CustodyError, match="revealed first"):
        CU.reveal_withheld_family(child, led, withheld_spec=EASIER_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)
    with pytest.raises(CustodyError):  # the parent's own sealed run is still open: no early reveal
        CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    CU.record_fit_output_frozen(p0, led, class_tag=QUAL, fit_output_sha256=_h("parent fit"))  # superseded: allowed
    CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    with pytest.raises(CustodyError, match="hard custody failure"):
        CU.reveal_withheld_family(child, led, withheld_spec=EASIER_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)


def test_w1_reference_is_the_nearest_ancestor_that_committed_a_withheld_family(tmp_path):
    p0, q0 = make_world()
    led = CU.CustodyLedger()
    prepare(p0, q0, led, make_tree(tmp_path))
    qualify_and_reveal(p0, q0, led, exposure_id="exp-p0")
    p1, _ = make_world(set_snr(0.3))  # frozen but never committed: carries no withheld family of its own
    successor(p0, p1, led)
    CU.record_generator_freeze(p1, led)
    p2, q2 = make_world(set_snr(0.2), withheld=EASIER_WITHHELD_SPEC)
    successor(p1, p2, led)
    CU.record_generator_freeze(p2, led)
    commit_and_attest(p2, q2, led, make_tree(tmp_path, "tree_p2"), change="UNCHANGED")
    expose(p2, led, QUAL, "exp-p2")
    CU.record_fit_output_frozen(p2, led, class_tag=QUAL, fit_output_sha256=_h("p2 fit"))
    with pytest.raises(CustodyError, match="hard custody failure"):  # compared with p0's family, two levels up
        CU.reveal_withheld_family(p2, led, withheld_spec=EASIER_WITHHELD_SPEC, nonce=q2, withheld_class_tag=WTAG)


def test_withheld_change_declaration_must_match_the_successor_record(exposed_parent, tmp_path):
    p0, led = exposed_parent
    child, q1 = make_world(set_snr(0.3), withheld=EASIER_WITHHELD_SPEC)
    successor(p0, child, led)  # no defect record: the withheld family must stay unchanged
    CU.record_generator_freeze(child, led)
    CU.record_nonce_commitment(child, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(q1))
    tree = make_tree(tmp_path, "tree_child")
    for bad in (None, "CHANGED", "CHANGED_BY_DEFECT", True):
        with pytest.raises(CustodyError):
            commit_withheld(child, q1, led, tree, change=bad)
    commit_withheld(child, q1, led, tree, change="UNCHANGED")


def test_withheld_family_changed_by_defect_is_a_post_exposure_version(exposed_parent, tmp_path):
    p0, led = exposed_parent
    child, q1 = make_world(withheld=EASIER_WITHHELD_SPEC)  # public spec unchanged; only the withheld family changes
    disp = successor(p0, child, led, defect(p0, child, components=["withheld_family"]))
    assert disp.disposition == "POST_EXPOSURE_VERSION" and disp.inherits_qualification is False
    CU.record_generator_freeze(child, led)
    CU.record_nonce_commitment(child, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(q1))
    tree = make_tree(tmp_path, "tree_child")
    with pytest.raises(CustodyError):
        commit_withheld(child, q1, led, tree, change="UNCHANGED")  # contradicts the defect record
    commit_withheld(child, q1, led, tree, change="CHANGED_BY_DEFECT")


def test_lineage_root_declares_no_withheld_change(tmp_path):
    fr, q = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(fr, led)
    CU.record_nonce_commitment(fr, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(q))
    with pytest.raises(CustodyError):
        commit_withheld(fr, q, led, make_tree(tmp_path), change="UNCHANGED")


def test_declared_withheld_change_that_is_not_a_change_fails_at_reveal(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(
        tmp_path, DUMMY_WITHHELD_SPEC, change="CHANGED_BY_DEFECT", defect_components=["withheld_family"])
    with pytest.raises(CustodyError, match="not a change"):
        CU.reveal_withheld_family(child, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)


def test_withheld_family_changed_by_defect_reveals_a_different_family(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(
        tmp_path, EASIER_WITHHELD_SPEC, change="CHANGED_BY_DEFECT", defect_components=["withheld_family"])
    CU.reveal_withheld_family(child, led, withheld_spec=EASIER_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)


def test_superseded_reference_without_a_sealed_run_is_revealed_after_a_descendant_fit(tmp_path):
    p0, q0 = make_world()
    led = CU.CustodyLedger()
    prepare(p0, q0, led, make_tree(tmp_path))
    expose(p0, led, DEBUG)  # development exposure only: p0 can never freeze a qualification fit
    child, q1 = make_world(set_snr(0.3))
    successor(p0, child, led)
    CU.record_generator_freeze(child, led)
    commit_and_attest(child, q1, led, make_tree(tmp_path, "tree_child"), change="UNCHANGED")
    with pytest.raises(CustodyError):  # the child's sealed run has not even started: no early disclosure
        CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    expose(child, led, QUAL, "exp-child")
    with pytest.raises(CustodyError):  # no descendant qualification fit is frozen yet
        CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    CU.record_fit_output_frozen(child, led, class_tag=QUAL, fit_output_sha256=_h("child fit"))
    with pytest.raises(CustodyError, match="revealed first"):
        CU.reveal_withheld_family(child, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)
    CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    CU.reveal_withheld_family(child, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


def test_no_withheld_reveal_while_a_lineage_sealed_run_is_open(tmp_path):
    p0, q0 = make_world()
    led = CU.CustodyLedger()
    prepare(p0, q0, led, make_tree(tmp_path))
    expose(p0, led, QUAL, "exp-p0")
    CU.record_fit_output_frozen(p0, led, class_tag=QUAL, fit_output_sha256=_h("p0 fit"))
    child, q1 = make_world(set_snr(0.3))  # shares p0's withheld family
    successor(p0, child, led)
    CU.record_generator_freeze(child, led)
    commit_and_attest(child, q1, led, make_tree(tmp_path, "tree_child"), change="UNCHANGED")
    expose(child, led, QUAL, "exp-child")  # the child's sealed run is open
    with pytest.raises(CustodyError, match="open"):
        CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    CU.record_fit_output_frozen(child, led, class_tag=QUAL, fit_output_sha256=_h("child fit"))
    CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    CU.reveal_withheld_family(child, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)


# --------------------- withheld-check eligibility: a reused family must still be secret

def _withheld_entry(led, freeze):
    return [e["payload"] for e in led.entries()
            if e["kind"] == "WITHHELD_COMMITTED" and e["payload"]["generator_semantic_hash"] == freeze.generator_semantic_hash][0]


def test_unchanged_family_committed_before_the_reference_reveal_is_eligible(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(tmp_path, DUMMY_WITHHELD_SPEC, reveal_parent=False)
    assert _withheld_entry(led, child)["withheld_check_secret"] is True
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is True
    CU.record_fit_output_frozen(p0, led, class_tag=QUAL, fit_output_sha256=_h("parent fit"))
    CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is True  # revealed after its fit froze
    assert CU.withheld_check_eligible(led, p0.generator_semantic_hash) is True  # lineage root
    CU.reveal_withheld_family(child, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is True  # equal to its own group: expected


def test_unchanged_family_committed_after_the_reference_reveal_is_ineligible(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(tmp_path, DUMMY_WITHHELD_SPEC, reveal_parent=True)
    assert _withheld_entry(led, child)["withheld_check_secret"] is False
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is False
    CU.reveal_withheld_family(child, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q1, withheld_class_tag=WTAG)
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is False  # reveal does not repair it
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


def test_reused_family_disclosed_before_the_successor_fit_is_ineligible(tmp_path):
    p0, q0 = make_world()
    led = CU.CustodyLedger()
    prepare(p0, q0, led, make_tree(tmp_path))
    expose(p0, led, QUAL, "exp-p0")
    CU.record_fit_output_frozen(p0, led, class_tag=QUAL, fit_output_sha256=_h("p0 fit"))
    child, q1 = make_world(set_snr(0.3))
    successor(p0, child, led)
    CU.record_generator_freeze(child, led)
    commit_and_attest(child, q1, led, make_tree(tmp_path, "tree_child"), change="UNCHANGED")
    assert _withheld_entry(led, child)["withheld_check_secret"] is True  # still secret when committed ...
    CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is False  # ... public before its fit


def test_family_shared_through_an_unrevealed_parent_is_public_once_the_grandparent_is_revealed(tmp_path):
    p0, q0 = make_world()
    led = CU.CustodyLedger()
    prepare(p0, q0, led, make_tree(tmp_path))
    expose(p0, led, QUAL, "exp-p0")
    CU.record_fit_output_frozen(p0, led, class_tag=QUAL, fit_output_sha256=_h("p0 fit"))
    p1, q1 = make_world(set_snr(0.3))
    successor(p0, p1, led)
    CU.record_generator_freeze(p1, led)
    commit_and_attest(p1, q1, led, make_tree(tmp_path, "tree_p1"), change="UNCHANGED")  # p0 still secret
    CU.reveal_withheld_family(p0, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=q0, withheld_class_tag=WTAG)
    p2, q2 = make_world(set_snr(0.2))
    successor(p1, p2, led)
    CU.record_generator_freeze(p2, led)
    commit_and_attest(p2, q2, led, make_tree(tmp_path, "tree_p2"), change="UNCHANGED")
    assert _withheld_entry(led, p2)["withheld_check_secret"] is False  # p1 unrevealed, but p0 shares the family
    assert CU.withheld_check_eligible(led, p2.generator_semantic_hash) is False


def test_changed_by_defect_family_is_secret_and_eligible(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(
        tmp_path, EASIER_WITHHELD_SPEC, change="CHANGED_BY_DEFECT", defect_components=["withheld_family"])
    assert _withheld_entry(led, child)["withheld_check_secret"] is True
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is True


def test_version_without_a_withheld_commitment_is_ineligible(exposed_parent):
    p0, led = exposed_parent
    child, _ = make_world(set_snr(0.3))
    successor(p0, child, led)
    CU.record_generator_freeze(child, led)
    assert CU.withheld_check_eligible(led, child.generator_semantic_hash) is False
    assert CU.withheld_check_eligible(led, _h("never frozen")) is False


def test_forged_withheld_check_secret_flag_is_refused_on_replay(tmp_path):
    p0, q0, child, q1, led = _qualified_parent_and_child(tmp_path, DUMMY_WITHHELD_SPEC, reveal_parent=True)
    entries = [(e["kind"], e["payload"]) for e in led.entries()]
    idx = [i for i, (k, p) in enumerate(entries)
           if k == "WITHHELD_COMMITTED" and p["generator_semantic_hash"] == child.generator_semantic_hash][0]
    entries[idx][1]["withheld_check_secret"] = True
    raw, head = _forge(entries)
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(raw, expected_head=head)


# ------------- Q1: a qualification class nonce also opens the shared withheld family

def _three_unchanged_versions(tmp_path, expose_v3=True):
    """V1 -> V2 -> V3, all UNCHANGED (one family); V1 and V2 qualification fits frozen, nothing revealed."""
    v1, q1 = make_world()
    led = CU.CustodyLedger()
    prepare(v1, q1, led, make_tree(tmp_path, "t1"))
    expose(v1, led, QUAL, "e1")
    CU.record_fit_output_frozen(v1, led, class_tag=QUAL, fit_output_sha256=_h("v1 fit"))
    v2, q2 = make_world(set_snr(0.4))
    successor(v1, v2, led)
    CU.record_generator_freeze(v2, led)
    commit_and_attest(v2, q2, led, make_tree(tmp_path, "t2"), change="UNCHANGED")
    expose(v2, led, QUAL, "e2")
    CU.record_fit_output_frozen(v2, led, class_tag=QUAL, fit_output_sha256=_h("v2 fit"))
    v3, q3 = make_world(set_snr(0.3))
    successor(v2, v3, led)
    CU.record_generator_freeze(v3, led)
    commit_and_attest(v3, q3, led, make_tree(tmp_path, "t3"), change="UNCHANGED")
    if expose_v3:
        expose(v3, led, QUAL, "e3")  # V3's sealed qualification run is open
    return v1, q1, v2, q2, v3, q3, led


def test_q1_class_nonce_of_a_sharing_version_is_refused_while_a_run_is_open(tmp_path):
    v1, q1, v2, q2, v3, q3, led = _three_unchanged_versions(tmp_path)
    with pytest.raises(CustodyError, match="open"):
        CU.reveal_class_nonce(v2, led, class_tag=QUAL, nonce=q2)  # would open V2's commitment to the shared family
    assert CU.withheld_check_eligible(led, v3.generator_semantic_hash) is True
    CU.record_fit_output_frozen(v3, led, class_tag=QUAL, fit_output_sha256=_h("v3 fit"))
    CU.reveal_class_nonce(v2, led, class_tag=QUAL, nonce=q2)  # after V3's fit froze: lawful
    assert CU.withheld_check_eligible(led, v3.generator_semantic_hash) is True


def test_q1b_ancestor_class_nonce_is_refused_while_a_descendant_run_is_open(tmp_path):
    v1, q1, v2, q2, v3, q3, led = _three_unchanged_versions(tmp_path)
    with pytest.raises(CustodyError, match="open"):
        CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1)


def test_q1_class_nonce_reveal_before_a_sharing_fit_makes_it_ineligible(tmp_path):
    v1, q1, v2, q2, v3, q3, led = _three_unchanged_versions(tmp_path, expose_v3=False)
    CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1)  # no run open anywhere: allowed
    assert CU.withheld_check_eligible(led, v3.generator_semantic_hash) is False  # family public before V3's fit
    assert CU.withheld_check_eligible(led, v2.generator_semantic_hash) is True  # V2's fit froze first
    v4, q4 = make_world(set_snr(0.2))
    successor(v3, v4, led)
    CU.record_generator_freeze(v4, led)
    commit_and_attest(v4, q4, led, make_tree(tmp_path, "t4"), change="UNCHANGED")
    assert _withheld_entry(led, v4)["withheld_check_secret"] is False  # committed after the disclosure


def test_q1_unrelated_family_class_nonce_is_not_blocked(tmp_path):
    v1, q1 = make_world()
    led = CU.CustodyLedger()
    prepare(v1, q1, led, make_tree(tmp_path, "t1"))
    expose(v1, led, QUAL, "e1")
    CU.record_fit_output_frozen(v1, led, class_tag=QUAL, fit_output_sha256=_h("v1 fit"))
    v2, q2 = make_world(set_snr(0.4), withheld=EASIER_WITHHELD_SPEC)
    successor(v1, v2, led, defect(v1, v2, ["difficulty_grid/signal_to_noise"], ["withheld_family"]))
    CU.record_generator_freeze(v2, led)
    commit_and_attest(v2, q2, led, make_tree(tmp_path, "t2"), change="CHANGED_BY_DEFECT")
    CU.record_requalification_prerequisites(v2, led, realism_rerun_receipt_sha256=_h("r"),
                                            withheld_check_plan_sha256=_h("p"))
    expose(v2, led, QUAL, "e2")  # open run, but on a different withheld family
    CU.reveal_class_nonce(v1, led, class_tag=QUAL, nonce=q1)
    assert CU.withheld_check_eligible(led, v2.generator_semantic_hash) is True


# ---------------------- Q3: a "changed" family may not be one that is already public

def test_q3_change_back_to_an_already_public_family_is_ineligible(tmp_path):
    v1, q1 = make_world()
    led = CU.CustodyLedger()
    prepare(v1, q1, led, make_tree(tmp_path, "t1"))
    qualify_and_reveal(v1, q1, led, DUMMY_WITHHELD_SPEC, "e1")  # family W_A public
    versions = [v1]
    for k, (level, family) in enumerate(((0.4, EASIER_WITHHELD_SPEC), (0.3, DUMMY_WITHHELD_SPEC)), start=2):
        v, q = make_world(set_snr(level), withheld=family)
        parent = versions[-1]
        successor(parent, v, led, defect(parent, v, ["difficulty_grid/signal_to_noise"], ["withheld_family"]))
        CU.record_generator_freeze(v, led)
        commit_and_attest(v, q, led, make_tree(tmp_path, f"t{k}"), change="CHANGED_BY_DEFECT")
        assert _withheld_entry(led, v)["withheld_check_secret"] is True  # its spec is unknown at commit time
        CU.record_requalification_prerequisites(v, led, realism_rerun_receipt_sha256=_h(f"r{k}"),
                                                withheld_check_plan_sha256=_h(f"p{k}"))
        qualify_and_reveal(v, q, led, family, f"e{k}")
        versions.append(v)
    v2, v3 = versions[1], versions[2]
    assert CU.withheld_check_eligible(led, v2.generator_semantic_hash) is True  # W_B was new
    assert CU.withheld_check_eligible(led, v3.generator_semantic_hash) is False  # back to the public W_A
    reveal3 = [e["payload"] for e in led.entries() if e["kind"] == "REVEALED"
               and e["payload"]["generator_semantic_hash"] == v3.generator_semantic_hash][0]
    assert reveal3["family_previously_public"] is True
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)
    entries = [(e["kind"], e["payload"]) for e in led.entries()]
    idx = [i for i, (k, p) in enumerate(entries) if k == "REVEALED"
           and p["generator_semantic_hash"] == v3.generator_semantic_hash][0]
    entries[idx][1]["family_previously_public"] = False
    raw, head = _forge(entries)
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(raw, expected_head=head)


# ------------------------------- Q2: qualification draws are counted per method

def test_q2_qualification_draws_are_counted_per_method_across_versions(tmp_path):
    v, q = make_world()
    led = CU.CustodyLedger()
    prepare(v, q, led, make_tree(tmp_path, "t0"))

    def expose_as(fr, method, class_tag, eid):
        CU.record_exposure(fr, {"exposure_id": eid, "method_id": method, "realization_class": class_tag}, led)

    expose_as(v, METHOD_A, QUAL, "a0")
    expose_as(v, METHOD_B, QUAL, "b0")
    expose_as(v, METHOD_A, DEBUG, "a0-debug")  # development draws are not qualification draws
    versions = [v]
    for k, level in enumerate((0.4999, 0.4998, 0.4997), start=1):  # negligibly harder successors
        child, qc = make_world(set_snr(level))
        successor(versions[-1], child, led)
        CU.record_generator_freeze(child, led)
        commit_and_attest(child, qc, led, make_tree(tmp_path, f"t{k}"), change="UNCHANGED")
        expose_as(child, METHOD_A, QUAL, f"a{k}")
        versions.append(child)
    draws = CU.qualification_draws_for_method(led, METHOD_A)
    assert [d["generator_semantic_hash"] for d in draws] == [x.generator_semantic_hash for x in versions]
    assert [d["exposure_id"] for d in draws] == ["a0", "a1", "a2", "a3"]
    assert all(d["class_tag"] == QUAL for d in draws)
    positions = [d["ledger_index"] for d in draws]
    assert positions == sorted(positions) and len(set(positions)) == 4
    entries = led.entries()
    for d in draws:
        assert entries[d["ledger_index"]]["entry_hash"] == d["exposure_entry_hash"]
        att = [e for e in entries if e["kind"] == "REALIZATION_SET_ATTESTED"
               and e["payload"]["generator_semantic_hash"] == d["generator_semantic_hash"]
               and e["payload"]["class_tag"] == QUAL][0]
        assert d["realization_set"]["attestation_entry_hash"] == att["entry_hash"]
        assert d["realization_set"]["emitted_set_sha256"] == att["payload"]["emitted_set_sha256"]
    assert [d["exposure_id"] for d in CU.qualification_draws_for_method(led, METHOD_B)] == ["b0"]
    assert CU.qualification_draws_for_method(led, _h("DUMMY method C")) == []
    for bad in ("", "method-A", METHOD_A[:63], METHOD_A.upper()):
        with pytest.raises(CustodyError):
            CU.qualification_draws_for_method(led, bad)


def test_q2_renaming_the_method_digest_does_not_reset_the_lineage_count(tmp_path):
    v, q = make_world()
    led = CU.CustodyLedger()
    prepare(v, q, led, make_tree(tmp_path, "t0"))
    CU.record_exposure(v, {"exposure_id": "a0", "method_id": METHOD_A, "realization_class": QUAL}, led)
    near_copy, qc = make_world(set_snr(0.4999))
    successor(v, near_copy, led)
    CU.record_generator_freeze(near_copy, led)
    commit_and_attest(near_copy, qc, led, make_tree(tmp_path, "t1"), change="UNCHANGED")
    CU.record_exposure(near_copy, {"exposure_id": "a1", "method_id": METHOD_A_RENAMED,
                                   "realization_class": QUAL}, led)
    # the per-method view alone is fooled: (1, 1) ...
    assert len(CU.qualification_draws_for_method(led, METHOD_A)) == 1
    assert len(CU.qualification_draws_for_method(led, METHOD_A_RENAMED)) == 1
    # ... the lineage view counts both draws, whatever the label
    for version in (v, near_copy):
        draws = CU.qualification_draws_in_lineage(led, version.generator_semantic_hash)
        assert [d["exposure_id"] for d in draws] == ["a0", "a1"]
        assert [d["method_id"] for d in draws] == [METHOD_A, METHOD_A_RENAMED]


def test_q2_lineage_draws_span_ancestors_and_descendants_and_exclude_debug_and_other_ledgers(tmp_path):
    v0, q0 = make_world()
    led = CU.CustodyLedger()
    prepare(v0, q0, led, make_tree(tmp_path, "t0"))
    CU.record_exposure(v0, {"exposure_id": "q0", "method_id": METHOD_A, "realization_class": QUAL}, led)
    CU.record_exposure(v0, {"exposure_id": "d0", "method_id": METHOD_A, "realization_class": DEBUG}, led)
    versions = [v0]
    for k, (level, method) in enumerate(((0.4, METHOD_B), (0.3, METHOD_A)), start=1):
        child, qc = make_world(set_snr(level))
        successor(versions[-1], child, led)
        CU.record_generator_freeze(child, led)
        commit_and_attest(child, qc, led, make_tree(tmp_path, f"t{k}"), change="UNCHANGED")
        CU.record_exposure(child, {"exposure_id": f"q{k}", "method_id": method, "realization_class": QUAL}, led)
        versions.append(child)
    middle = versions[1].generator_semantic_hash
    draws = CU.qualification_draws_in_lineage(led, middle)
    assert [d["exposure_id"] for d in draws] == ["q0", "q1", "q2"]  # ancestor, itself, descendant; no debug
    assert [d["generator_semantic_hash"] for d in draws] == [x.generator_semantic_hash for x in versions]
    assert all(d["class_tag"] == QUAL for d in draws)
    for d in draws:
        per_method = CU.qualification_draws_for_method(led, d["method_id"])
        assert any(m["exposure_entry_hash"] == d["exposure_entry_hash"] for m in per_method)
    other_world, other_q = make_world()
    other = CU.CustodyLedger()
    prepare(other_world, other_q, other, make_tree(tmp_path, "t_other"))
    CU.record_exposure(other_world, {"exposure_id": "x0", "method_id": METHOD_A, "realization_class": QUAL}, other)
    assert [d["exposure_id"] for d in CU.qualification_draws_in_lineage(other, other_world.generator_semantic_hash)] \
        == ["x0"]
    with pytest.raises(CustodyError):  # a version from another lineage's ledger is not in this lineage
        CU.qualification_draws_in_lineage(led, other_world.generator_semantic_hash)


# ------------------------------------- N-c: requalification prerequisites

@pytest.mark.parametrize("incomparable", [False, True])
def test_defect_corrected_version_needs_requalification_prerequisites_before_exposure(exposed_parent, tmp_path,
                                                                                        incomparable):
    p0, led = exposed_parent
    p1, q1 = make_world(set_snr(0.9))
    disp = successor(p0, p1, led, defect(p0, p1, ["difficulty_grid/signal_to_noise"], incomparable=incomparable))
    assert disp.disposition == ("NEW_SCIENTIFIC_TESTBED" if incomparable else "POST_EXPOSURE_VERSION")
    CU.record_generator_freeze(p1, led)
    commit_and_attest(p1, q1, led, make_tree(tmp_path, "tree_p1"), change="UNCHANGED")
    with pytest.raises(CustodyError):
        expose(p1, led)
    for bad in ("not-hex", _h("x").upper(), None):
        with pytest.raises(CustodyError):
            CU.record_requalification_prerequisites(p1, led, realism_rerun_receipt_sha256=bad,
                                                    withheld_check_plan_sha256=_h("plan"))
        with pytest.raises(CustodyError):
            CU.record_requalification_prerequisites(p1, led, realism_rerun_receipt_sha256=_h("realism"),
                                                    withheld_check_plan_sha256=bad)
    CU.record_requalification_prerequisites(p1, led, realism_rerun_receipt_sha256=_h("realism"),
                                            withheld_check_plan_sha256=_h("plan"))
    with pytest.raises(CustodyError):
        CU.record_requalification_prerequisites(p1, led, realism_rerun_receipt_sha256=_h("realism2"),
                                                withheld_check_plan_sha256=_h("plan2"))
    expose(p1, led)
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


def test_superseded_defect_corrected_version_cannot_record_prerequisites(exposed_parent):
    p0, led = exposed_parent
    p1, _ = make_world(set_snr(0.9))
    successor(p0, p1, led, defect(p0, p1, ["difficulty_grid/signal_to_noise"]))
    CU.record_generator_freeze(p1, led)
    p2, _ = make_world(set_snr(0.8))  # harder than the floor p1
    successor(p1, p2, led)
    with pytest.raises(CustodyError, match="superseded"):
        CU.record_requalification_prerequisites(p1, led, realism_rerun_receipt_sha256=_h("realism"),
                                                withheld_check_plan_sha256=_h("plan"))


def test_requalification_prerequisites_apply_only_to_defect_corrected_versions(exposed_parent):
    p0, led = exposed_parent
    with pytest.raises(CustodyError):
        CU.record_requalification_prerequisites(p0, led, realism_rerun_receipt_sha256=_h("realism"),
                                                withheld_check_plan_sha256=_h("plan"))
    p1, _ = make_world(set_snr(0.3))
    successor(p0, p1, led)
    CU.record_generator_freeze(p1, led)
    with pytest.raises(CustodyError):
        CU.record_requalification_prerequisites(p1, led, realism_rerun_receipt_sha256=_h("realism"),
                                                withheld_check_plan_sha256=_h("plan"))


# --------------------------------------- E2 / N3: withheld plaintext leakage

@pytest.mark.parametrize("edit", [
    lambda s: s.update(withheld_spec={"x": 1}),
    lambda s: s["parameter_distributions"].update(withheld_family_params={"w": 0.1}),
    lambda s: s["mechanism_mixture"]["weights"].update(withheld_variant_a=0.1),
    lambda s: s["applicability_control_matrix"].update(rules=["withheld-family scoring rule"]),
    lambda s: s["serialization_contract"].update(controller_nonce="ab" * 32),
    lambda s: s["observation_calibration_distributions"].update(preimage_note="x"),
    lambda s: s["stress_regimes"].update(Withheld_Composition_Regime={"x": 1}),
    lambda s: s["challenge_families"]["novelty_regimes"].append("withheld mechanism variant"),
    lambda s: s["realization_budgets"].update(SYNTH_QUALIFICATION_WITHHELD=2),
])
def test_freeze_rejects_withheld_plaintext_in_public_spec(edit):
    spec = base_spec()
    edit(spec)
    spec["withheld_family_commitment"] = _h("DUMMY commitment")
    with pytest.raises(CustodyError):
        CU.freeze_generator_version(spec)


def test_withheld_commitment_requires_clean_scan_and_code_path_attestations(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    CU.record_generator_freeze(fr, led)
    CU.record_nonce_commitment(fr, led, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(qnonce))
    clean = make_tree(tmp_path, "clean")
    leaky = make_tree(tmp_path, "leaky")
    (leaky / "scripts" / "config.json").write_bytes(C.canonical_json_bytes(DUMMY_WITHHELD_SPEC))
    leak_scan = CU.scan_secret_absence(leaky, C.canonical_json_bytes(DUMMY_WITHHELD_SPEC))
    assert leak_scan["secret_absent"] is False
    good_scan = CU.scan_secret_absence(clean, qnonce)
    other = make_tree(tmp_path, "other")  # same file count, different content
    (other / "scripts" / "public_mechanism.py").write_bytes(b"def shared_kernel(x):\n    return 2 * x\n")
    other_tree_scan = CU.scan_secret_absence(other, qnonce)
    assert other_tree_scan["files_scanned"] == good_scan["files_scanned"]
    assert other_tree_scan["tree_identity"] != good_scan["tree_identity"]
    cpa = code_path_attestation()
    nc = CU.nonce_commitment(qnonce)
    bad_cases = [
        dict(secret_absence_attestations=[leak_scan], code_path_attestation=cpa),
        dict(secret_absence_attestations=[good_scan, other_tree_scan], code_path_attestation=cpa),
        dict(secret_absence_attestations=[dict(good_scan, matched_path="scripts/x.py")], code_path_attestation=cpa),
        dict(secret_absence_attestations=[], code_path_attestation=cpa),
        dict(secret_absence_attestations=[good_scan],
             code_path_attestation=dict(cpa, no_unique_withheld_public_path=False)),
        dict(secret_absence_attestations=[good_scan], code_path_attestation=dict(cpa, withheld_paths=["m.py::x"])),
        dict(secret_absence_attestations=[good_scan], code_path_attestation=dict(cpa, withheld_paths_count=1)),
    ]
    for kwargs in bad_cases:
        with pytest.raises(CustodyError):
            CU.record_withheld_commitment(fr, led, withheld_class_tag=WTAG, nonce_commitment=nc, **kwargs)
    CU.record_withheld_commitment(fr, led, withheld_class_tag=WTAG, nonce_commitment=nc,
                                  secret_absence_attestations=[good_scan], code_path_attestation=cpa)
    with pytest.raises(CustodyError):
        CU.record_withheld_commitment(fr, led, withheld_class_tag=WTAG, nonce_commitment=nc,
                                      secret_absence_attestations=[good_scan], code_path_attestation=cpa)


def test_withheld_only_public_code_path_fails_without_echoing_it():
    secret_name = "pkg/biology.py::DUMMY_withheld_only_composition_branch"
    shared = "pkg/biology.py::shared_program_kernel"
    with pytest.raises(CustodyError) as exc:
        CU.attest_no_unique_withheld_code_path({shared, secret_name}, {shared}, {shared, secret_name})
    assert "DUMMY_withheld_only_composition_branch" not in _chain_text(exc.value)
    assert "biology.py" not in _chain_text(exc.value)


@pytest.mark.parametrize("args", [
    ("pkg/a.py::f", {"pkg/a.py::f"}, {"pkg/a.py::f"}),
    (set(), {"pkg/a.py::f"}, {"pkg/a.py::f"}),
    ({"pkg/a.py::f"}, set(), {"pkg/a.py::f"}),
    ({"pkg/a.py::f"}, {"pkg/a.py::f"}, set()),
    ({"pkg/a.py::f", 3}, {"pkg/a.py::f"}, {"pkg/a.py::f"}),
    ({""}, {"pkg/a.py::f"}, {"pkg/a.py::f"}),
])
def test_code_path_attestation_rejects_vacuous_or_malformed_inputs(args):
    with pytest.raises(CustodyError):
        CU.attest_no_unique_withheld_code_path(*args)


@pytest.mark.parametrize("empty_position", [0, 1, 2])
def test_empty_code_path_sets_are_refused_as_vacuous(empty_position):
    args = [{"pkg/a.py::f"}, {"pkg/a.py::f"}, {"pkg/a.py::f"}]
    args[empty_position] = set()
    with pytest.raises(CustodyError, match="empty"):
        CU.attest_no_unique_withheld_code_path(*args)


# ------------------------------------------------- N-b: nothing supplied is echoed

def test_code_path_digest_failure_does_not_echo_paths():
    hidden = "DUMMY_hidden_" + "branch"
    a, b = "pkg/x.py::" + hidden + "\r\nz", "pkg/x.py::" + hidden + "\nz"  # collide after normalization
    with pytest.raises(CustodyError) as exc:
        CU.attest_no_unique_withheld_code_path({b}, {a, b}, {a, b})
    assert hidden not in _chain_text(exc.value)
    lone = "pkg/x.py::" + hidden + "\ud800"
    with pytest.raises(CustodyError) as exc:
        CU.attest_no_unique_withheld_code_path({lone}, {lone}, {lone})
    assert hidden not in _chain_text(exc.value)


def test_unknown_keys_are_reported_by_count_not_name(exposed_parent):
    hidden = "DUMMY_unlisted_" + "component"
    spec = base_spec()
    spec["withheld_family_commitment"] = _h("x")
    spec[hidden] = {"x": 1}
    with pytest.raises(CustodyError) as exc:
        CU.freeze_generator_version(spec)
    assert hidden not in _chain_text(exc.value)
    p0, led = exposed_parent
    child, _ = make_world(set_snr(0.9))
    rec = defect(p0, child, ["difficulty_grid/signal_to_noise"])
    rec[hidden] = 1
    with pytest.raises(CustodyError) as exc:
        successor(p0, child, led, rec)
    assert hidden not in _chain_text(exc.value)
    with pytest.raises(CustodyError) as exc:
        CU.record_exposure(p0, {"exposure_id": "e9", "method_id": METHOD, "realization_class": DEBUG, hidden: 1}, led)
    assert hidden not in _chain_text(exc.value)


def test_withheld_spec_key_collision_is_not_echoed(exposed_qual):
    hidden = "DUMMY_hidden_" + "key"
    colliding = {hidden + "\r\n": 1, hidden + "\n": 2}
    pre = CU.generator_precommitment_semantic_hash(base_spec())
    with pytest.raises(CustodyError) as exc:
        CU.withheld_family_commitment(dummy_nonce(), colliding, pre, WTAG)
    assert hidden not in _chain_text(exc.value)
    fr, led, roots, qnonce = exposed_qual
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit"))
    with pytest.raises(CustodyError) as exc:
        CU.reveal_withheld_family(fr, led, withheld_spec=colliding, nonce=qnonce, withheld_class_tag=WTAG)
    assert hidden not in _chain_text(exc.value)


# ----------------------------------------------------------- forged ledgers

def _forge(entries):
    """Hand-build a hash-chain-valid ledger (chain validity alone is public knowledge)."""
    out, prev = [], "0" * 64
    for i, (kind, payload) in enumerate(entries):
        body = {"format": ENTRY_FORMAT, "index": i, "kind": kind, "payload": payload, "prev_entry_hash": prev}
        h = C.semantic_sha256(body)
        out.append({"index": i, "kind": kind, "payload": payload, "prev_entry_hash": prev, "entry_hash": h})
        prev = h
    return C.canonical_json_bytes({"format": LEDGER_FORMAT, "entries": out}), prev


def test_chain_valid_ledger_with_out_of_order_custody_is_refused_on_replay():
    fr, _ = make_world()
    gf = ("GENERATOR_FROZEN", {"generator_semantic_hash": fr.generator_semantic_hash, "spec": fr.spec()})
    exposure = ("EXPOSURE_RECORDED", {"generator_semantic_hash": fr.generator_semantic_hash, "exposure_id": "e",
                                      "method_id": METHOD, "realization_class": DEBUG})
    reveal = ("REVEALED", {"reveal_type": "CLASS_NONCE", "generator_semantic_hash": fr.generator_semantic_hash,
                           "class_tag": QUAL, "nonce_hex": dummy_nonce().hex()})
    ok_raw, ok_head = _forge([gf])
    CU.CustodyLedger.from_bytes(ok_raw, expected_head=ok_head)
    for entries in ([gf, exposure], [gf, reveal], [exposure], [gf, ("UNKNOWN_KIND", {})], [gf, gf]):
        raw, head = _forge(entries)
        with pytest.raises(CustodyError):
            CU.CustodyLedger.from_bytes(raw, expected_head=head)


def test_chain_recomputed_after_deleting_an_entry_is_caught_by_the_anchor(exposed_parent):
    parent, led = exposed_parent
    entries = [(e["kind"], e["payload"]) for e in led.entries()]
    assert entries[-1][0] == "EXPOSURE_RECORDED"
    raw, head = _forge(entries[:-1])
    CU.CustodyLedger.from_bytes(raw)
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(raw, expected_head=led.head)


@pytest.mark.parametrize("override", [
    {"budget": 5, "n_emitted": 5},  # consistently inflated: only the frozen-budget check can catch it
    {"budget": 3, "n_emitted": 3},
    {"n_emitted": 3},
    {"budget": True},
])
def test_forged_attestation_with_wrong_counts_is_refused_on_replay(committed, override):
    fr, led, roots, _ = committed
    root = roots[QUAL][1]
    CU.attest_realization_set(root, QUAL, 4, emit(root, QUAL, 4), led, freeze=fr)
    entries = [(e["kind"], e["payload"]) for e in led.entries()]
    entries[-1][1].update(override)
    raw, head = _forge(entries)
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(raw, expected_head=head)


@pytest.mark.parametrize("field", ["root_commitment", "authorized_ids_digest"])
def test_forged_attestation_digest_is_caught_at_reveal(exposed_qual, field):
    fr, led, roots, qnonce = exposed_qual
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit"))
    entries = [(e["kind"], e["payload"]) for e in led.entries()]
    idx = [i for i, (k, p) in enumerate(entries) if k == "REALIZATION_SET_ATTESTED" and p["class_tag"] == QUAL][0]
    entries[idx][1][field] = _h("forged " + field)
    raw, head = _forge(entries)
    forged = CU.CustodyLedger.from_bytes(raw, expected_head=head)  # chain- and order-valid
    with pytest.raises(CustodyError):
        CU.reveal_class_nonce(fr, forged, class_tag=QUAL, nonce=qnonce)


def test_forged_withheld_entry_bound_to_another_nonce_is_refused_on_replay(committed):
    fr, led, roots, qnonce = committed
    entries = [(e["kind"], e["payload"]) for e in led.entries()]
    idx = [i for i, (k, _) in enumerate(entries) if k == "WITHHELD_COMMITTED"][0]
    entries[idx][1]["nonce_commitment"] = CU.nonce_commitment(roots[DEBUG][0])
    raw, head = _forge(entries)
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(raw, expected_head=head)


def test_forged_generator_entry_with_wrong_hash_is_refused():
    fr, _ = make_world()
    raw, head = _forge([("GENERATOR_FROZEN", {"generator_semantic_hash": _h("forged"), "spec": fr.spec()})])
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(raw, expected_head=head)
