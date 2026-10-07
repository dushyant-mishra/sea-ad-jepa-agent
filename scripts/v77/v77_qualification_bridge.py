#!/usr/bin/env python3
"""Bridge: a V77 synthetic conversion -> the shared QualificationBatchV1 (PR #223), and a
ZERO_UPDATE qualification of the plumbing.

Claim namespace: SYNTHETIC_PIPELINE_ANTICHEAT_REHEARSAL. Runtime-agnostic. The shared interface
is consumed as published at a pinned commit, loaded from a read-only worktree under a private
package name, so this branch neither merges nor modifies the runtime lane's work.

WHAT THIS BRIDGE DECIDES: nothing scientific. Every field the interface requires that belongs to
another lane is set to an explicit UNSET value: the estimand, the thresholds, the target spec, the
split protocol, the evaluation weights and the representation stability protocol. The
representation function of the qualification run is PLUMBING ONLY: it summarises what it was
allowed to see and computes no representation, so the run qualifies the data path, not a model.

WHAT IT AUTHENTICATES, from the producer side:
  feature identity      registry address ids in tensor order, checked against the world's registry
                        digest and address-order digest
  operator identity     every cell's source and operator resolved by NAME against the observer's
                        rosters; the interface refuses an operator outside the cell's source
  measurement support   producer support re-read from the observer shards on an independent path,
                        which the interface requires to equal the batch mask exactly

Visibility classes map one-to-one from the adapter's structures; nothing ORACLE_ONLY enters the
batch, and the oracle record stays outside, sealed.

RESTRICTION ON OBSERVATION CONTEXT, recorded when a3e272ba was accepted as the synthetic plumbing
baseline. Raw source_index and operator_index are authenticated measurement context and
provenance for qualification. They are NOT automatically authorized learned model covariates: a
model given raw study or operator identity can memorise which experiment produced a cell instead
of learning the measurement process. Any production observation-context representation must be
approved by the real-data scientific lane and should encode defensible measurement properties
(depth, coverage, capture, chemistry) rather than unrestricted dataset identity. The plumbing
qualification below passes them as LAWFUL_OPERATOR_CONTEXT only because it learns nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import v77_synthetic_batch_adapter as AD  # noqa: E402

INTERFACE_COMMIT = "f6d63b2f53209786e3c45e7545b9bd442838a3d4"
INTERFACE_MODULES = ("canonical", "protocol", "visibility", "identity", "qsafe", "receipts",
                     "authorities", "lifecycle", "oracle", "pipeline")
UNSET = "UNSET_REQUIRES_APPROVAL"
OBSERVATION_CONTEXT_RESTRICTION = dict(
    raw_identity_fields=["source_index", "operator_index"],
    status="AUTHENTICATED_MEASUREMENT_CONTEXT__NOT_AN_AUTHORIZED_LEARNED_COVARIATE",
    production_observation_context="requires real-data scientific-lane approval; should encode defensible "
                                   "measurement properties, not unrestricted dataset identity")
PACKAGE_NAME = "v77_shared_qualification_interface"


class BridgeContractError(RuntimeError):
    """The conversion cannot be bridged without guessing or deciding, so the bridge refuses."""


def load_interface(worktree: Path):
    worktree = Path(worktree)
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=worktree).stdout.strip()
    if head != INTERFACE_COMMIT:
        raise BridgeContractError(f"interface worktree is at {head or 'unknown'}, not the pinned {INTERFACE_COMMIT}")
    if subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=worktree).stdout.strip():
        raise BridgeContractError("interface worktree is modified; it must be read-only at the pinned commit")
    pkg = worktree / "src" / "sea_ad_jepa" / "qualification"
    if PACKAGE_NAME not in sys.modules:
        spec = importlib.util.spec_from_file_location(PACKAGE_NAME, pkg / "__init__.py",
                                                      submodule_search_locations=[str(pkg)])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE_NAME] = mod
        spec.loader.exec_module(mod)
    ns = {m: importlib.import_module(f"{PACKAGE_NAME}.{m}") for m in INTERFACE_MODULES}
    digests = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(pkg.glob("*.py"))}
    return ns, dict(commit=head, package_file_sha256=digests)


def _rows(mask: np.ndarray) -> tuple:
    return tuple(tuple(bool(x) for x in row) for row in np.asarray(mask, dtype=bool))


def producer_support_rows(world: Path, obs_dir: str, universe: np.ndarray, cells: np.ndarray) -> tuple:
    """Re-read producer support from the observer shards, independently of the adapter's path."""
    odir = Path(world) / "observable_raw" / obs_dir
    man = json.loads(next(odir.glob("*MANIFEST*.json")).read_text())
    n_addr = int(man["n_addresses"])
    want = {int(c): i for i, c in enumerate(cells)}
    out = np.zeros((len(cells), len(universe)), dtype=bool)
    found = 0
    for s in man["shards"]:
        z = np.load(odir / s["file"], allow_pickle=False)
        gci = np.asarray(z["global_cell_index"], dtype=np.int64)
        sup = np.unpackbits(np.asarray(z["support_mask_packed"], dtype=np.uint8), axis=1, count=n_addr).astype(bool)
        for r, c in enumerate(gci):
            if int(c) in want:
                out[want[int(c)]] = sup[r, universe]
                found += 1
    if found != len(cells):
        raise BridgeContractError(f"producer support found for {found} of {len(cells)} cells")
    return _rows(out)


def authenticated_feature_ids(universe: np.ndarray, address_ids, manifest: dict, registry_check: bool) -> tuple:
    if registry_check:
        import v77_address_universe as AU
        fi = manifest.get("feature_identity") or {}
        order = hashlib.sha256("\n".join(map(str, address_ids)).encode()).hexdigest()
        if fi.get("registry_sha256") != AU.REGISTRY_SHA256 or fi.get("address_id_order_sha256") != order:
            raise BridgeContractError("world feature identity does not match the registry and its address order")
    return tuple(str(address_ids[int(i)]) for i in universe)


def build_qualification_batch(Q, conv, *, world: Path, obs_dir: str, universe: np.ndarray, address_ids,
                              registry_check: bool, experiment_run_id: str, realization_id: str,
                              code_commit: str, environment_digest: str):
    canon = Q["canonical"].canonical_digest
    V, I, P = Q["visibility"], Q["identity"], Q["pipeline"]
    man_path = next((Path(world) / "observable_raw" / obs_dir).glob("*MANIFEST*.json"))
    manifest = json.loads(man_path.read_text())
    oi = manifest.get("observation_identity")
    if not oi:
        raise BridgeContractError("world has no producer-side observation identity")
    rule = manifest.get("structural_support_rule")
    if not rule:
        raise BridgeContractError("world records no structural support rule")

    feats = authenticated_feature_ids(universe, address_ids, manifest, registry_check)
    feature_receipt = I.FeatureIdentityReceiptV1.from_ordered_ids(
        registry_ids=feats, reader_axis_ids=feats, tokenizer_axis_ids=feats,
        tensor_feature_axis_ids=feats, synthetic=True)

    cells = np.asarray(conv.global_cell_index, dtype=np.int64)
    obs_ids = tuple(f"{realization_id}:cell{int(c)}" for c in cells)
    roster = tuple(str(s) for s in oi["source_roster"])
    ops = [str(o) for o in oi["operator_ids"]]
    src_idx = tuple(int(i) for i in conv.operator_context.source_index)
    operator_receipt = I.ObservationOperatorIdentityReceiptV1(
        source_roster=roster, source_indices=src_idx,
        source_names=tuple(roster[i] for i in src_idx),
        operator_ids=tuple(ops[int(i)] for i in conv.operator_context.operator_index),
        operator_source_map=tuple((str(o), str(s)) for o, s in oi["operator_source_map"]),
        support_rule_id=str(rule))

    support_receipt = I.MeasurementSupportReceiptV1.from_support_rows(
        observation_ids=obs_ids,
        producer_support_rows=producer_support_rows(world, obs_dir, universe, cells),
        batch_measurement_rows=_rows(conv.model.measurement_mask),
        support_rule_id=str(rule),
        producer_manifest_digest=hashlib.sha256(man_path.read_bytes()).hexdigest())

    donors = [str(d) for d in oi["donor_ids"]]
    donor_ids = tuple(donors[int(i)] for i in conv.split_context.donor_index) if donors else \
        tuple(f"donor{int(i)}" for i in conv.split_context.donor_index)
    query_spec = dict(rule="hidden targets within structural support, measured zeros eligible, each cell "
                           "seeded by (seed, global_cell_index)",
                      hidden_fraction=conv.provenance["hidden_fraction"], seed=conv.provenance["seed"],
                      hidden_target_mask=[list(r) for r in _rows(conv.model.hidden_target_mask)])
    identity = I.QualificationBatchIdentityV1(
        observation_ids=obs_ids,
        feature_receipt_digest=feature_receipt.digest(),
        operator_identity_receipt_digest=operator_receipt.digest(),
        measurement_support_receipt_digest=support_receipt.digest(),
        query_spec_digest=canon(query_spec),
        evidence_mask_digest=canon([list(r) for r in _rows(conv.model.evidence_mask)]),
        measurement_mask_digest=support_receipt.batch_measurement_digest,
        operator_context_digest=operator_receipt.digest(),
        evaluation_weight_digest=canon(UNSET),
        grouping_digest=canon(list(donor_ids)),
        split_digest=canon("NO_SPLIT__ZERO_UPDATE_PLUMBING"),
        target_spec_digest=canon(UNSET))

    F, C = V.FieldDeclaration, V.VisibilityClass
    m, oc, rd = conv.model, conv.operator_context, conv.readout
    fields = (
        P.BatchFieldV1(F("gene_ids", C.MODEL_VISIBLE), [int(x) for x in m.gene_ids[0]]),
        P.BatchFieldV1(F("student_expression", C.MODEL_VISIBLE), m.student_expression.astype(float).tolist()),
        P.BatchFieldV1(F("measurement_mask", C.MODEL_VISIBLE), [list(r) for r in _rows(m.measurement_mask)]),
        P.BatchFieldV1(F("hidden_target_mask", C.MODEL_VISIBLE), [list(r) for r in _rows(m.hidden_target_mask)]),
        P.BatchFieldV1(F("source_index", C.LAWFUL_OPERATOR_CONTEXT), list(src_idx)),
        P.BatchFieldV1(F("operator_index", C.LAWFUL_OPERATOR_CONTEXT), [int(x) for x in oc.operator_index]),
        P.BatchFieldV1(F("visible_library_size", C.LAWFUL_OPERATOR_CONTEXT), [float(x) for x in oc.visible_library_size]),
        P.BatchFieldV1(F("n_measured", C.LAWFUL_OPERATOR_CONTEXT), [int(x) for x in oc.n_measured]),
        P.BatchFieldV1(F("donor_id", C.SPLIT_ONLY), list(donor_ids)),
        P.BatchFieldV1(F("query_counts", C.READOUT_ONLY), rd.query_counts.astype(float).tolist()),
        P.BatchFieldV1(F("full_library_size", C.READOUT_ONLY), [float(x) for x in rd.full_library_size]),
        P.BatchFieldV1(F("global_cell_index", C.PROVENANCE_ONLY), [int(c) for c in cells]),
        P.BatchFieldV1(F("observer_manifest_sha256", C.PROVENANCE_ONLY), support_receipt.producer_manifest_digest),
    )
    adapter_path = HERE / "v77_synthetic_batch_adapter.py"
    batch = P.QualificationBatchV1(
        experiment_run_id=experiment_run_id,
        data_kind=Q["receipts"].DataKind.SYNTHETIC,
        adapter_id="v77_synthetic_batch_adapter",
        adapter_digest=hashlib.sha256(adapter_path.read_bytes()).hexdigest(),
        feature_identity_receipt=feature_receipt,
        operator_identity_receipt=operator_receipt,
        measurement_support_receipt=support_receipt,
        scientific_identity=identity,
        q_safety_policy=Q["qsafe"].QSafetyPolicyV1(tuple(Q["qsafe"].REQUIRED_Q_SAFETY_CHANNELS)),
        fields=fields,
        inference_unit="DONOR",
        inference_group_ids=donor_ids,
        code_commit=code_commit,
        environment_digest=environment_digest,
        synthetic_realization_id=realization_id,
        challenge_partition="DEVELOPMENT_CALIBRATION")
    return batch


def plumbing_protocol(Q):
    PR = Q["protocol"]
    return PR.QualificationProtocolV1(
        governance_digest=PR.APPROVED_V3_GOVERNANCE_DIGEST,
        qualification_contract_version=f"shared-qualification-interface-v1@{INTERFACE_COMMIT[:12]}",
        runtime_interface_version="NONE__NO_RUNTIME_CONSUMED",
        representation_family="GLOBAL_CELL_STATE",
        target_evidence_construction_id=UNSET,
        q_safety_policy_id="qsafe-v1",
        observation_operator_policy_id="v77-producer-identity-by-name-v1",
        biological_evidence_operator_id="v77-student-evidence-visible-counts-v1",
        measurement_depth_operator_id="v77-visible-library-v1",
        split_resampling_protocol_id=UNSET,
        representation_stability_protocol_id=UNSET,
        transport_ood_axes=(UNSET,),
        diagnostic_readout_firewall_id="v77-readout-record-v1",
        unit_of_inference="DONOR",
        estimand_spec=UNSET,
        threshold_status=PR.ThresholdStatus.UNSET_REQUIRES_APPROVAL,
        deciding_numeric_thresholds=UNSET,
        exploratory_thresholds=(),
        execution_mode=PR.ExecutionMode.ZERO_UPDATE_QUALIFICATION,
        claim_ceiling="RNA_REPRESENTATION")


def plumbing_authorities(Q, protocol):
    A = Q["authorities"]
    return A.AuthorityBundleV1(
        scientific=A.ScientificExperimentAuthorityV1(protocol_digest=protocol.digest(),
                                                     scope=A.ExperimentScope.SYNTHETIC_PIPELINE_VALIDITY,
                                                     evaluation_authorized=True),
        mutation=A.MutationAuthorityV1(A.MutationStatus.MUTATION_NOT_AUTHORIZED),
        claim=A.ClaimAuthorityV1(A.ClaimLevel.NO_CLAIM))


def run_plumbing_qualification(Q, batch):
    """ZERO_UPDATE qualification of the data path. The representation function computes no
    representation; it records which fields it was allowed to see, which is what is qualified."""
    seen = {}

    def representation_fn(view):
        seen["model_inputs"] = sorted(view.model_inputs)
        seen["lawful_operator_context"] = sorted(view.lawful_operator_context)
        ev = [sum(1 for m, h in zip(mr, hr) if m and not h)
              for mr, hr in zip(view.model_inputs["measurement_mask"], view.model_inputs["hidden_target_mask"])]
        return {"plumbing_only": True, "visible_evidence_per_cell": ev}

    def readout_fn(rep, rview):
        seen["readout_only"] = sorted(rview.readout_only)
        seen["split_only"] = sorted(rview.split_only)
        return {"plumbing_only": True, "hidden_targets_per_cell":
                [sum(1 for v in row if v) for row in batch.model_view().model_inputs["hidden_target_mask"]]}

    protocol = plumbing_protocol(Q)
    out = Q["pipeline"].run_zero_update_qualification(
        protocol, plumbing_authorities(Q, protocol), batch, representation_fn, readout_fn)
    return protocol, out, seen


def environment_digest() -> str:
    return hashlib.sha256(json.dumps(dict(python=platform.python_version(), numpy=np.__version__,
                                          scipy=scipy.__version__), sort_keys=True).encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--observer-dir", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--interface-worktree", required=True)
    ap.add_argument("--max-cells", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    git = lambda *x: subprocess.run(["git", *x], capture_output=True, text=True, cwd=HERE).stdout.strip()
    mine = ("v77_qualification_bridge.py", "v77_synthetic_batch_adapter.py", "v77_address_universe.py")
    if git("status", "--porcelain", "--untracked-files=no") or not all(git("ls-files", "--", f) for f in mine):
        sys.exit("refusing: the qualification receipt must describe committed code")
    executor_sha256 = {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in mine}
    Q, iface = load_interface(Path(a.interface_worktree))
    import v77_address_universe as AU
    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]
    conv = AD.build_from_world(Path(a.world), a.observer_dir, universe, max_cells=a.max_cells)
    uni = AU.AddressUniverse(7302)
    truth_manifest = Path(a.world) / "hidden_truth" / "TRUTH_MANIFEST.json"
    realization = f"V77_SEED7302_{hashlib.sha256(truth_manifest.read_bytes()).hexdigest()[:16]}"
    head = git("rev-parse", "HEAD")
    batch = build_qualification_batch(Q, conv, world=Path(a.world), obs_dir=a.observer_dir, universe=universe,
                                      address_ids=uni.address_id, registry_check=True,
                                      experiment_run_id=f"v77-zero-update-plumbing-{head[:12]}",
                                      realization_id=realization, code_commit=head,
                                      environment_digest=environment_digest())
    protocol, out, seen = run_plumbing_qualification(Q, batch)
    canon = Q["canonical"].canonical_digest
    rec = dict(
        schema="V77_ZERO_UPDATE_PLUMBING_QUALIFICATION_V1",
        claim_namespace="SYNTHETIC_PIPELINE_ANTICHEAT_REHEARSAL",
        claim_ceiling="NO_CLAIM: qualifies the synthetic data path only; no representation, model or target",
        interface=iface, protocol_digest=protocol.digest(),
        unset_by_design=["estimand_spec", "deciding thresholds", "target_evidence_construction_id",
                         "split_resampling_protocol_id", "representation_stability_protocol_id",
                         "transport_ood_axes", "evaluation weights", "target spec", "split"],
        authority=dict(scope="SYNTHETIC_PIPELINE_VALIDITY", evaluation_authorized=True, mutation="NOT_AUTHORIZED",
                       claim_level="NO_CLAIM", basis="reviewer-lane instruction item 8, relayed by the owner"),
        batch=dict(experiment_run_id=batch.experiment_run_id, n_observations=len(batch.scientific_identity.observation_ids),
                   n_features=len(batch.feature_identity_receipt.tensor_feature_axis_ids),
                   scientific_identity_digest=batch.scientific_identity.digest(),
                   feature_identity_digest=batch.feature_identity_receipt.digest(),
                   operator_identity_digest=batch.operator_identity_receipt.digest(),
                   measurement_support_digest=batch.measurement_support_receipt.digest(),
                   producer_support_digest=batch.measurement_support_receipt.producer_support_digest,
                   batch_measurement_digest=batch.measurement_support_receipt.batch_measurement_digest,
                   field_visibility={f.declaration.name: f.declaration.visibility.value for f in batch.fields},
                   synthetic_realization_id=batch.synthetic_realization_id,
                   challenge_partition=batch.challenge_partition),
        seen_by_the_representation_function=seen,
        frozen_outputs=dict(run_id=out.run_id, output_digest=out.output_digest,
                            provenance_receipt_digest=out.provenance_receipt_digest,
                            mutation_proof_status=out.mutation_proof_status.value,
                            q_safety_execution_proof_status=out.q_safety_execution_proof_status.value),
        oracle=dict(digest=conv.oracle.digest(), status="held outside the batch, sealed, not unblinded"),
        observation_context_restriction=OBSERVATION_CONTEXT_RESTRICTION,
        adapter_provenance_digest=canon(json.loads(json.dumps(conv.provenance, default=str))),
        command=" ".join(["python", "scripts/v77/v77_qualification_bridge.py", *sys.argv[1:]]),
        source_commit=head, provenance_status="CLEAN_COMMITTED_HEAD__EXECUTORS_TRACKED",
        executor_sha256=executor_sha256, no_training_performed=True, no_mutation=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(dict(frozen_outputs=rec["frozen_outputs"], seen=seen, n=rec["batch"]["n_observations"]), indent=1))


if __name__ == "__main__":
    main()
