"""Custody tests for production synthetic V3.1.1 Task 2.

Controlling law: V3.1 sections 1.1-1.3 and 2.2, V3.1.1 errata E1/E2, plan
withheld-family custody law and binding note N3.

Every secret in this file is a DUMMY generated in-test (``secrets.token_bytes``)
or a literal visibly labelled DUMMY. No production nonce, withheld
specification or withheld-only code exists here; anything written to disk is
written under pytest ``tmp_path`` and discarded.
"""
import ast
import base64
import hashlib
import importlib.util
import itertools
import json
import random
import secrets
import sys

import numpy as np
import pytest

import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU
from scripts.production_synthetic.custody_v1 import CustodyError

QUAL = "SYNTH_QUALIFICATION"
DEBUG = "SYNTH_DEBUG"
WTAG = "SYNTH_QUALIFICATION_WITHHELD"

COMMIT_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-COMMIT-V1\x00"
NONCE_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-NONCE-COMMIT-V1\x00"
ROOT_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-SEALED-ROOT-V1\x00"
ROOT_COMMIT_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-ROOT-COMMIT-V1\x00"
RID_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-REALIZATION-ID-V1\x00"
STREAM_DOMAIN = b"JEPA-PRODUCTION-SYNTHETIC-CUSTODY-STREAM-V1\x00"

# DUMMY withheld-family specification: a stand-in so commit/reveal mechanics can
# be exercised. It is not, and does not resemble, the controller-held secret.
DUMMY_WITHHELD_SPEC = {
    "DUMMY_family": {"composition": "DUMMY_pair_of_shared_programs", "weight": 0.125},
    "DUMMY_scoring_rule": "DUMMY",
    "DUMMY_budget": 2,
}


def _h(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _frame(b):
    return len(b).to_bytes(8, "big") + b


def dummy_nonce():
    """DUMMY 256-bit nonce, freshly generated per call; never a production secret."""
    return secrets.token_bytes(32)


def base_spec():
    """A complete public generator spec WITHOUT the withheld-family commitment."""
    return {
        "generator_source": {"scripts/production_synthetic/fixture_generator.py": _h("fixture-src")},
        "transitive_dependencies": {"numpy==2.4.6": _h("numpy-wheel")},
        "parameter_distributions": {"library_size": {"law": "lognormal", "mu": 8.0, "sigma": 0.5}},
        "mechanism_mixture": {"weights": {"program_a": 0.5, "program_b": 0.5}},
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
        "applicability_control_matrix": {"matched_null": ["all_targets"]},
        "registries": {"address_registry": _h("addr"), "modality_namespace_registry": _h("mod")},
        "serialization_contract": {"canonical_module": "canonical_v1", "format_version": 1},
        "realization_budgets": {DEBUG: 3, QUAL: 4},
    }


def make_world(edit=None, withheld=DUMMY_WITHHELD_SPEC):
    """Freeze a fixture generator whose E2 commitment uses its SYNTH_QUALIFICATION nonce (returned)."""
    spec = base_spec()
    if edit is not None:
        edit(spec)
    qnonce = dummy_nonce()
    pre = CU.generator_precommitment_semantic_hash(spec)
    spec["withheld_family_commitment"] = CU.withheld_family_commitment(qnonce, withheld, pre, WTAG)
    return CU.freeze_generator_version(spec), qnonce


def full_spec():
    spec = base_spec()
    spec["withheld_family_commitment"] = _h("DUMMY-commitment-placeholder")
    return spec


def make_tree(tmp_path, name="tree"):
    tree = tmp_path / name
    (tree / "scripts").mkdir(parents=True)
    (tree / "scripts" / "public_mechanism.py").write_bytes(b"def shared_kernel(x):\n    return x\n")
    (tree / "README.md").write_bytes(b"public fixture tree\n")
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
    scans = [
        CU.require_secret_absence(tree, qnonce),
        CU.require_secret_absence(tree, C.canonical_json_bytes(DUMMY_WITHHELD_SPEC)),
    ]
    CU.record_withheld_commitment(
        freeze, ledger, withheld_class_tag=WTAG, nonce_commitment=CU.nonce_commitment(qnonce),
        secret_absence_attestations=scans, code_path_attestation=code_path_attestation(),
    )


def commit_and_attest(freeze, qnonce, ledger, tree, attest=True):
    """Nonce commitments -> withheld commitment -> attestations; return {class_tag: (nonce, root)}."""
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


# ---------------------------------------------------------------- commitments

def test_nonce_must_be_at_least_256_bits():
    ph = _h("payload")
    with pytest.raises(CustodyError):
        CU.commit_secret(secrets.token_bytes(31), ph, "TAG")
    assert len(CU.commit_secret(secrets.token_bytes(32), ph, "TAG")) == 64
    assert len(CU.commit_secret(secrets.token_bytes(64), ph, "TAG")) == 64
    with pytest.raises(CustodyError):
        CU.nonce_commitment(secrets.token_bytes(16))
    with pytest.raises(CustodyError):
        CU.sealed_root(secrets.token_bytes(31), ph, QUAL, 4)


@pytest.mark.parametrize("bad", ["a" * 64, 2**255, bytearray(32), memoryview(bytes(range(32))), None, 1.5])
def test_nonce_type_must_be_bytes(bad):
    with pytest.raises(CustodyError):
        CU.commit_secret(bad, _h("payload"), "TAG")
    with pytest.raises(CustodyError):
        CU.nonce_commitment(bad)


def test_commit_secret_known_answer_and_field_binding():
    nonce = bytes(range(100, 132))  # DUMMY fixed nonce for a known-answer test
    ph = _h("payload")
    tag = "SYNTH_QUALIFICATION_WITHHELD"
    expected = hashlib.sha256(
        COMMIT_DOMAIN + _frame(nonce) + _frame(bytes.fromhex(ph)) + _frame(tag.encode("utf-8"))
    ).hexdigest()
    assert CU.commit_secret(nonce, ph, tag) == expected
    assert CU.commit_secret(nonce, ph, tag) == expected  # deterministic
    assert CU.commit_secret(bytes(range(101, 133)), ph, tag) != expected
    assert CU.commit_secret(nonce, _h("other"), tag) != expected
    assert CU.commit_secret(nonce, ph, tag + "X") != expected
    with pytest.raises(CustodyError):
        CU.commit_secret(nonce, ph.upper(), tag)  # payload hash must be lowercase hex
    with pytest.raises(CustodyError):
        CU.commit_secret(nonce, ph[:63], tag)
    with pytest.raises(CustodyError):
        CU.commit_secret(nonce, ph, "")


def test_verify_reveal_accepts_match_and_rejects_every_mismatch():
    nonce = dummy_nonce()
    ph = _h("payload")
    commitment = CU.commit_secret(nonce, ph, "TAG")
    CU.verify_reveal(commitment, nonce, ph, "TAG")
    with pytest.raises(CustodyError):
        CU.verify_reveal(commitment, dummy_nonce(), ph, "TAG")
    with pytest.raises(CustodyError):
        CU.verify_reveal(commitment, nonce, _h("alternative"), "TAG")
    with pytest.raises(CustodyError):
        CU.verify_reveal(commitment, nonce, ph, "OTHER_TAG")
    with pytest.raises(CustodyError):
        CU.verify_reveal(_h("not the commitment"), nonce, ph, "TAG")


def test_nonce_commitment_sealed_root_and_ids_known_answer():
    nonce = bytes(range(7, 39))  # DUMMY
    gsh = _h("generator")
    assert CU.nonce_commitment(nonce) == hashlib.sha256(NONCE_DOMAIN + _frame(nonce)).hexdigest()
    root = CU.sealed_root(nonce, gsh, QUAL, 4)
    expected_root = hashlib.sha256(
        ROOT_DOMAIN + _frame(nonce) + _frame(bytes.fromhex(gsh)) + _frame(QUAL.encode()) + _frame((4).to_bytes(8, "big"))
    ).digest()
    assert isinstance(root, bytes) and root == expected_root and len(root) == 32
    assert CU.root_commitment(root) == hashlib.sha256(ROOT_COMMIT_DOMAIN + _frame(root)).hexdigest()
    ids = CU.authorized_realization_ids(root, QUAL, 4)
    assert ids == [
        hashlib.sha256(RID_DOMAIN + _frame(root) + _frame(QUAL.encode()) + _frame(i.to_bytes(8, "big"))).hexdigest()
        for i in range(4)
    ]
    assert CU.nonce_commitment(nonce) != root.hex()


def test_sealed_root_binds_every_field():
    nonce = dummy_nonce()
    gsh = _h("generator")
    ref = CU.sealed_root(nonce, gsh, QUAL, 4)
    assert CU.sealed_root(dummy_nonce(), gsh, QUAL, 4) != ref
    assert CU.sealed_root(nonce, _h("other generator"), QUAL, 4) != ref
    assert CU.sealed_root(nonce, gsh, DEBUG, 4) != ref
    assert CU.sealed_root(nonce, gsh, QUAL, 5) != ref
    for bad_budget in (0, -1, True, 4.0, "4"):
        with pytest.raises(CustodyError):
            CU.sealed_root(nonce, gsh, QUAL, bad_budget)


def test_withheld_commitment_maps_e2_and_verifies_reveal():
    nonce = bytes(range(50, 82))  # DUMMY
    pre = CU.generator_precommitment_semantic_hash(base_spec())
    spec_hash = C.semantic_sha256(DUMMY_WITHHELD_SPEC)
    payload = C.semantic_sha256(
        {"withheld_spec_sha256": spec_hash, "generator_precommitment_semantic_hash": pre}
    )
    assert CU.withheld_commitment_payload_hash(spec_hash, pre) == payload
    commitment = CU.withheld_family_commitment(nonce, DUMMY_WITHHELD_SPEC, pre, WTAG)
    assert commitment == CU.commit_secret(nonce, payload, WTAG)
    CU.verify_withheld_reveal(commitment, nonce, DUMMY_WITHHELD_SPEC, pre, WTAG)
    alternative = dict(DUMMY_WITHHELD_SPEC, DUMMY_budget=3)  # an alternative withheld-family draw
    for args in (
        (commitment, nonce, alternative, pre, WTAG),
        (commitment, bytes(range(51, 83)), DUMMY_WITHHELD_SPEC, pre, WTAG),
        (commitment, nonce, DUMMY_WITHHELD_SPEC, _h("other generator"), WTAG),
        (commitment, nonce, DUMMY_WITHHELD_SPEC, pre, "SYNTH_QUALIFICATION_OTHER"),
    ):
        with pytest.raises(CustodyError):
            CU.verify_withheld_reveal(*args)


def test_precommitment_hash_breaks_the_generator_hash_cycle():
    spec = base_spec()
    pre = CU.generator_precommitment_semantic_hash(spec)
    assert pre == C.semantic_sha256({"generator_precommitment_v1": spec})
    a = dict(spec, withheld_family_commitment=_h("commitment-a"))
    b = dict(spec, withheld_family_commitment=_h("commitment-b"))
    fa, fb = CU.freeze_generator_version(a), CU.freeze_generator_version(b)
    assert fa.generator_semantic_hash != fb.generator_semantic_hash
    assert fa.precommitment_semantic_hash == fb.precommitment_semantic_hash == pre
    with pytest.raises(CustodyError):
        CU.generator_precommitment_semantic_hash(a)  # must be computed before the commitment exists


# ------------------------------------------------------------- random streams

def test_stream_seed_known_answer_and_generator_construction():
    root = bytes(range(32))  # DUMMY fixed root
    parts = (("purpose_tag", "noise"), ("cell_id", "c1"), ("world_id", "w0"))
    ident = C.canonical_json_bytes({"cell_id": "c1", "purpose_tag": "noise", "world_id": "w0"})
    expected = hashlib.sha256(STREAM_DOMAIN + _frame(root) + _frame(ident)).digest()
    assert CU.stream_seed_digest(root, *parts) == expected
    ref = np.random.Generator(np.random.PCG64(np.random.SeedSequence(int.from_bytes(expected, "big"))))
    assert np.array_equal(CU.derive_stream(root, *parts).integers(0, 2**62, 32), ref.integers(0, 2**62, 32))


def test_stream_identity_key_order_is_irrelevant():
    root = secrets.token_bytes(32)
    parts = [("world_id", "w0"), ("donor_id", "d7"), ("cell_id", "c3"), ("purpose_tag", "counts")]
    ref = CU.derive_stream(root, *parts).random(16)
    for perm in itertools.permutations(parts):
        assert np.array_equal(CU.derive_stream(root, *perm).random(16), ref)


def test_stream_domain_separation_by_scientific_identity():
    root = secrets.token_bytes(32)
    base = {"world_id": "w0", "component_id": "k1", "donor_id": "d1", "cell_id": "c1",
            "modality_id": "rna", "address_id": "a1", "purpose_tag": "counts", "draw_index_tag": "draw-0"}
    ref = CU.derive_stream(root, *base.items()).integers(0, 2**62, 8)
    seen = {tuple(ref)}
    for key in base:
        changed = dict(base, **{key: base[key] + "x"})
        out = tuple(CU.derive_stream(root, *changed.items()).integers(0, 2**62, 8))
        assert out not in seen
        seen.add(out)
    dropped = {k: v for k, v in base.items() if k != "address_id"}
    assert tuple(CU.derive_stream(root, *dropped.items()).integers(0, 2**62, 8)) not in seen
    other_root = tuple(CU.derive_stream(secrets.token_bytes(32), *base.items()).integers(0, 2**62, 8))
    assert other_root not in seen


def test_streams_are_row_order_invariant():
    root = secrets.token_bytes(32)
    cells = [("d%d" % (i % 3), "c%03d" % i) for i in range(40)]

    def run(order):
        out = {}
        for donor, cell in order:
            rng = CU.derive_stream(root, ("world_id", "w0"), ("donor_id", donor), ("cell_id", cell),
                                   ("purpose_tag", "counts"))
            out[(donor, cell)] = rng.poisson(5.0, 6).tolist()
        return out

    ref = run(cells)
    shuffled = list(cells)
    random.Random(0).shuffle(shuffled)
    assert run(shuffled) == ref
    assert run(list(reversed(cells))) == ref


def test_purpose_tag_is_required():
    root = secrets.token_bytes(32)
    with pytest.raises(CustodyError):
        CU.derive_stream(root, ("world_id", "w0"), ("cell_id", "c1"))
    with pytest.raises(CustodyError):
        CU.derive_stream(root)


def test_world_id_is_required_and_separates_worlds():
    root = secrets.token_bytes(32)
    with pytest.raises(CustodyError):
        CU.derive_stream(root, ("cell_id", "c1"), ("purpose_tag", "counts"))
    a = CU.derive_stream(root, ("world_id", "w0"), ("cell_id", "c1"), ("purpose_tag", "counts"))
    b = CU.derive_stream(root, ("world_id", "w1"), ("cell_id", "c1"), ("purpose_tag", "counts"))
    assert not np.array_equal(a.integers(0, 2**62, 16), b.integers(0, 2**62, 16))


# ------------------------------------------------------------ generator freeze

def test_freeze_identity_is_semantic_hash_of_spec():
    spec = full_spec()
    fr = CU.freeze_generator_version(spec)
    assert fr.generator_semantic_hash == C.semantic_sha256(spec)
    reordered = dict(reversed(list(spec.items())))
    assert CU.freeze_generator_version(reordered).generator_semantic_hash == fr.generator_semantic_hash
    assert fr.withheld_family_commitment == spec["withheld_family_commitment"]
    assert fr.realization_budget(QUAL) == 4 and fr.realization_budget(DEBUG) == 3
    assert fr.spec() == C.load_canonical_json(C.canonical_json_bytes(spec))


@pytest.mark.parametrize("missing", list(full_spec()))
def test_freeze_rejects_missing_component(missing):
    spec = full_spec()
    del spec[missing]
    with pytest.raises(CustodyError):
        CU.freeze_generator_version(spec)


def test_freeze_rejects_unknown_component():
    with pytest.raises(CustodyError):
        CU.freeze_generator_version(dict(full_spec(), notes={"x": 1}))
    with pytest.raises(CustodyError):
        CU.freeze_generator_version([("generator_source", {})])


@pytest.mark.parametrize("budgets", [
    {"DEV": 3, QUAL: 4},
    {"SEALED": 4},
    {"SYNTH_DEV": 3, QUAL: 4},
    {"SYNTH_SEALED": 4, QUAL: 4},
    {QUAL: 4, "SYNTH_OTHER": 1},
    {DEBUG: 3},
    {QUAL: 0},
    {QUAL: -2},
    {QUAL: True},
    {QUAL: 4.0},
    {},
])
def test_freeze_rejects_bad_realization_budgets(budgets):
    with pytest.raises(CustodyError):
        CU.freeze_generator_version(dict(full_spec(), realization_budgets=budgets))


@pytest.mark.parametrize("tag", ["DEV", "SEALED", "SYNTH_DEV", "SYNTH_SEALED", "SYNTH_QUALIFICATION_SEALED"])
def test_real_partition_names_are_refused_by_the_naming_law(tag):
    with pytest.raises(CustodyError, match="DEV or SEALED"):
        CU.freeze_generator_version(dict(full_spec(), realization_budgets={tag: 1, QUAL: 4}))


@pytest.mark.parametrize("grid", [
    {},
    {"snr": {"level": 0.5}},
    {"snr": {"level": 0.5, "harder_direction": "sideways"}},
    {"snr": {"level": True, "harder_direction": "increasing"}},
    {"snr": {"level": "0.5", "harder_direction": "increasing"}},
    {"snr": {"level": 0.5, "harder_direction": "increasing", "extra": 1}},
    {"snr": 0.5},
])
def test_freeze_rejects_malformed_difficulty_grid(grid):
    with pytest.raises(CustodyError):
        CU.freeze_generator_version(dict(full_spec(), difficulty_grid=grid))


def test_freeze_challenge_families_must_be_exactly_the_e1_categories():
    fams = full_spec()["challenge_families"]
    missing = {k: v for k, v in fams.items() if k != "novelty_regimes"}
    extra = dict(fams, other_challenges=["x"])
    dup = dict(fams, control_families=["matched_null", "matched_null"])
    nonstr = dict(fams, control_families=["matched_null", 3])
    for bad in (missing, extra, dup, nonstr):
        with pytest.raises(CustodyError):
            CU.freeze_generator_version(dict(full_spec(), challenge_families=bad))


def test_freeze_binds_source_dependencies_and_registries_by_digest():
    for key in ("generator_source", "transitive_dependencies", "registries"):
        for bad in ({}, {"x": "not-a-digest"}, {"x": _h("y").upper()}, ["x"]):
            with pytest.raises(CustodyError):
                CU.freeze_generator_version(dict(full_spec(), **{key: bad}))
    for key in ("parameter_distributions", "mechanism_mixture", "observation_calibration_distributions",
                "applicability_control_matrix", "serialization_contract", "stress_regimes"):
        with pytest.raises(CustodyError):
            CU.freeze_generator_version(dict(full_spec(), **{key: {}}))
    with pytest.raises(CustodyError):
        CU.freeze_generator_version(dict(full_spec(), withheld_family_commitment="DUMMY plaintext"))


def test_freeze_is_immutable_and_self_consistent():
    fr = CU.freeze_generator_version(full_spec())
    with pytest.raises(Exception):
        fr.generator_semantic_hash = _h("forged")
    copy = fr.spec()
    copy["difficulty_grid"]["signal_to_noise"]["level"] = 99.0
    assert fr.spec()["difficulty_grid"]["signal_to_noise"]["level"] == 0.5
    assert CU.freeze_generator_version(fr.spec()).generator_semantic_hash == fr.generator_semantic_hash
    with pytest.raises(CustodyError):
        CU.GeneratorFreeze(
            generator_semantic_hash=_h("forged"),
            precommitment_semantic_hash=fr.precommitment_semantic_hash,
            withheld_family_commitment=fr.withheld_family_commitment,
            canonical_spec=fr.canonical_spec,
        )


def test_freeze_accepts_evidence_rights_state_names():
    spec = full_spec()
    spec["applicability_control_matrix"] = {
        "evidence_states": ["MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED",
                            "MEASURED_COLLISION_UNRESOLVED", "WITHHELD_BY_EVIDENCE_RIGHTS"],
    }
    CU.freeze_generator_version(spec)


# ---------------------------------------------------------------------- ledger

def test_ledger_entry_hash_known_answer_and_chain():
    led = CU.CustodyLedger()
    assert led.head == "0" * 64 and len(led) == 0
    fr = CU.freeze_generator_version(full_spec())
    h0 = CU.record_generator_freeze(fr, led)
    body = {
        "format": "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-ENTRY-V1",
        "index": 0,
        "kind": "GENERATOR_FROZEN",
        "payload": {"generator_semantic_hash": fr.generator_semantic_hash, "spec": fr.spec()},
        "prev_entry_hash": "0" * 64,
    }
    assert h0 == C.semantic_sha256(body) == led.head
    entries = led.entries()
    assert entries[0]["entry_hash"] == h0 and entries[0]["prev_entry_hash"] == "0" * 64
    entries[0]["kind"] = "REVEALED"  # a copy: mutating it cannot change the ledger
    assert led.entries()[0]["kind"] == "GENERATOR_FROZEN"
    assert led.verify() == h0


def test_ledger_round_trip_and_tamper_detection(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    prepare(fr, qnonce, led, make_tree(tmp_path))
    raw = led.to_bytes()
    replay = CU.CustodyLedger.from_bytes(raw, expected_head=led.head)
    assert replay.to_bytes() == raw and replay.head == led.head
    obj = C.load_canonical_json(raw)
    debug_att = [i for i, e in enumerate(obj["entries"])
                 if e["kind"] == "REALIZATION_SET_ATTESTED" and e["payload"]["class_tag"] == DEBUG][0]

    edited = C.load_canonical_json(raw)
    edited["entries"][debug_att]["payload"]["n_emitted"] = 2
    dropped = C.load_canonical_json(raw)
    del dropped["entries"][2]
    swapped = C.load_canonical_json(raw)
    swapped["entries"][2], swapped["entries"][3] = swapped["entries"][3], swapped["entries"][2]
    for bad in (edited, dropped, swapped):
        with pytest.raises(CustodyError):
            CU.CustodyLedger.from_bytes(C.canonical_json_bytes(bad))
    truncated = dict(obj, entries=obj["entries"][:-1])
    # a prefix is a valid chain; truncation is caught only against the anchored head
    CU.CustodyLedger.from_bytes(C.canonical_json_bytes(truncated))
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(C.canonical_json_bytes(truncated), expected_head=led.head)
    with pytest.raises(CustodyError):
        CU.CustodyLedger.from_bytes(raw.decode("utf-8"))


def test_ledger_exposes_no_public_mutation_api():
    led = CU.CustodyLedger()
    for name in ("append", "add", "delete", "remove", "pop", "insert", "clear", "set", "update", "__setitem__",
                 "__delitem__"):
        assert not hasattr(led, name), name


def test_internal_mutation_is_detected_by_verify():
    led = CU.CustodyLedger()
    CU.record_generator_freeze(CU.freeze_generator_version(full_spec()), led)
    led._entries[0]["payload"]["spec"]["realization_budgets"][QUAL] = 1  # simulated in-memory tampering
    with pytest.raises(CustodyError):
        led.verify()


# --------------------------------------------------- ordering and exposure law

def test_record_exposure_requires_commitments_and_attestation_first(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    tree = make_tree(tmp_path)
    with pytest.raises(CustodyError):
        expose(fr, led)  # not frozen
    CU.record_generator_freeze(fr, led)
    with pytest.raises(CustodyError):
        expose(fr, led)  # no nonce commitments
    nonces = {DEBUG: dummy_nonce(), QUAL: qnonce}
    for tag in (DEBUG, QUAL):
        CU.record_nonce_commitment(fr, led, class_tag=tag, nonce_commitment=CU.nonce_commitment(nonces[tag]))
    with pytest.raises(CustodyError):
        expose(fr, led)  # realization set not attested (and no withheld commitment)
    root = CU.sealed_root(nonces[DEBUG], fr.generator_semantic_hash, DEBUG, 3)
    CU.attest_realization_set(root, DEBUG, 3, emit(root, DEBUG, 3), led, freeze=fr)
    with pytest.raises(CustodyError, match="withheld"):
        expose(fr, led)  # everything except the withheld commitment
    assert CU.exposure_state(fr, led).exposed is False
    commit_withheld(fr, qnonce, led, tree)
    state = expose(fr, led)
    assert state.exposed is True and state.exposure_count == 1
    assert state.generator_semantic_hash == fr.generator_semantic_hash
    assert CU.exposure_state(fr, led) == state
    with pytest.raises(CustodyError):
        expose(fr, led, class_tag=QUAL, exposure_id="exp-2")  # qualification set not yet attested
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


def test_exposure_record_shape_is_strict(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    prepare(fr, qnonce, led, make_tree(tmp_path))
    good = {"exposure_id": "e", "method_id": "m", "realization_class": DEBUG}
    for bad in (
        {k: v for k, v in good.items() if k != "method_id"},
        dict(good, realization_class="DEV"),
        dict(good, realization_class="SYNTH_OTHER"),
        dict(good, method_id=""),
        dict(good, nonce_hex="00"),
    ):
        with pytest.raises(CustodyError):
            CU.record_exposure(fr, bad, led)
    CU.record_exposure(fr, good, led)
    with pytest.raises(CustodyError):
        CU.record_exposure(fr, good, led)  # duplicate exposure id


def test_attest_realization_set_binds_exact_emitted_set(tmp_path):
    fr, qnonce = make_world()
    led_a, led_b = CU.CustodyLedger(), CU.CustodyLedger()
    roots_a = prepare(fr, qnonce, led_a, make_tree(tmp_path), attest=False)
    root = roots_a[QUAL][1]
    rows = emit(root, QUAL, 4)
    att = CU.attest_realization_set(root, QUAL, 4, rows, led_a, freeze=fr)
    assert att.n_emitted == 4 and att.budget == 4 and att.class_tag == QUAL
    assert att.emitted_set_sha256 == C.semantic_row_set_sha256(rows, ["realization_id"])
    assert att.root_commitment == CU.root_commitment(root)
    assert att.ledger_entry_hash == led_a.head
    # the same emitted set in a different order has the same identity
    CU.record_generator_freeze(fr, led_b)
    CU.record_nonce_commitment(fr, led_b, class_tag=QUAL, nonce_commitment=CU.nonce_commitment(qnonce))
    commit_withheld(fr, qnonce, led_b, make_tree(tmp_path, "tree_b"))
    att_b = CU.attest_realization_set(root, QUAL, 4, list(reversed(rows)), led_b, freeze=fr)
    assert att_b.emitted_set_sha256 == att.emitted_set_sha256


# ----------------------------------------------------------------- successors

def _lower_snr(spec):
    spec["difficulty_grid"]["signal_to_noise"]["level"] = 0.9  # decreasing-harder: 0.5 -> 0.9 is easier


def _raise_snr(spec):
    spec["difficulty_grid"]["signal_to_noise"]["level"] = 0.3  # harder


def test_pre_exposure_revision_may_change_difficulty_and_components(tmp_path):
    parent, _ = make_world()

    def edit(spec):
        _lower_snr(spec)
        spec["parameter_distributions"]["library_size"]["sigma"] = 0.01

    child, _ = make_world(edit)
    led = CU.CustodyLedger()
    CU.record_generator_freeze(parent, led)
    disp = CU.validate_successor_version(parent, child, parent_exposure_state=CU.exposure_state(parent, led),
                                         ledger=led)
    assert disp.disposition == "PRE_EXPOSURE_REVISION"
    assert disp.inherits_qualification is False
    assert disp.easier_dimensions == ("difficulty_grid/signal_to_noise",)
    assert disp.changed_components == ("parameter_distributions",)
    assert disp.floor_generator_semantic_hash is None
    CU.record_generator_freeze(child, led)
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


def test_exposed_successor_that_is_not_easier_is_a_new_version(tmp_path):
    parent, qnonce = make_world()
    led = CU.CustodyLedger()
    prepare(parent, qnonce, led, make_tree(tmp_path))
    expose(parent, led)

    def harder(spec):
        _raise_snr(spec)
        spec["challenge_families"]["control_families"].append("extra_null")
        spec["difficulty_grid"]["new_dimension"] = {"level": 1, "harder_direction": "increasing"}

    child, _ = make_world(harder)
    disp = CU.validate_successor_version(parent, child, parent_exposure_state=CU.exposure_state(parent, led),
                                         ledger=led)
    assert disp.disposition == "SUCCESSOR_NOT_EASIER"
    assert disp.inherits_qualification is False
    assert disp.requires_realism_rerun is True and disp.requires_withheld_check is True
    assert disp.easier_dimensions == () and disp.changed_components == ()
    assert disp.floor_generator_semantic_hash == parent.generator_semantic_hash
    CU.record_generator_freeze(child, led)
    CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)


# --------------------------------------------------------------------- reveal

def test_full_custody_lifecycle_and_reveal(tmp_path):
    fr, qnonce = make_world()
    led = CU.CustodyLedger()
    roots = prepare(fr, qnonce, led, make_tree(tmp_path))
    assert roots[QUAL][0] == qnonce
    expose(fr, led, DEBUG, "exp-debug")
    expose(fr, led, QUAL, "exp-qual")
    CU.record_fit_output_frozen(fr, led, class_tag=QUAL, fit_output_sha256=_h("fit-output"))
    CU.reveal_class_nonce(fr, led, class_tag=QUAL, nonce=qnonce)
    CU.reveal_withheld_family(fr, led, withheld_spec=DUMMY_WITHHELD_SPEC, nonce=qnonce, withheld_class_tag=WTAG)
    replay = CU.CustodyLedger.from_bytes(led.to_bytes(), expected_head=led.head)
    kinds = [e["kind"] for e in replay.entries()]
    assert kinds.count("REVEALED") == 2 and kinds[0] == "GENERATOR_FROZEN"
    assert CU.exposure_state(fr, replay).exposure_count == 2


# ------------------------------------------------------------- secret scanner

DUMMY_SECRET = b"DUMMY-SECRET-not-a-production-value-0123456789"


def _encodings(secret):
    return {
        "raw": secret,
        "hex_lower": secret.hex().encode(),
        "hex_upper": secret.hex().upper().encode(),
        "b64_std": base64.b64encode(secret),
        "b64_std_nopad": base64.b64encode(secret).rstrip(b"="),
        "b64_url": base64.urlsafe_b64encode(secret),
        "b64_url_nopad": base64.urlsafe_b64encode(secret).rstrip(b"="),
        "b64_embedded_offset1": base64.b64encode(b"A" + secret + b"tail"),
        "b64_embedded_offset2": base64.b64encode(b"AB" + secret + b"tail"),
        "b64url_embedded_offset1": base64.urlsafe_b64encode(b"Z" + secret + b"zz"),
    }


def _wrap(text, width, sep=b"\n"):
    return sep.join(text[i:i + width] for i in range(0, len(text), width))


def _wrapped_encodings(secret):
    b64 = base64.b64encode(secret)
    hexs = secret.hex().encode()
    items = [b"0x%02x" % x for x in secret]
    c_array = b"{\n    " + b",\n    ".join(b", ".join(items[i:i + 12]) for i in range(0, len(items), 12)) + b"\n}"
    return {
        "mime_76_crlf": base64.encodebytes(secret).replace(b"\n", b"\r\n"),
        "pem_64": b"-----BEGIN DUMMY-----\n" + _wrap(b64, 64) + b"\n-----END DUMMY-----\n",
        "urlsafe_wrapped_offset1": _wrap(base64.urlsafe_b64encode(b"Q" + secret + b"q"), 60),
        "b64_space_indented": _wrap(b64, 40, b"\n    "),
        "hex_wrapped": _wrap(hexs, 32),
        "hex_colon": b":".join(b"%02x" % x for x in secret),
        "hex_colon_upper": b":".join(b"%02X" % x for x in secret),
        "hex_0x_c_array": c_array,
        "hex_0x_prefixed_run": b"0x" + hexs,
        "python_bytes_repr": repr(secret).encode("ascii"),
        "json_byte_list": json.dumps(list(secret)).encode("ascii"),
        "json_byte_list_compact": json.dumps(list(secret), separators=(",", ":")).encode("ascii"),
        "json_byte_list_wrapped": json.dumps(list(secret), indent=2).encode("ascii"),
        "decimal_big_endian": str(int.from_bytes(secret, "big")).encode("ascii"),
    }


def test_scan_clean_tree_attests_absence_with_only_boolean_and_identity(tmp_path):
    tree = make_tree(tmp_path)
    att = CU.scan_secret_absence(tree, DUMMY_SECRET)
    assert set(att) == {"secret_absent", "tree_identity", "files_scanned"}
    assert att["secret_absent"] is True and att["files_scanned"] == 2
    rows = []
    for rel in ("README.md", "scripts/public_mechanism.py"):
        rows.append({"path": rel, "entry_type": "file", "raw_sha256": C.raw_sha256((tree / rel).read_bytes())})
    assert att["tree_identity"] == C.ordered_registry_digest(rows, ["path"])
    assert CU.scan_secret_absence(tree, DUMMY_SECRET) == att  # deterministic
    (tree / "README.md").write_bytes(b"public fixture tree, edited\n")
    assert CU.scan_secret_absence(tree, DUMMY_SECRET)["tree_identity"] != att["tree_identity"]
    assert CU.require_secret_absence(tree, DUMMY_SECRET)["secret_absent"] is True


@pytest.mark.parametrize("encoding", list(_encodings(DUMMY_SECRET)))
def test_scan_detects_secret_in_any_supported_encoding(tmp_path, encoding):
    tree = make_tree(tmp_path)
    leak = tree / "scripts" / "leaky_module_DUMMY.py"
    leak.write_bytes(b"x = '" + _encodings(DUMMY_SECRET)[encoding] + b"'\n")
    att = CU.scan_secret_absence(tree, DUMMY_SECRET)
    assert att["secret_absent"] is False
    text = repr(att).encode()
    for enc in _encodings(DUMMY_SECRET).values():
        assert enc not in text
    assert b"leaky_module" not in text
    with pytest.raises(CustodyError) as exc:
        CU.require_secret_absence(tree, DUMMY_SECRET)
    msg = str(exc.value).encode()
    assert b"leaky_module" not in msg and DUMMY_SECRET not in msg and DUMMY_SECRET.hex().encode() not in msg


@pytest.mark.parametrize("encoding", list(_wrapped_encodings(b"\x00" * 120)))
def test_scan_detects_wrapped_separated_and_numeric_encodings(tmp_path, encoding):
    secret = secrets.token_bytes(120)  # DUMMY binary secret; long enough for MIME/PEM wrapping
    payload = _wrapped_encodings(secret)[encoding]
    tree = make_tree(tmp_path)
    assert CU.scan_secret_absence(tree, secret)["secret_absent"] is True
    (tree / "leak.txt").write_bytes(b"prefix\n" + payload + b"\nsuffix\n")
    assert CU.scan_secret_absence(tree, secret)["secret_absent"] is False


def test_scan_detects_pretty_printed_canonical_json(tmp_path):
    tree = make_tree(tmp_path)
    preimage = C.canonical_json_bytes(DUMMY_WITHHELD_SPEC)
    pretty = json.dumps(DUMMY_WITHHELD_SPEC, indent=2, sort_keys=True).encode("utf-8")
    assert pretty != preimage
    (tree / "notes.json").write_bytes(pretty)
    assert CU.scan_secret_absence(tree, preimage)["secret_absent"] is False


def test_scan_detects_secret_across_read_chunk_boundary(tmp_path):
    tree = make_tree(tmp_path)
    blob = b"a" * ((1 << 20) - 7) + DUMMY_SECRET + b"b" * 100
    (tree / "big.bin").write_bytes(blob)
    assert CU.scan_secret_absence(tree, DUMMY_SECRET)["secret_absent"] is False
    secret = secrets.token_bytes(48)  # DUMMY: wrapped hex straddling the chunk boundary
    blob = b"z" * ((1 << 20) - 41) + _wrap(b"0x" + secret.hex().encode(), 30)
    (tree / "big2.bin").write_bytes(blob)
    assert CU.scan_secret_absence(tree, secret)["secret_absent"] is False


def test_scan_joins_a_0x_prefix_split_across_the_chunk_boundary(tmp_path):
    secret = secrets.token_bytes(48)  # DUMMY
    text = b", ".join(b"0x%02x" % x for x in secret)
    second_prefix = text.index(b"0x", 1)  # an interior "0x"; split it as "0" | "x"
    blob = b"z" * ((1 << 20) - 1 - second_prefix) + text
    assert blob[(1 << 20) - 1:(1 << 20) + 1] == b"0x"
    tree = make_tree(tmp_path)
    (tree / "c_array.h").write_bytes(blob)
    assert CU.scan_secret_absence(tree, secret)["secret_absent"] is False


def test_scan_flushes_a_trailing_hex_zero_at_end_of_file(tmp_path):
    secret = secrets.token_bytes(31) + b"\x30"  # DUMMY; its hex ends in "0"
    tree = make_tree(tmp_path)
    (tree / "seed.hex").write_bytes(secret.hex().encode())  # no trailing newline
    assert CU.scan_secret_absence(tree, secret)["secret_absent"] is False


def test_scan_detects_secret_in_a_path_name(tmp_path):
    tree = make_tree(tmp_path)
    (tree / ("x_" + DUMMY_SECRET.hex() + ".txt")).write_bytes(b"benign")
    assert CU.scan_secret_absence(tree, DUMMY_SECRET)["secret_absent"] is False


def test_scan_detects_committed_dummy_withheld_preimage(tmp_path):
    tree = make_tree(tmp_path)
    preimage = C.canonical_json_bytes(DUMMY_WITHHELD_SPEC)
    assert CU.scan_secret_absence(tree, preimage)["secret_absent"] is True
    (tree / "configs").mkdir()
    (tree / "configs" / "generator.json").write_bytes(b'{"public":1,"oops":' + preimage + b"}")
    assert CU.scan_secret_absence(tree, preimage)["secret_absent"] is False
    nonce = dummy_nonce()
    (tree / "configs" / "seed.txt").write_bytes(nonce.hex().encode())
    assert CU.scan_secret_absence(tree, nonce)["secret_absent"] is False


def test_scan_skips_git_directory_and_rejects_vacuous_or_weak_input(tmp_path):
    tree = make_tree(tmp_path)
    (tree / ".git" / "objects").mkdir(parents=True)
    (tree / ".git" / "objects" / "blob").write_bytes(DUMMY_SECRET)
    att = CU.scan_secret_absence(tree, DUMMY_SECRET)
    assert att["secret_absent"] is True and att["files_scanned"] == 2
    with pytest.raises(CustodyError):
        CU.scan_secret_absence(tree, b"short-secret")  # < 16 bytes
    with pytest.raises(CustodyError):
        CU.scan_secret_absence(tree, DUMMY_SECRET.decode())
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(CustodyError, match="empty tree"):
        CU.scan_secret_absence(empty, DUMMY_SECRET)
    with pytest.raises(CustodyError):
        CU.scan_secret_absence(tmp_path / "missing", DUMMY_SECRET)


def test_scan_fails_closed_on_unlistable_directory_or_unreadable_file(tmp_path, monkeypatch):
    tree = make_tree(tmp_path)
    real_walk = CU.os.walk

    def walk_with_unlistable_directory(top, onerror=None, followlinks=False):
        yield from real_walk(top, onerror=onerror, followlinks=followlinks)
        onerror(PermissionError("simulated unlistable directory"))

    monkeypatch.setattr(CU.os, "walk", walk_with_unlistable_directory)
    with pytest.raises(CustodyError):
        CU.scan_secret_absence(tree, DUMMY_SECRET)
    monkeypatch.setattr(CU.os, "walk", real_walk)

    def unreadable(*args, **kwargs):
        raise PermissionError("simulated unreadable file")

    monkeypatch.setattr(CU, "_scan_file", unreadable)
    with pytest.raises(CustodyError):
        CU.scan_secret_absence(tree, DUMMY_SECRET)


# ------------------------------------------------- unique withheld code paths

DUMMY_MECHANISM_SOURCE = b'''
def shared_program_kernel(weight, scale):
    return weight * scale


def development_only_noise(scale):
    return scale + 1.0


def dummy_withheld_only_branch(weight):
    return -weight
'''


def _load_dummy_mechanisms(tmp_path):
    path = tmp_path / "dummy_mechanisms.py"
    path.write_bytes(DUMMY_MECHANISM_SOURCE)
    spec = importlib.util.spec_from_file_location("dummy_mechanisms_fixture", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    public = {"dummy_mechanisms.py::" + n.name for n in ast.parse(DUMMY_MECHANISM_SOURCE).body
              if isinstance(n, ast.FunctionDef)}
    return mod, str(path), public


def _exercised(module_file, fn):
    hits = set()

    def profiler(frame, event, arg):
        if event == "call" and frame.f_code.co_filename == module_file:
            hits.add("dummy_mechanisms.py::" + frame.f_code.co_qualname)

    sys.setprofile(profiler)
    try:
        fn()
    finally:
        sys.setprofile(None)
    return hits


def test_withheld_family_over_shared_public_paths_is_allowed(tmp_path):
    mod, path, public = _load_dummy_mechanisms(tmp_path)
    dev = _exercised(path, lambda: (mod.shared_program_kernel(0.5, 2.0), mod.development_only_noise(1.0)))
    withheld = _exercised(path, lambda: mod.shared_program_kernel(0.125, 3.0))  # secret parameterization only
    att = CU.attest_no_unique_withheld_code_path(withheld, dev, public)
    assert set(att) == {"no_unique_withheld_public_path", "public_paths_digest", "development_paths_digest"}
    assert att["no_unique_withheld_public_path"] is True
    assert att["public_paths_digest"] == C.semantic_row_set_sha256(
        [{"code_path": p} for p in public], ["code_path"])


def test_committed_code_path_unique_to_withheld_family_is_a_custody_failure(tmp_path):
    mod, path, public = _load_dummy_mechanisms(tmp_path)
    dev = _exercised(path, lambda: (mod.shared_program_kernel(0.5, 2.0), mod.development_only_noise(1.0)))
    withheld = _exercised(path, lambda: (mod.shared_program_kernel(0.125, 3.0),
                                         mod.dummy_withheld_only_branch(0.125)))
    assert "dummy_mechanisms.py::dummy_withheld_only_branch" in withheld - dev
    with pytest.raises(CustodyError) as exc:
        CU.attest_no_unique_withheld_code_path(withheld, dev, public)
    assert "dummy_withheld_only_branch" not in str(exc.value)  # never echo a withheld path name
    off_repo_public = public - {"dummy_mechanisms.py::dummy_withheld_only_branch"}
    assert CU.attest_no_unique_withheld_code_path(withheld, dev, off_repo_public)[
        "no_unique_withheld_public_path"] is True
