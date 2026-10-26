"""V3.1.1 production-synthetic Task 3: observation-only calibration firewall.

Fixture/development mechanics. No real donor data or controller secrets are
embedded; in particular, *no* result here grants authenticated-human,
known-truth, production-realization, FINAL, or training authority.

Authority is fail-closed. A caller-supplied digest, donor list, split label or
statistic is never promoted to authentication:

* ``AUTHENTICATED_EMPIRICAL_CALIBRATION`` is reachable only for a content
  digest present in the code-pinned ``_AUTHENTICATED_CALIBRATION_REGISTRY``.
  V1 pins none, so V1 can only report consistency, never authentication.
* Address-universe invariance for real reuse is not demonstrable in V1; the
  check returns an explicitly non-authoritative fixture status.
* Realism search state is issued only by this module, once per generator
  family per process, and is not durable across processes (a STOP_B
  prerequisite that remains open).
* Authority-bearing outputs (``CalibrationCheck``, ``RealismState``) are issued
  handles backed by private copies that never leave the module. Consumers must
  call ``verify_calibration_check`` / ``verify_realism_state`` at every use;
  hand-built, stale, token-swapped or mutated handles are refused. Inputs are
  re-validated at use because construction-time checks do not survive
  ``object.__setattr__``.

Which artifacts, split authority and universe registries get pinned is a
deciding-lane decision; this module only fails closed until they exist.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields as dataclass_fields, replace
from hashlib import sha256
from math import ceil, isfinite, log
from threading import Lock
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
_PROTECTED_ROLES = frozenset({"VALIDATION", "ORACLE", "RESERVED", "DEVELOPMENT"})
_UNIVERSE_INVARIANT_METRICS = frozenset({"OBSERVATION_MEAN_DEPTH"})
_REALISM_NAMES = frozenset({
    "OBS_DEPTH", "DETECTION", "MISSINGNESS", "SUPPORT",
    "OBS_FRAGMENT_MULTIPLICITY", "OBS_MODALITY",
    "MEAN_VARIANCE", "CORRELATION_SPECTRUM", "INTRINSIC_DIMENSION",
    "LIBRARY_ONLY_CEILING", "SOURCE_ONLY_CEILING", "MARKER_ONLY_CEILING",
    "PCA_LINEAR_CEILING",
})

# Code-pinned authority registries. Empty in V1: nothing is authenticated until
# the deciding lane pins independently authenticated identities here.
_AUTHENTICATED_CALIBRATION_REGISTRY: frozenset[str] = frozenset()
_PINNED_PILOT_UNIVERSE_SHA256: str | None = None
_PINNED_FULL_UNIVERSE_SHA256: str | None = None

UNAUTHENTICATED_FIXTURE = "CONSISTENT_UNAUTHENTICATED_FIXTURE"
AUTHENTICATED = "AUTHENTICATED_EMPIRICAL_CALIBRATION"
UNIVERSE_FIXTURE_ONLY = "FIXTURE_WITNESS_ONLY__CALIBRATION_INELIGIBLE"


def _hex64(s: object) -> bool:
    return type(s) is str and len(s) == 64 and all(x in "0123456789abcdef" for x in s)


def _finite(x: object) -> bool:
    if type(x) not in (int, float):
        return False
    try:
        return isfinite(x)
    except OverflowError:
        return False


def _strtuple(items: object, *, nonempty: bool = False) -> bool:
    return (
        type(items) is tuple and (not nonempty or bool(items))
        and all(type(x) is str and bool(x) for x in items)
        and len(set(items)) == len(items)
    )


def _exact_str(x: object) -> bool:
    return type(x) is str and bool(x)


def _exact_equal(a: object, b: object) -> bool:
    """Equality that refuses subclasses at every depth and never calls an overridable __eq__."""
    if type(a) is not type(b):
        return False
    kind = type(a)
    if a is None:
        return True
    if kind is str:
        return str.__eq__(a, b)
    if kind is int:
        return int.__eq__(a, b)
    if kind is float:
        return float.__eq__(a, b)
    if kind is tuple:
        return len(a) == len(b) and all(_exact_equal(x, y) for x, y in zip(a, b))
    return False


def _same_fields(cls, public: object, private: object, *, skip: frozenset[str] = frozenset()) -> bool:
    for f in dataclass_fields(cls):
        if f.name in skip:
            continue
        theirs = object.__getattribute__(public, f.name)
        mine = object.__getattribute__(private, f.name)
        if type(mine) is CalibrationArtifact:
            if type(theirs) is not type(mine) or not _same_fields(type(mine), theirs, mine):
                return False
        elif not _exact_equal(theirs, mine):
            return False
    return True


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

    def __post_init__(self) -> None:
        _validate_artifact_fields(self)


def _validate_artifact_fields(a: CalibrationArtifact) -> None:
    """Re-run at every use: construction-time checks do not survive object.__setattr__."""
    if type(a) is not CalibrationArtifact or (
        not _hex64(object.__getattribute__(a, "content_sha256"))
        or not _exact_str(object.__getattribute__(a, "source_scope"))
        or not _strtuple(object.__getattribute__(a, "donors"), nonempty=True)
        or not _exact_str(object.__getattribute__(a, "split_role"))
        or not _exact_str(object.__getattribute__(a, "feature_family"))
        or not _strtuple(object.__getattribute__(a, "stratification"))
        or not _exact_str(object.__getattribute__(a, "provenance"))
    ):
        raise CalibrationError("calibration artifact fields must be exact canonical types")


# Issued firewall outcomes: public handle -> private copy, keyed by an issuance token.
_CHECK_LOCK = Lock()
_ISSUED_CHECKS: dict[object, tuple["CalibrationCheck", "CalibrationCheck"]] = {}


@dataclass(frozen=True)
class CalibrationCheck:
    """Firewall outcome, issued only by ``validate_calibration_firewall``.

    Authority is re-derived by ``verify_calibration_check``: the object must be
    the issued handle, unmutated against the module's private copy, and an
    AUTHENTICATED status must still be backed by the code-pinned registry.
    """

    artifact: CalibrationArtifact
    status: str
    _token: object | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.status) is not str or self.status not in {AUTHENTICATED, UNAUTHENTICATED_FIXTURE}:
            raise CalibrationError("calibration check status is closed")
        if self.status == AUTHENTICATED and (
            type(self.artifact) is not CalibrationArtifact
            or self.artifact.content_sha256 not in _AUTHENTICATED_CALIBRATION_REGISTRY
        ):
            raise CalibrationError("AUTHENTICATED status requires a code-pinned authenticated artifact")

    @property
    def provenance(self) -> str:
        return AUTHENTICATED if self.authenticated else UNAUTHENTICATED_FIXTURE

    @property
    def authenticated(self) -> bool:
        try:
            return verify_calibration_check(self).status == AUTHENTICATED
        except CalibrationError:
            return False


def verify_calibration_check(check: CalibrationCheck) -> CalibrationCheck:
    """Return ``check`` only if it is the issued, unmutated handle; refuse anything else.

    The module's private copy is never returned, so a caller cannot edit it.
    Verify again at every use: a later mutation of the handle is refused then.
    """
    if type(check) is not CalibrationCheck:
        raise CalibrationError("exact calibration check required")
    issued = _ISSUED_CHECKS.get(object.__getattribute__(check, "_token"))
    if issued is None or issued[0] is not check:
        raise CalibrationError("calibration check was not issued by the firewall")
    public, private = issued
    if not _same_fields(CalibrationCheck, check, private, skip=frozenset({"_token"})):
        raise CalibrationError("issued calibration check was mutated after issuance")
    if private.status == AUTHENTICATED and private.artifact.content_sha256 not in _AUTHENTICATED_CALIBRATION_REGISTRY:
        raise CalibrationError("authenticated identity is no longer pinned")
    return check  # the verified public handle; the private copy never leaves the module


def _issue_check(artifact: CalibrationArtifact, status: str) -> CalibrationCheck:
    token = object()
    private = CalibrationCheck(replace(artifact), status, token)
    public = CalibrationCheck(replace(artifact), status, token)
    with _CHECK_LOCK:
        _ISSUED_CHECKS[token] = (public, private)
    return public


@dataclass(frozen=True)
class NumericProvenance:
    name: str
    value: int | float
    category: str
    identity_sha256: str

    def __post_init__(self) -> None:
        validate_numeric_provenance(self)


def validate_numeric_provenance(p: NumericProvenance) -> NumericProvenance:
    """Re-run at every use: construction-time checks do not survive object.__setattr__."""
    if type(p) is not NumericProvenance:
        raise CalibrationError("exact numeric provenance required")
    name = object.__getattribute__(p, "name")
    value = object.__getattribute__(p, "value")
    category = object.__getattribute__(p, "category")
    identity = object.__getattribute__(p, "identity_sha256")
    if (
        not _exact_str(name)
        or not _finite(value)
        or type(category) is not str or category not in _PROVENANCE
        or not _hex64(identity)
    ):
        raise CalibrationError("decision-bearing number lacks closed provenance or finite value")
    if category == AUTHENTICATED and identity not in _AUTHENTICATED_CALIBRATION_REGISTRY:
        raise CalibrationError(
            "AUTHENTICATED_EMPIRICAL_CALIBRATION must reference a code-pinned authenticated artifact"
        )
    return p


def validate_calibration_firewall(
    artifact: CalibrationArtifact, *,
    raw_bytes: bytes,
    independently_pinned_sha256: str,
    expected_source_scope: str,
    eligible_fit_donors: tuple[str, ...],
    protected_partitions: Mapping[str, tuple[str, ...]],
) -> CalibrationCheck:
    """Check observation-only input for consistency; authenticate only via the code-pinned registry.

    Matching a caller-supplied digest is NOT authentication. ``protected_partitions``
    must name every protected role (validation, oracle, reserved, development),
    each non-empty. This function never computes latent human prevalence,
    disease parameters, target truth, or candidate decisions.
    """
    if type(artifact) is not CalibrationArtifact or type(raw_bytes) is not bytes:
        raise CalibrationError("exact calibration artifact and raw bytes required")
    _validate_artifact_fields(artifact)
    if not _hex64(independently_pinned_sha256):
        raise CalibrationError("exact content digest required")
    actual = sha256(raw_bytes).hexdigest()
    if actual != independently_pinned_sha256 or actual != artifact.content_sha256:
        raise CalibrationError("calibration byte identity differs from pinned source")
    if (
        not _exact_str(expected_source_scope)
        or artifact.source_scope != expected_source_scope
        or artifact.split_role != "CALIBRATION_FIT"
        or artifact.provenance != AUTHENTICATED
    ):
        raise CalibrationError("calibration source, split or provenance mismatch")
    if not _strtuple(eligible_fit_donors, nonempty=True):
        raise CalibrationError("calibration donor identities require unique canonical strings")
    if type(protected_partitions) is not dict or set(protected_partitions) != _PROTECTED_ROLES:
        raise CalibrationError("every protected partition (validation, oracle, reserved, development) is required")
    protected: set[str] = set()
    for role in sorted(_PROTECTED_ROLES):
        members = dict.__getitem__(protected_partitions, role)
        if not _strtuple(members, nonempty=True):
            raise CalibrationError(f"protected partition {role} must be a non-empty canonical donor tuple")
        if protected & set(members):
            raise CalibrationError("protected partitions must be disjoint donor sets")
        protected.update(members)
    donors = set(artifact.donors)
    eligible = set(eligible_fit_donors)
    if eligible & protected:
        raise CalibrationError("fit-eligible donors overlap a protected partition")
    if donors - eligible or donors & protected:
        raise CalibrationError("calibration donors overlap or escape allowed fit partition")
    if artifact.feature_family not in _ALLOWED_FEATURES:
        raise CalibrationError("biological truth/pathology proxy not eligible as calibration feature")
    if any(x not in _ALLOWED_STRATA for x in artifact.stratification):
        raise CalibrationError("pathology, diagnosis, source-as-disease proxy or unapproved stratification")
    status = AUTHENTICATED if actual in _AUTHENTICATED_CALIBRATION_REGISTRY else UNAUTHENTICATED_FIXTURE
    return _issue_check(artifact, status)


@dataclass(frozen=True)
class UniverseCheck:
    """Outcome of the cross-universe check. Only ``calibration_eligible`` bears authority."""

    metric_name: str
    n_units: int
    status: str

    def __post_init__(self) -> None:
        if (
            type(self.metric_name) is not str or self.metric_name not in _UNIVERSE_INVARIANT_METRICS
            or type(self.n_units) is not int or self.n_units < 1
            or type(self.status) is not str or self.status != UNIVERSE_FIXTURE_ONLY
        ):
            raise CalibrationError("universe check status is closed to the V1 fixture-only value")

    @property
    def calibration_eligible(self) -> bool:
        return False


def validate_address_universe_agnostic(
    metric_name: str,
    pilot_values: Mapping[str, float],
    full_values: Mapping[str, float],
    *,
    pilot_n_addresses: int,
    full_n_addresses: int,
    full_universe_sha256: str,
    expected_full_universe_sha256: str,
) -> UniverseCheck:
    """Strict *fixture-level* cross-universe invariance witness; never real eligibility in V1.

    Only a prespecified observation statistic is considered; a detected-feature
    envelope from the 96-gene pilot is ineligible. Caller-computed statistics and
    caller-matched digests cannot demonstrate §22.13 invariance, so the result
    is always ``FIXTURE_WITNESS_ONLY__CALIBRATION_INELIGIBLE`` until pinned
    universe registries and an authenticated per-address computation exist.
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
    for key, value in dict.items(pilot_values):
        if type(key) is not str or not key or not _finite(value):
            raise CalibrationError("invalid pilot universe statistic")
        other = dict.__getitem__(full_values, key)
        if not _finite(other) or float(value) != float(other):
            raise CalibrationError("pilot/full universe statistic is not invariant")
    return UniverseCheck(metric_name, len(pilot_values), UNIVERSE_FIXTURE_ONLY)


@dataclass(frozen=True)
class PrecisionTarget:
    """Hoeffding width for bounded [0,1] *independent* units; not power."""

    epsilon: float
    alpha: float

    def __post_init__(self) -> None:
        _validate_precision(self)


def _validate_precision(t: "PrecisionTarget") -> None:
    """Re-run at every use: construction-time checks do not survive object.__setattr__."""
    epsilon = object.__getattribute__(t, "epsilon")
    alpha = object.__getattribute__(t, "alpha")
    if (
        not _finite(epsilon) or not 0 < epsilon < 1
        or not _finite(alpha) or not 0 < alpha < 1
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
        _validate_precision(item)
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
    """Immutable prospective fixture criteria. Never selects biology parameters.

    ``contract_sha256`` must equal the content digest of the contract itself;
    use ``RealismContract.frozen(...)`` to compute it.
    """

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
        if self.contract_sha256 != _contract_digest(self):
            raise CalibrationError("realism contract identity must equal its own content digest")

    @classmethod
    def frozen(cls, *, metric_bands, adjustable_observation_parameters, max_iterations,
               version_family_sha256, authority_scope) -> "RealismContract":
        probe = object.__new__(cls)
        for key, value in dict(
            metric_bands=metric_bands,
            adjustable_observation_parameters=adjustable_observation_parameters,
            max_iterations=max_iterations,
            version_family_sha256=version_family_sha256,
            authority_scope=authority_scope,
        ).items():
            object.__setattr__(probe, key, value)
        try:
            digest = _contract_digest(probe)
        except (TypeError, ValueError, OverflowError) as exc:
            raise CalibrationError("realism contract parts are not canonically serializable") from exc
        return cls(digest, metric_bands, adjustable_observation_parameters, max_iterations,
                   version_family_sha256, authority_scope)


# Process-local realism custody. One contract and one search per generator family
# per process; states are issued by this module only, and each issued state is
# checked against a private copy that is never returned. Not durable across
# processes: persistent custody is a STOP_B prerequisite that remains open.
_REALISM_LOCK = Lock()
_REALISM_FAMILY_LEASES: dict[str, "RealismContract"] = {}  # version family -> private contract snapshot
_REALISM_PUBLIC: dict[object, "RealismState"] = {}    # token -> current public state
_REALISM_PRIVATE: dict[object, "RealismState"] = {}   # token -> private copy


@dataclass(frozen=True)
class RealismState:
    """Module-issued fixture search state; external durable custody is separate."""

    contract_state_sha256: str
    contract_sha256: str
    versions_tested: tuple[str, ...]
    first_passing_version: str | None
    status: str
    _token: object | None = field(default=None, repr=False, compare=False)

    @classmethod
    def initial(cls, contract: RealismContract) -> "RealismState":
        if type(contract) is not RealismContract:
            raise CalibrationError("typed realism contract required")
        snapshot = _snapshot_contract(contract)
        digest = _contract_digest(snapshot)
        with _REALISM_LOCK:
            if snapshot.version_family_sha256 in _REALISM_FAMILY_LEASES:
                raise CalibrationError(
                    "realism search already opened for this generator family in this process; "
                    "re-initialisation, replay or re-contracting is refused"
                )
            _REALISM_FAMILY_LEASES[snapshot.version_family_sha256] = snapshot
            private = cls(digest, snapshot.contract_sha256, (), None, "SEARCHING", object())
            return _issue_state(private)


def _snapshot_contract(contract: RealismContract) -> RealismContract:
    """Re-validate every field now (mutation may follow construction) into a private copy."""
    return RealismContract(*(object.__getattribute__(contract, f.name) for f in dataclass_fields(RealismContract)))


def _issue_state(private: RealismState) -> RealismState:
    public = replace(private)
    _REALISM_PRIVATE[private._token] = private
    _REALISM_PUBLIC[private._token] = public
    return public


def _current_private_state(state: RealismState) -> RealismState:
    token = object.__getattribute__(state, "_token")
    if token is None or _REALISM_PUBLIC.get(token) is not state:
        raise CalibrationError("realism state is not the current module-issued state")
    private = _REALISM_PRIVATE[token]
    for f in dataclass_fields(RealismState):
        if f.name == "_token":
            continue
        if not _exact_equal(object.__getattribute__(state, f.name), object.__getattribute__(private, f.name)):
            raise CalibrationError("issued realism state was mutated after issuance")
    return private


def verify_realism_state(state: RealismState) -> RealismState:
    """Return ``state`` only if it is the current module-issued, unmutated handle.

    Downstream consumers must call this before trusting ``status`` or
    ``first_passing_version``; a hand-built or stale state is refused.
    """
    if type(state) is not RealismState:
        raise CalibrationError("exact realism state required")
    with _REALISM_LOCK:
        _current_private_state(state)
    return state  # the verified public handle; the private copy never leaves the module


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
    with _REALISM_LOCK:
        s = _current_private_state(state)
        frozen = _REALISM_FAMILY_LEASES.get(object.__getattribute__(contract, "version_family_sha256"))
        if frozen is None or not _same_fields(RealismContract, contract, frozen):
            raise CalibrationError("realism contract differs from the snapshot frozen at search start")
        digest = _contract_digest(frozen)
        if (
            s.contract_sha256 != frozen.contract_sha256
            or s.contract_state_sha256 != digest
            or s.status != "SEARCHING"
            or s.first_passing_version is not None
        ):
            raise CalibrationError("realism criteria moved or terminal search was reopened")
        if not _hex64(version_sha256) or version_sha256 in s.versions_tested:
            raise CalibrationError("realism generator version must be unique and exact")
        if len(s.versions_tested) >= frozen.max_iterations:
            raise CalibrationError("frozen realism iteration budget exhausted")
        bands = dict(frozen.metric_bands)
        if type(metrics) is not dict or set(metrics) != set(bands):
            raise CalibrationError("metric roster differs from frozen contract")
        if any(type(k) is not str for k in metrics) or not all(_finite(x) for x in dict.values(metrics)):
            raise CalibrationError("nonfinite/forged realism metric")
        passing = all(low <= dict.__getitem__(metrics, name) <= high for name, (low, high) in bands.items())
        versions = s.versions_tested + (version_sha256,)
        if passing:
            nxt = replace(s, versions_tested=versions, first_passing_version=version_sha256,
                          status="FIRST_JOINT_PASS_FROZEN")
        elif len(versions) >= frozen.max_iterations:
            nxt = replace(s, versions_tested=versions, status="REALISM_NOT_QUALIFIED")
        else:
            nxt = replace(s, versions_tested=versions)
        return _issue_state(nxt)
