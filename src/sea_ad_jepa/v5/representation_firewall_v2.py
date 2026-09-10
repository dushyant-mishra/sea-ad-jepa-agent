"""Fail-closed representation routing contract for prospective Teacher/Student V5.

V1 blocked a small blacklist of direct z_bio fields.  That is insufficient for
an anti-cheat boundary because aliases (for example dataset_id) and unregistered
auxiliary objectives can bypass a blacklist while remaining semantically the
same shortcut.  V2 therefore uses explicit allowlists for learned-state inputs
and an exact objective registry.

This is a prospective mechanics/governance contract only.  It selects no loss
coefficient, dimension, threshold, schedule, biological target, or training
authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

ALLOWED_DIRECT_Z_BIO_FIELDS = frozenset(
    {
        "common_core_expression",
        "common_core_detection",
    }
)

ALLOWED_DIRECT_Z_OBS_FIELDS = frozenset(
    {
        "measurement_mask",
        "depth",
        "detected_genes",
        "operator_support_state",
    }
)

# These values may exist as identity/provenance/RNG metadata, but they are not
# lawful direct learned-state features.  In particular stable_key is permitted
# for keyed RNG/identity checks, never as a numeric model covariate.
FORBIDDEN_DIRECT_MODEL_FIELDS = frozenset(
    {
        "donor_id",
        "source",
        "matrix_id",
        "operator_index",
        "operator_id",
        "dataset_id",
        "study_id",
        "batch_id",
        "sample_id",
        "cell_id",
        "stable_key",
        "local_row",
        "sample_row",
        "support_fingerprint",
        "pathology",
        "protected_label",
        "sealed_label",
    }
)

REQUIRED_TECHNICAL_INTERVENTIONS = frozenset(
    {"SUPPORT_FAMILY", "MASK_IDENTITY", "EVIDENCE_FRACTION", "MEASUREMENT_DEPTH"}
)
BIOLOGICAL_OBJECTIVES = frozenset(
    {
        "BASE_JEPA_CELL_STATE",
        "RELATIONAL_GEOMETRY",
        "BIOLOGICAL_CHECKPOINT_SELECTION",
        "DOWNSTREAM_BIOLOGY_READOUT",
    }
)
RECONSTRUCTION_OBJECTIVES = frozenset({"GENE_LEDGER_RECONSTRUCTION"})
REGISTERED_OBJECTIVES = BIOLOGICAL_OBJECTIVES | RECONSTRUCTION_OBJECTIVES

# Input routing alone is not sufficient: an objective can consume z_bio and
# still turn a technical reconstruction target into a gradient shortcut.  V2
# therefore freezes the *per-objective learned-state gradient destinations* as
# part of the routing manifest.  Checkpoint selection and downstream readouts
# are evaluation-only.  Gene-ledger reconstruction may condition on detached
# z_bio, but it may train only the observation route/decoder, never z_bio.
EXPECTED_OBJECTIVE_GRADIENT_TARGETS = {
    "BASE_JEPA_CELL_STATE": ("z_bio",),
    "RELATIONAL_GEOMETRY": ("z_bio",),
    "BIOLOGICAL_CHECKPOINT_SELECTION": (),
    "DOWNSTREAM_BIOLOGY_READOUT": (),
    "GENE_LEDGER_RECONSTRUCTION": ("z_obs",),
}


def _string_sequence(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    out = tuple(map(str, value))
    if any(not item for item in out):
        raise ValueError(f"{name} contains an empty field")
    if len(set(out)) != len(out):
        raise ValueError(f"{name} contains duplicate fields")
    return out


def _exact_allowed_fields(
    value: object,
    *,
    name: str,
    allowed: frozenset[str],
) -> tuple[str, ...]:
    fields = _string_sequence(value, name)
    forbidden = sorted(FORBIDDEN_DIRECT_MODEL_FIELDS & set(fields))
    if forbidden:
        raise ValueError(f"forbidden direct model fields in {name}: {forbidden}")
    unknown = sorted(set(fields) - allowed)
    if unknown:
        raise ValueError(
            f"unregistered direct fields in {name}: {unknown}; "
            "new descriptors require an explicit successor authority"
        )
    if not fields:
        raise ValueError(f"{name} must not be empty")
    return fields


@dataclass(frozen=True)
class RepresentationFirewallAuthorityV2:
    biological_state_id: str
    observation_state_id: str
    common_core_anchor_policy_id: str
    same_cell_intervention_policy_id: str
    observation_descriptor_authority_id: str
    reconstruction_routing_policy_id: str
    relational_routing_policy_id: str
    observation_gradient_firewall_policy_id: str
    categorical_identity_embeddings_allowed: bool
    source_adversary_is_default: bool
    pathology_used_for_training: bool

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name.endswith("_id") and (not isinstance(value, str) or not value):
                raise ValueError(f"{name} must be an explicit nonempty authority ID")
        if self.categorical_identity_embeddings_allowed is not False:
            raise ValueError(
                "free categorical donor/source/matrix/operator/dataset identity embeddings are forbidden"
            )
        if self.source_adversary_is_default is not False:
            raise ValueError(
                "source-adversarial erasure is not a default: source can be confounded with legitimate biology"
            )
        if self.pathology_used_for_training is not False:
            raise ValueError("pathology/protected outcomes cannot enter foundation training")


def validate_routing_manifest_v2(manifest: Mapping[str, object]) -> dict[str, object]:
    z_bio_fields = _exact_allowed_fields(
        manifest.get("z_bio_direct_fields"),
        name="z_bio_direct_fields",
        allowed=ALLOWED_DIRECT_Z_BIO_FIELDS,
    )
    z_obs_fields = _exact_allowed_fields(
        manifest.get("z_obs_direct_fields"),
        name="z_obs_direct_fields",
        allowed=ALLOWED_DIRECT_Z_OBS_FIELDS,
    )

    if manifest.get("common_core_anchor_present") is not True:
        raise ValueError("z_bio requires a common-core same-cell anchor")
    if manifest.get("native_support_biology_route") != "PREDICT_COMMON_CORE_ANCHORED_Z_BIO":
        raise ValueError(
            "native support may enter biology only by predicting common-core-anchored z_bio"
        )
    if manifest.get("observation_gradient_into_biology_allowed") is not False:
        raise ValueError(
            "observation-route objectives must not be allowed to write gradients into the biology state"
        )
    if manifest.get("categorical_identity_embeddings_allowed") is not False:
        raise ValueError("categorical identity embeddings must be explicitly disabled")

    interventions = _string_sequence(
        manifest.get("same_cell_interventions"), "same_cell_interventions"
    )
    intervention_set = set(interventions)
    missing = sorted(REQUIRED_TECHNICAL_INTERVENTIONS - intervention_set)
    unknown = sorted(intervention_set - REQUIRED_TECHNICAL_INTERVENTIONS)
    if missing:
        raise ValueError(f"missing same-cell technical interventions: {missing}")
    if unknown:
        raise ValueError(f"unregistered same-cell technical interventions: {unknown}")

    objectives = manifest.get("objective_inputs")
    if not isinstance(objectives, Mapping):
        raise ValueError("objective_inputs must be a mapping")
    names = set(map(str, objectives.keys()))
    missing_objectives = sorted(REGISTERED_OBJECTIVES - names)
    unknown_objectives = sorted(names - REGISTERED_OBJECTIVES)
    if missing_objectives:
        raise ValueError(f"missing registered objectives: {missing_objectives}")
    if unknown_objectives:
        raise ValueError(
            f"unregistered objectives: {unknown_objectives}; all learned objectives must be classified"
        )

    for objective in BIOLOGICAL_OBJECTIVES:
        inputs = _string_sequence(objectives[objective], f"objective_inputs[{objective}]")
        if inputs != ("z_bio",):
            raise ValueError(f"{objective} must consume z_bio only, got {inputs}")

    reconstruction = _string_sequence(
        objectives["GENE_LEDGER_RECONSTRUCTION"],
        "objective_inputs[GENE_LEDGER_RECONSTRUCTION]",
    )
    if reconstruction != ("z_bio", "z_obs"):
        raise ValueError(
            "GENE_LEDGER_RECONSTRUCTION must consume exactly (z_bio, z_obs) and no side channel"
        )

    gradient_routes = manifest.get("objective_gradient_targets")
    if not isinstance(gradient_routes, Mapping):
        raise ValueError("objective_gradient_targets must be a mapping")
    gradient_names = set(map(str, gradient_routes.keys()))
    missing_gradient = sorted(REGISTERED_OBJECTIVES - gradient_names)
    unknown_gradient = sorted(gradient_names - REGISTERED_OBJECTIVES)
    if missing_gradient:
        raise ValueError(f"missing objective gradient routes: {missing_gradient}")
    if unknown_gradient:
        raise ValueError(f"unregistered objective gradient routes: {unknown_gradient}")
    for objective, expected in EXPECTED_OBJECTIVE_GRADIENT_TARGETS.items():
        actual = _string_sequence(
            gradient_routes[objective], f"objective_gradient_targets[{objective}]"
        )
        if actual != expected:
            raise ValueError(
                f"{objective} gradient targets must be exactly {expected}, got {actual}"
            )

    return {
        "passed": True,
        "schema": "JEPA_V5_REPRESENTATION_FIREWALL_V2",
        "z_bio_direct_fields": list(z_bio_fields),
        "z_obs_direct_fields": list(z_obs_fields),
        "registered_objectives": sorted(REGISTERED_OBJECTIVES),
        "objective_gradient_targets": {
            key: list(value) for key, value in sorted(EXPECTED_OBJECTIVE_GRADIENT_TARGETS.items())
        },
        "required_same_cell_interventions": sorted(REQUIRED_TECHNICAL_INTERVENTIONS),
        "categorical_identity_embeddings_allowed": False,
        "observation_gradient_into_biology_allowed": False,
        "training_authorized": False,
    }
