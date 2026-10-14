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


def commit_withheld(freeze, qnonce, ledger, tree):
    scans = [CU.require_secret_absence(tree, qnonce)]
    CU.record_withheld_commitment(freeze, ledger, withheld_class_tag=WTAG, nonce_commitment=CU.nonce_commitment(qnonce),
                                  secret_absence_attestations=scans, code_path_attestation=code_path_attestation())


def commit_and_attest(freeze, qnonce, ledger, tree, attest=True):
    nonces = {DEBUG: dummy_nonce(), QUAL: qnonce}
    for tag in (DEBUG, QUAL):
        CU.record_nonce_commitment(freeze, ledger, class_tag=tag, nonce_commitment=CU.nonce_commitment(nonces[tag]))
    commit_withheld(freeze, qnonce, ledger, tree)
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
        freeze, {"exposure_id": exposure_id, "method_id": "fixture_method", "realization_class": class_tag}, ledger
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
    p2_rollback, _ = make_world(set_snr(0.5))  # rolling back only never-exposed hardening is lawful
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
    p2_same, _ = make_world(set_snr(0.7))
    disp = successor(p1, p2_same, led)
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
    good = {"exposure_id": "e", "method_id": "m", "realization_class": DEBUG}
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


# ------------------------------------- N-c: requalification prerequisites

@pytest.mark.parametrize("incomparable", [False, True])
def test_defect_corrected_version_needs_requalification_prerequisites_before_exposure(exposed_parent, tmp_path,
                                                                                        incomparable):
    p0, led = exposed_parent
    p1, q1 = make_world(set_snr(0.9))
    disp = successor(p0, p1, led, defect(p0, p1, ["difficulty_grid/signal_to_noise"], incomparable=incomparable))
    assert disp.disposition == ("NEW_SCIENTIFIC_TESTBED" if incomparable else "POST_EXPOSURE_VERSION")
    CU.record_generator_freeze(p1, led)
    commit_and_attest(p1, q1, led, make_tree(tmp_path, "tree_p1"))
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
        CU.record_exposure(p0, {"exposure_id": "e9", "method_id": "m", "realization_class": DEBUG, hidden: 1}, led)
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
                                      "method_id": "m", "realization_class": DEBUG})
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
