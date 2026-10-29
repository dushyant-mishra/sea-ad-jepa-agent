"""Non-promoting G7 E3 -> terminal V3 *composed* fixture entry point.

This is the only new integration path proposed by the #476 review repair.
It snapshots every caller-controlled object, verifies exact rights/atom
content through the existing E3 binder, checks that the terminal rows consumed
by V3 are exactly the bound rows, then invokes the existing V3 decision law.

The legacy directly callable V3 function is intentionally NOT modified: its
historical fixtures and decisions need reproducibility. Direct legacy calls
are not authenticated E3 decisions. No current source/rights issuer, physical
atom identity, donor identity, depth provenance or known-truth attestation is
created by this composition.
"""
from __future__ import annotations

from scripts.v5 import td_real_g7_content_enforcement_v1 as E3
from scripts.v5 import td_real_g7_terminal_decision_v3 as V3


def adjudicate_fixture_g7_e3_v3_composed(
    *, manifest, full_atoms, levels, expected_pins, required_sources,
    rows, reference_input_binding_sha256, decision_qualification,
    reference_artifact, alpha=0.01
):
    """Bind -> immutable snapshot -> V3, returning NO HUMAN authority.

    There is ONE prevalidation immutable input snapshot. The binder is called
    on that snapshot and the V3 reducer receives the same frozen row objects.
    The caller cannot mutate this run after the snapshot. A hash comparison
    here is input consistency, not trusted physical source authentication.
    """
    (manifest, full_atoms, levels, expected_pins, required_sources,
     rows, reference_input_binding_sha256, decision_qualification,
     reference_artifact, alpha) = E3._snapshot(
        [manifest, full_atoms, levels, expected_pins, required_sources,
         rows, reference_input_binding_sha256, decision_qualification,
         reference_artifact, alpha],
        "composed E3/V3 fixture transaction",
    )
    bound = E3.bind_g7_terminal_inputs_e3(
        manifest=manifest,
        full_atoms=full_atoms,
        levels=levels,
        expected_pins=expected_pins,
        required_sources=required_sources,
        rows=rows,
        reference_input_binding_sha256=reference_input_binding_sha256,
    )
    if bound["status"] != "E3_TERMINAL_INPUTS_BOUND_FIXTURE_ONLY":
        raise E3.G7ContentError("composed path lacks successful E3 binding")
    exact_rows = E3.canonical_sha256(sorted(
        rows, key=lambda row: (row["source"], row["donor_id"])
    ))
    if exact_rows != bound["deciding_rows_sha256"]:
        raise E3.G7ContentError("V3 row snapshot differs from E3 bound evidence")
    if bound["input_binding_sha256"] != reference_input_binding_sha256:
        raise E3.G7ContentError("composed reference binding differs from E3 source")
    if type(reference_artifact) is not dict or (
        reference_artifact.get("input_binding_sha256") != reference_input_binding_sha256
    ):
        raise E3.G7ContentError("V3 reference not tied to bound E3 fixture input")

    try:
        decision = V3.adjudicate_g7_terminal_v3(
            rows=rows, required_sources=required_sources,
            decision_qualification=decision_qualification,
            reference_artifact=reference_artifact, alpha=alpha,
        )
    except V3.G7DecisionError:
        raise E3.G7ContentError("V3 rejected the composed fixture input") from None
    if type(decision) is not dict or decision.get("authority") != V3.NO_AUTHORITY:
        raise E3.G7ContentError("V3 produced unexpected authority or receipt shape")
    # Do not return V3 donor details, private E3 rows or any asserted physical
    # source claim. An apparent V3 PASS is mechanically possible even if one
    # physical donor was misrepresented as several specimen IDs.
    return {
        "schema": "JEPA_TD_G7_E3_V3_COMPOSED_FIXTURE_V1",
        "status": "E3_BIND_TO_V3_COMPOSED_FIXTURE_ONLY",
        "v3_mechanics_status": decision["status"],
        "bound_unit_count": bound["bound_unit_count"],
        "deciding_rows_sha256": bound["deciding_rows_sha256"],
        "input_binding_sha256": bound["input_binding_sha256"],
        "external_source_authenticated": False,
        "physical_atom_identity_authenticated": False,
        "independent_donor_identity_authenticated": False,
        "q_excluded_library_provenance_authenticated": False,
        "reference_issuer_authenticated": False,
        "known_truth_issuer_authenticated": False,
        "human_g7_authorized": False,
        "stage4_authorized": False,
        "real_training_authorized": False,
        "authority_effect": "NONE",
    }
