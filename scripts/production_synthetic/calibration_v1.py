"""V3.1.1 production-synthetic Task 3: observation-only calibration firewall.

Fixture/development mechanics. No real donor data or controller secrets are
embedded; in particular, *no* result here grants authenticated-human,
known-truth, production-realization, FINAL, or training authority. Pinned
content identities must come from an independently authenticated source.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import ceil, isfinite, log
from typing import Mapping
import json


class CalibrationError(ValueError):
    """Fail-closed calibration, provenance or realism contract violation."""


_PROVENANCE = frozenset({
    "AUTHENTICATED_EMPIRICAL_CALIBRATION",
    "PINNED_EXECUTOR_MATHEMATICS",
    "PROSPECTIVE_CONVENTION",
})
_ALLOWED_FEATURES = frozenset({
    "OBSERVATION_DEPTH", "OBSERVATION_DETECTION", "OBSERVATION_MISSINGNESS",
    "OBSERVATION_SUPPORT", "OBSERVATION_FRAGMENT_MULTIPLICITY",
    "OBSERVATION_MODALITY_AVAILABILITY", "OBSERVATION_DONOR_OPERATOR_ALLOCATION",
    "OBSERVATION_MEAN_VARIANCE", "OBSERVATION_CORRELATION_SPECTRUM",
    "OBSERVATION_INTRINSIC_DIMENSION",
})
_ALLOWED_STRATA = frozenset({
    "OBS_DEPTH_BIN", "OBS_DETECTION_BIN", "OBS_OPERATOR",
    "OBS_MODALITY", "OBS_SUPPORT_STATE",
})
_UNIVERSE_INVARIANT_METRICS = frozenset({"OBSERVATION_MEAN_DEPTH"})
_REALISM_NAMES = frozenset({
    "OBS_DEPTH", "DETECTION", "MISSINGNESS", "SUPPORT",
    "OBS_FRAGMENT_MULTIPLICITY", "OBS_MODALITY",
    "MEAN_VARIANCE", "CORRELATION_SPECTRUM", "INTRINSIC_DIMENSION",
    "LIBRARY_ONLY_CEILING", "SOURCE_ONLY_CEILING", "MARKER_ONLY_CEILING",
    "PCA_LINEAR_CEILING",
})


def _hex64(s: object) -> bool:
    return type(s) is str and len(s) == 64 and all(x in "0123456789abcdef" for x in s)


def _finite(x: object) -> bool:
    return type(x) in (int, float) and isfinite(x)


def _strtuple(items: object, *, nonempty: bool = False) -> bool:
    return (
        type(items) is tuple and (not nonempty or bool(items))
        and all(type(x) is str and bool(x) for x in items)
        and len(set(items)) == len(items)
    )


@dataclass(frozen=True)
class CalibrationArtifact:
    """Declared metadata only; caller values are not attestations."""

    content_sha256: str
    source_scope: str
    donors: tuple[str, ...]
    split_role: str
    feature_family: str
    stratification: tuple[str, ...]
    provenance: str


@dataclass(frozen=True)
class NumericProvenance:
    name: str
    value: int | float
    category: str
    identity_sha256: str

    def __post_init__(self) -> None:
        if (
            type(self.name) is not str or not self.name
            or not _finite(self.value)
            or type(self.category) is not str or self.category not in _PROVENANCE
            or not _hex64(self.identity_sha256)
        ):
            raise CalibrationError("decision-bearing number lacks closed provenance or finite value")


def validate_calibration_firewall(
    artifact: CalibrationArtifact, *,
    raw_bytes: bytes,
    independently_pinned_sha256: str,
    expected_source_scope: str,
    eligible_fit_donors: tuple[str, ...],
    excluded_donors: tuple[str, ...],
) -> CalibrationArtifact:
    """Check pinned observation-only input against externally supplied identities.

    Matching a digest is NOT independent authentication of the digest's issuer.
    This function never computes latent human prevalence, disease parameters,
    target truth, or candidate decisions.
    """
    if type(artifact) is not CalibrationArtifact or type(raw_bytes) is not bytes:
        raise CalibrationError("exact calibration artifact and raw bytes required")
    if not _hex64(independently_pinned_sha256) or not _hex64(artifact.content_sha256):
        raise CalibrationError("exact authenticated content digest required")
    actual = sha256(raw_bytes).hexdigest()
    if actual != independently_pinned_sha256 or actual != artifact.content_sha256:
        raise CalibrationError("calibration byte identity differs from pinned source")
    if (
        type(expected_source_scope) is not str or not expected_source_scope
        or type(artifact.source_scope) is not str
        or artifact.source_scope != expected_source_scope
        or artifact.split_role != "CALIBRATION_FIT"
        or artifact.provenance != "AUTHENTICATED_EMPIRICAL_CALIBRATION"
    ):
        raise CalibrationError("calibration source, split or provenance mismatch")
    if not (
        _strtuple(artifact.donors, nonempty=True)
        and _strtuple(eligible_fit_donors, nonempty=True)
        and _strtuple(excluded_donors)
    ):
        raise CalibrationError("calibration donor identities require unique canonical strings")
    donors = set(artifact.donors)
    if donors - set(eligible_fit_donors) or donors & set(excluded_donors):
        raise CalibrationError("calibration donors overlap or escape allowed fit partition")
    if type(artifact.feature_family) is not str or artifact.feature_family not in _ALLOWED_FEATURES:
        raise CalibrationError("biological truth/pathology proxy not eligible as calibration feature")
    if not _strtuple(artifact.stratification) or any(
        x not in _ALLOWED_STRATA for x in artifact.stratification
    ):
        raise CalibrationError("pathology, diagnosis, source-as-disease proxy or unapproved stratification")
    return artifact


def validate_address_universe_agnostic(
    metric_name: str,
    pilot_values: Mapping[str, float],
    full_values: Mapping[str, float],
    *,
    pilot_n_addresses: int,
    full_n_addresses: int,
    full_universe_sha256: str,
    expected_full_universe_sha256: str,
) -> bool:
    """Strict *fixture-level* cross-universe invariance check.

    Only a prespecified observation statistic can pass; a detected-feature
    envelope from the 96-gene pilot is ineligible. A matching synthetic witness
    is not a substitute for a human-data receipt or authenticated 41k values.
    """
    if (
        type(metric_name) is not str or metric_name not in _UNIVERSE_INVARIANT_METRICS
        or type(pilot_n_addresses) is not int or pilot_n_addresses != 96
        or type(full_n_addresses) is not int or full_n_addresses != 41238
        or not _hex64(full_universe_sha256)
        or not _hex64(expected_full_universe_sha256)
        or full_universe_sha256 != expected_full_universe_sha256
    ):
        raise CalibrationError("address-universe agnosticism has not been demonstrated")
    if type(pilot_values) is not dict or type(full_values) is not dict:
        raise CalibrationError("explicit exact-keyed cross-universe fixtures required")
    if not pilot_values or set(pilot_values) != set(full_values):
        raise CalibrationError("same scientific units must be inspected in both universes")
    for key, value in pilot_values.items():
        if type(key) is not str or not key or not _finite(value):
            raise CalibrationError("invalid pilot universe statistic")
        other = full_values[key]
        if not _finite(other) or float(value) != float(other):
            raise CalibrationError("pilot/full universe statistic is not invariant")
    return True


@dataclass(frozen=True)
class PrecisionTarget:
    """Hoeffding width for bounded [0,1] *independent* units; not power."""

    epsilon: float
    alpha: float

    def __post_init__(self) -> None:
        if (
            not _finite(self.epsilon) or not 0 < self.epsilon < 1
            or not _finite(self.alpha) or not 0 < self.alpha < 1
        ):
            raise CalibrationError("precision width and tail probability must be pre-frozen within (0,1)")


def derive_budget_from_precision(targets: Mapping[str, PrecisionTarget]) -> dict[str, int]:
    """Prospective non-adaptive precision lower bounds, not a biology power law.

    The bound applies only to independent [0,1] unit-level summaries. Donor
    biological independence must be assessed by a separate qualification;
    technical thinning draws can never increase biological donor count.
    """
    if type(targets) is not dict or set(targets) != {"donors", "worlds", "nulls"}:
        raise CalibrationError("all three prospective precision channels are required")
    out: dict[str, int] = {}
    for name, item in targets.items():
        if type(item) is not PrecisionTarget:
            raise CalibrationError("precision budgets must be typed frozen targets")
        n = ceil(log(2.0 / item.alpha) / (2.0 * item.epsilon ** 2))
        if n <= 0 or n > 10**9:
            raise CalibrationError("precision budget cannot be represented safely")
        out[name] = n
    return out


def _contract_parts(contract: "RealismContract") -> dict[str, object]:
    return {
        "metrics": [
            [name, [float(low), float(high)]]
            for name, (low, high) in contract.metric_bands
        ],
        "adjustable_observation_parameters": list(contract.adjustable_observation_parameters),
        "max_iterations": contract.max_iterations,
        "generator_version_family_sha256": contract.version_family_sha256,
        "authority_scope": contract.authority_scope,
    }


def _contract_digest(contract: "RealismContract") -> str:
    raw = json.dumps(_contract_parts(contract), sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


@dataclass(frozen=True)
class RealismContract:
    """Immutable prospective fixture criteria. Never selects biology parameters."""

    contract_sha256: str
    metric_bands: tuple[tuple[str, tuple[float, float]], ...]
    adjustable_observation_parameters: tuple[str, ...]
    max_iterations: int
    version_family_sha256: str
    authority_scope: str

    def __post_init__(self) -> None:
        if not _hex64(self.contract_sha256) or not _hex64(self.version_family_sha256):
            raise CalibrationError("realism contract requires exact frozen source identities")
        if (
            type(self.metric_bands) is not tuple or not self.metric_bands
            or type(self.max_iterations) is not int or self.max_iterations < 1
            or type(self.authority_scope) is not str
            or self.authority_scope != "SYNTH_DEBUG_ONLY"
            or not _strtuple(self.adjustable_observation_parameters, nonempty=True)
        ):
            raise CalibrationError("only frozen fixture realism contract is executable here")
        if any(not x.startswith("OBS_") for x in self.adjustable_observation_parameters):
            raise CalibrationError("biology parameter cannot be realism-tuned")
        names = []
        for entry in self.metric_bands:
            if type(entry) is not tuple or len(entry) != 2:
                raise CalibrationError("metric band must be exact pair")
            name, band = entry
            if type(name) is not str or name not in _REALISM_NAMES:
                raise CalibrationError("candidate outcome or unlisted realism metric refused")
            if (
                type(band) is not tuple or len(band) != 2
                or not _finite(band[0]) or not _finite(band[1]) or band[0] > band[1]
            ):
                raise CalibrationError("invalid metric acceptance band")
            names.append(name)
        if len(names) != len(set(names)):
            raise CalibrationError("duplicate realism metric names")


@dataclass(frozen=True)
class RealismState:
    """Append-only conceptual fixture state; external durable custody is separate."""

    contract_state_sha256: str
    contract_sha256: str
    versions_tested: tuple[str, ...]
    first_passing_version: str | None
    status: str

    @classmethod
    def initial(cls, contract: RealismContract) -> "RealismState":
        if type(contract) is not RealismContract:
            raise CalibrationError("typed realism contract required")
        return cls(_contract_digest(contract), contract.contract_sha256, (), None, "SEARCHING")


def advance_realism_iteration(
    contract: RealismContract,
    state: RealismState,
    *,
    version_sha256: str,
    metrics: Mapping[str, float],
) -> RealismState:
    """First jointly passing *fixture* version terminates search irreversibly."""
    if type(contract) is not RealismContract or type(state) is not RealismState:
        raise CalibrationError("typed contract and state required")
    if (
        state.contract_sha256 != contract.contract_sha256
        or state.contract_state_sha256 != _contract_digest(contract)
        or state.status != "SEARCHING"
        or state.first_passing_version is not None
    ):
        raise CalibrationError("realism criteria moved or terminal search was reopened")
    if not _hex64(version_sha256) or version_sha256 in state.versions_tested:
        raise CalibrationError("realism generator version must be unique and exact")
    if len(state.versions_tested) >= contract.max_iterations:
        raise CalibrationError("frozen realism iteration budget exhausted")
    bands = dict(contract.metric_bands)
    if type(metrics) is not dict or set(metrics) != set(bands):
        raise CalibrationError("metric roster differs from frozen contract")
    if not all(_finite(x) for x in metrics.values()):
        raise CalibrationError("nonfinite/forged realism metric")
    passing = all(low <= metrics[name] <= high for name, (low, high) in bands.items())
    versions = state.versions_tested + (version_sha256,)
    if passing:
        return RealismState(state.contract_state_sha256, state.contract_sha256,
                            versions, version_sha256, "FIRST_JOINT_PASS_FROZEN")
    if len(versions) >= contract.max_iterations:
        return RealismState(state.contract_state_sha256, state.contract_sha256,
                            versions, None, "REALISM_NOT_QUALIFIED")
    return RealismState(state.contract_state_sha256, state.contract_sha256,
                        versions, None, "SEARCHING")
