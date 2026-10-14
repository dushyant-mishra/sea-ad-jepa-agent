"""Shared fixtures for the custody tests (production synthetic V3.1.1 Task 2).

Not a test module (no ``test_`` prefix). Every secret produced here is a DUMMY
generated in-test (``secrets.token_bytes``) or a literal visibly labelled DUMMY;
nothing here is, or resembles, a production nonce, withheld specification or
withheld-only code. Files are written only under the caller's pytest
``tmp_path``.
"""
import hashlib
import secrets

import scripts.production_synthetic.canonical_v1 as C
import scripts.production_synthetic.custody_v1 as CU

QUAL = CU.SYNTH_QUALIFICATION
DEBUG = CU.SYNTH_DEBUG
WTAG = "SYNTH_QUALIFICATION_WITHHELD"
ENTRY_FORMAT = "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-ENTRY-V1"
LEDGER_FORMAT = "JEPA-PRODUCTION-SYNTHETIC-CUSTODY-LEDGER-V1"
E1_COMPONENTS = [
    "generator_source", "transitive_dependencies", "parameter_distributions", "mechanism_mixture",
    "observation_calibration_distributions", "stress_regimes", "applicability_control_matrix", "registries",
    "serialization_contract", "realization_budgets",
]

# DUMMY withheld-family specifications: stand-ins so commit/reveal mechanics can be exercised.
DUMMY_WITHHELD_SPEC = {
    "DUMMY_family": {"composition": "DUMMY_pair_of_shared_programs", "weight": 0.125},
    "DUMMY_scoring_rule": "DUMMY",
    "DUMMY_budget": 2,
}
EASIER_WITHHELD_SPEC = dict(DUMMY_WITHHELD_SPEC, DUMMY_family={"composition": "DUMMY_single_program", "weight": 0.5})


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
    """A complete public generator spec WITHOUT the withheld-family commitment."""
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


def full_spec():
    spec = base_spec()
    spec["withheld_family_commitment"] = _h("DUMMY-commitment-placeholder")
    return spec


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


def commit_withheld(freeze, qnonce, ledger, tree, change=None):
    """WITHHELD_COMMITTED after scanning the tree for the qualification nonce and the DUMMY spec bytes."""
    scans = [
        CU.require_nonce_absence(tree, qnonce),
        CU.require_secret_absence(tree, C.canonical_json_bytes(DUMMY_WITHHELD_SPEC)),
    ]
    CU.record_withheld_commitment(
        freeze, ledger, withheld_class_tag=WTAG, nonce_commitment=CU.nonce_commitment(qnonce),
        secret_absence_attestations=scans, code_path_attestation=code_path_attestation(),
        withheld_family_change=change,
    )


def commit_and_attest(freeze, qnonce, ledger, tree, attest=True, change=None):
    """Nonce commitments -> withheld commitment -> attestations; return {class_tag: (nonce, root)}."""
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
            CU.attest_realization_set(freeze, ledger, root=root, class_tag=tag, emitted=emit(root, tag, budget))
    return out


def prepare(freeze, qnonce, ledger, tree, attest=True):
    CU.record_generator_freeze(freeze, ledger)
    return commit_and_attest(freeze, qnonce, ledger, tree, attest)


def expose(freeze, ledger, class_tag=DEBUG, exposure_id="exp-1"):
    return CU.record_exposure(
        freeze, ledger, {"exposure_id": exposure_id, "method_id": METHOD, "realization_class": class_tag}
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
        "justification_source": CU.DEFECT_JUSTIFICATION,
        "incomparable": False,
    }
    rec.update(over)
    return rec


def set_snr(level):
    def edit(spec):
        spec["difficulty_grid"]["signal_to_noise"]["level"] = level  # decreasing is harder
    return edit


def qualify_and_reveal(freeze, qnonce, ledger, withheld=DUMMY_WITHHELD_SPEC, exposure_id="exp-q"):
    expose(freeze, ledger, QUAL, exposure_id)
    CU.record_fit_output_frozen(freeze, ledger, class_tag=QUAL, exposure_id=exposure_id,
                                fit_output_sha256=_h("fit " + exposure_id))
    CU.reveal_withheld_family(freeze, ledger, withheld_spec=withheld, nonce=qnonce, withheld_class_tag=WTAG)


def forge_ledger(entries):
    """Hand-build a hash-chain-valid ledger (chain validity alone is public knowledge)."""
    out, prev = [], "0" * 64
    for i, (kind, payload) in enumerate(entries):
        body = {"format": ENTRY_FORMAT, "index": i, "kind": kind, "payload": payload, "prev_entry_hash": prev}
        h = C.semantic_sha256(body)
        out.append({"index": i, "kind": kind, "payload": payload, "prev_entry_hash": prev, "entry_hash": h})
        prev = h
    return C.canonical_json_bytes({"format": LEDGER_FORMAT, "entries": out}), prev


def withheld_entry(led, freeze):
    return [e["payload"] for e in led.entries()
            if e["kind"] == "WITHHELD_COMMITTED" and e["payload"]["generator_semantic_hash"] == freeze.generator_semantic_hash][0]
