"""Unified Task 4 sealed campaign lifecycle.

Custody mechanics only: no biological interpretation, registry promotion,
Stage 4, or training authority. FINAL transitions re-resolve current authority
through Task4AuthorityHarness; caller-created GREEN status objects are never
accepted as authority. Development campaigns remain permanently non-authorizing.

Task 4 V1 also maintains an in-process lifecycle provenance registry. Public
campaign fields describe state but are not proof that the state was reached by
lawful transitions. Directly constructed or copied-and-mutated campaign objects
therefore fail closed. This process-local registry is mechanics-only and is not
an external authority or a substitute for persistent cross-process custody.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import hashlib
import inspect
import json
from threading import Lock
from typing import Iterable, Mapping

from .task4_authority_barrier_v1 import Task4AuthorityHarness, Task4BarrierStatus


class Task4ChallengeCustodyError(ValueError):
    pass


def _canonical(payload: Mapping[str, object]) -> bytes:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _hex(value: object, n: int) -> bool:
    return type(value) is str and len(value) == n and all(ch in "0123456789abcdef" for ch in value)


_REQUIRED_64 = (
    "task2_manifest_sha", "task3_registry_sha", "producer_actor_identity",
    "executor_actor_identity", "controller_actor_identity", "adjudicator_actor_identity",
    "challenge_generator_policy_sha", "realization_schema_sha", "rng_policy_sha",
    "challenge_family_sha", "adjudication_contract_sha", "multiplicity_policy_sha",
    "publication_policy_sha", "genesis_ledger_identity",
)
_REQUIRED_DEPENDENCY_KEYS = frozenset(_REQUIRED_64 + (
    "registry_unit_identities", "challenge_generator_code_sha", "authority_scope",
    "authority_restrictions", "qualification_budget",
))


def validate_campaign_dependencies(dependencies: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(dependencies, Mapping):
        raise Task4ChallengeCustodyError("campaign dependencies must be a mapping")
    supplied = set(dependencies)
    if supplied != _REQUIRED_DEPENDENCY_KEYS:
        missing = sorted(_REQUIRED_DEPENDENCY_KEYS - supplied)
        extra = sorted(supplied - _REQUIRED_DEPENDENCY_KEYS)
        raise Task4ChallengeCustodyError(f"campaign dependency contract mismatch missing={missing} extra={extra}")
    for field_name in _REQUIRED_64:
        if not _hex(dependencies[field_name], 64):
            raise Task4ChallengeCustodyError(f"{field_name} must be exact lowercase 64-hex identity")
    if not _hex(dependencies["challenge_generator_code_sha"], 40):
        raise Task4ChallengeCustodyError("challenge_generator_code_sha must be exact lowercase 40-hex identity")
    units = dependencies["registry_unit_identities"]
    if type(units) not in {tuple, list} or not units:
        raise Task4ChallengeCustodyError("registry_unit_identities must be non-empty ordered pairs")
    normalized_units = []
    seen_unit_ids = set()
    for pair in units:
        if type(pair) not in {tuple, list} or len(pair) != 2:
            raise Task4ChallengeCustodyError("registry unit identity entry must be (unit_id, unit_sha)")
        unit_id, unit_sha = pair
        if type(unit_id) is not str or not unit_id or unit_id in seen_unit_ids or not _hex(unit_sha, 64):
            raise Task4ChallengeCustodyError("registry_unit_identities must bind unique unit IDs to exact SHA-256 identities")
        seen_unit_ids.add(unit_id)
        normalized_units.append((unit_id, unit_sha))
    actors = [dependencies[k] for k in ("producer_actor_identity", "executor_actor_identity", "controller_actor_identity", "adjudicator_actor_identity")]
    if len(set(actors)) != len(actors):
        raise Task4ChallengeCustodyError("producer/executor/controller/adjudicator actors must be pairwise distinct")
    scope = dependencies["authority_scope"]
    if type(scope) is not str or not scope:
        raise Task4ChallengeCustodyError("authority_scope must be non-empty text")
    restrictions = dependencies["authority_restrictions"]
    if type(restrictions) not in {tuple, list} or any(type(x) is not str or not x for x in restrictions):
        raise Task4ChallengeCustodyError("authority_restrictions must be a closed sequence of non-empty tokens")
    budget = dependencies["qualification_budget"]
    if type(budget) is not int or budget <= 0:
        raise Task4ChallengeCustodyError("qualification_budget must be positive integer")
    out = dict(dependencies)
    out["registry_unit_identities"] = tuple(normalized_units)
    out["authority_restrictions"] = tuple(restrictions)
    return out


class CampaignState(str, Enum):
    CAMPAIGN_CREATED = "CAMPAIGN_CREATED"
    DEFINITION_SEALED = "DEFINITION_SEALED"
    REALIZATION_SET_SEALED = "REALIZATION_SET_SEALED"
    EXPOSURE_ACTIVE = "EXPOSURE_ACTIVE"
    ALL_REQUIRED_OUTPUTS_FROZEN = "ALL_REQUIRED_OUTPUTS_FROZEN"
    HIDDEN_MATERIAL_REVEALED = "HIDDEN_MATERIAL_REVEALED"
    REGENERATION_VERIFIED = "REGENERATION_VERIFIED"
    CUSTODY_COMPLETE = "CUSTODY_COMPLETE"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True)
class ExposureRecord:
    campaign_identity: str
    exposure_id: str
    realization_id: str
    realization_content_sha256: str
    method_scientific_identity: str
    ordinal: int

    def identity_tuple(self) -> tuple[str, str, str, str, int]:
        return (
            self.exposure_id,
            self.realization_id,
            self.realization_content_sha256,
            self.method_scientific_identity,
            self.ordinal,
        )


@dataclass(frozen=True)
class QualificationCampaign:
    campaign_id: str
    dependencies: Mapping[str, object]
    namespace: str
    promotion_authority: str
    state: CampaignState
    campaign_identity: str
    sealed_definition_sha256: str | None = None
    sealed_realization_root: str | None = None
    exposures_consumed: int = 0
    sealed_budget: int = 0
    exposed_realization_ids: tuple[str, ...] = ()
    issued_exposures: tuple[tuple[str, str, str, str, int], ...] = ()
    frozen_outputs: tuple[tuple[str, str], ...] = ()
    terminal_statuses: tuple[tuple[str, str], ...] = ()
    _lifecycle_token: object | None = field(default=None, repr=False, compare=False)

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "QUALIFICATION_CAMPAIGN",
            "campaign_id": self.campaign_id,
            "dependencies": dict(self.dependencies),
            "namespace": self.namespace,
            "promotion_authority": self.promotion_authority,
            "state": self.state.value,
            "campaign_identity": self.campaign_identity,
            "sealed_definition_sha256": self.sealed_definition_sha256,
            "sealed_realization_root": self.sealed_realization_root,
            "exposures_consumed": self.exposures_consumed,
            "sealed_budget": self.sealed_budget,
            "exposed_realization_ids": list(self.exposed_realization_ids),
            "issued_exposures": [list(x) for x in self.issued_exposures],
            "frozen_outputs": [list(x) for x in self.frozen_outputs],
            "terminal_statuses": [list(x) for x in self.terminal_statuses],
        }


# Process-local lifecycle mechanics. This registry proves only that the object
# passed through this module's public transition functions in this process. It
# is intentionally excluded from serialized campaign payloads and confers no
# cross-process or external authority.
_LIFECYCLE_DIGESTS: dict[object, str] = {}
_REGENERATION_EXECUTIONS: dict[object, str] = {}
# Non-authorizing in-process campaign-identity leases. Prevent a duplicate
# create_campaign call from minting a fresh zero-spend lifecycle token for the
# same finite exam. Cross-process uniqueness still requires external custody.
_CAMPAIGN_IDENTITY_LEASES: set[str] = set()
_CAMPAIGN_CREATION_LOCK = Lock()


def _campaign_state_digest(campaign: QualificationCampaign) -> str:
    return _sha(campaign.to_payload())


def _register_campaign(campaign: QualificationCampaign) -> QualificationCampaign:
    token = campaign._lifecycle_token
    if token is None:
        raise Task4ChallengeCustodyError("campaign lacks process-local lifecycle provenance")
    _LIFECYCLE_DIGESTS[token] = _campaign_state_digest(campaign)
    return campaign


def _assert_lifecycle_current(campaign: QualificationCampaign) -> None:
    if not isinstance(campaign, QualificationCampaign):
        raise Task4ChallengeCustodyError("campaign must be a QualificationCampaign")
    token = campaign._lifecycle_token
    if token is None:
        raise Task4ChallengeCustodyError("campaign was not created through the lawful lifecycle")
    expected = _LIFECYCLE_DIGESTS.get(token)
    actual = _campaign_state_digest(campaign)
    if expected is None or expected != actual:
        raise Task4ChallengeCustodyError("campaign state lacks current lawful transition provenance")


def _advance_campaign(campaign: QualificationCampaign, **changes: object) -> QualificationCampaign:
    _assert_lifecycle_current(campaign)
    advanced = replace(campaign, **changes)
    token = campaign._lifecycle_token
    assert token is not None
    _LIFECYCLE_DIGESTS[token] = _campaign_state_digest(advanced)
    return advanced


@dataclass(frozen=True)
class SealedChallengeDefinition:
    campaign_identity: str
    family: str
    hidden_spec_commitment: str
    namespace: str

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "SEALED_CHALLENGE_DEFINITION",
            "campaign_identity": self.campaign_identity,
            "family": self.family,
            "hidden_spec_commitment": self.hidden_spec_commitment,
            "namespace": self.namespace,
        }


@dataclass(frozen=True)
class SealedRealizationSet:
    campaign_identity: str
    definition_sha256: str
    realization_ids: tuple[str, ...]
    content_sha256s: tuple[str, ...]
    challenge_classes: tuple[str, ...]
    budget: int
    sealed_root: str

    def to_payload(self) -> dict[str, object]:
        return {
            "object_role": "SEALED_REALIZATION_SET",
            "campaign_identity": self.campaign_identity,
            "definition_sha256": self.definition_sha256,
            "realization_ids": list(self.realization_ids),
            "content_sha256s": list(self.content_sha256s),
            "challenge_classes": list(self.challenge_classes),
            "budget": self.budget,
            "sealed_root": self.sealed_root,
        }


@dataclass(frozen=True)
class MethodOutputFreezeReceipt:
    exposure_id: str
    realization_id: str
    method_scientific_identity: str
    output_sha256: str


@dataclass(frozen=True)
class SealedQualificationReveal:
    campaign_identity: str
    hidden_spec_sha256: str
    sealed_root: str


@dataclass(frozen=True)
class RegenerationVerification:
    campaign_identity: str
    sealed_root: str
    verified: bool
    generator_code_sha: str
    generator_policy_sha: str
    rng_policy_sha: str
    execution_digest: str
    authority_effect: str = "NONE"


def _campaign_identity(campaign_id: str, dependencies: Mapping[str, object], namespace: str) -> str:
    return _sha({"campaign_id": campaign_id, "dependencies": dict(dependencies), "namespace": namespace})


def _guard_final(campaign: QualificationCampaign | None, authority_harness: Task4AuthorityHarness | None) -> None:
    if campaign is not None and campaign.namespace != "FINAL":
        return
    if not isinstance(authority_harness, Task4AuthorityHarness):
        raise Task4ChallengeCustodyError("FINAL transition requires Task4AuthorityHarness current-state re-resolution")
    try:
        authority_harness.current_status()
    except Exception as exc:
        raise Task4ChallengeCustodyError(f"FINAL transition authority re-resolution failed: {type(exc).__name__}") from exc


def create_campaign(campaign_id: str, dependencies: Mapping[str, object], *, barrier_status: Task4BarrierStatus | None, namespace: str, authority_harness: Task4AuthorityHarness | None = None) -> QualificationCampaign:
    if type(campaign_id) is not str or not campaign_id:
        raise Task4ChallengeCustodyError("campaign_id must be non-empty")
    if namespace not in {"DEVELOPMENT", "FINAL"}:
        raise Task4ChallengeCustodyError("unknown campaign namespace")
    deps = validate_campaign_dependencies(dependencies)
    if namespace == "FINAL":
        _guard_final(None, authority_harness)
        promotion_authority = "CUSTODY_ONLY"
    else:
        promotion_authority = "NONE"
    identity = _campaign_identity(campaign_id, deps, namespace)
    campaign = QualificationCampaign(
        campaign_id,
        deps,
        namespace,
        promotion_authority,
        CampaignState.CAMPAIGN_CREATED,
        identity,
        _lifecycle_token=object(),
    )
    with _CAMPAIGN_CREATION_LOCK:
        if identity in _CAMPAIGN_IDENTITY_LEASES:
            raise Task4ChallengeCustodyError(
                "campaign identity already claimed in this process; cannot reset finite-exam exposure budget"
            )
        _register_campaign(campaign)
        _CAMPAIGN_IDENTITY_LEASES.add(identity)
    return campaign


def assert_same_campaign_identity(campaign: QualificationCampaign, campaign_id: str, dependencies: Mapping[str, object]) -> None:
    _assert_lifecycle_current(campaign)
    deps = validate_campaign_dependencies(dependencies)
    if _campaign_identity(campaign_id, deps, campaign.namespace) != campaign.campaign_identity:
        raise Task4ChallengeCustodyError("campaign ID/dependency mutation creates a new campaign identity")


def seal_definition(campaign: QualificationCampaign, *, family: str, hidden_spec: bytes, authority_harness: Task4AuthorityHarness | None = None):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    if campaign.state is not CampaignState.CAMPAIGN_CREATED:
        raise Task4ChallengeCustodyError("challenge definition can seal only from CAMPAIGN_CREATED")
    if type(hidden_spec) is not bytes or not hidden_spec or type(family) is not str or not family:
        raise Task4ChallengeCustodyError("challenge family and hidden specification must be non-empty")
    definition = SealedChallengeDefinition(campaign.campaign_identity, family, hashlib.sha256(hidden_spec).hexdigest(), campaign.namespace)
    definition_sha = _sha(definition.to_payload())
    return _advance_campaign(campaign, state=CampaignState.DEFINITION_SEALED, sealed_definition_sha256=definition_sha), definition


def _validated_rows(rows: Iterable[Mapping[str, object]], budget: int):
    seq = list(rows)
    if type(budget) is not int or budget <= 0 or len(seq) != budget:
        raise Task4ChallengeCustodyError("realization inventory must exactly equal frozen budget")
    ids, digests, classes = [], [], []
    for row in seq:
        if set(row) != {"realization_id", "content_sha256", "challenge_class"}:
            raise Task4ChallengeCustodyError("realization row has unknown or missing fields")
        rid, digest, cls = row["realization_id"], row["content_sha256"], row["challenge_class"]
        if type(rid) is not str or not rid or rid in ids or not _hex(digest, 64) or digest in digests or type(cls) is not str or not cls:
            raise Task4ChallengeCustodyError("invalid or duplicate realization identity/content/class")
        ids.append(rid)
        digests.append(digest)
        classes.append(cls)
    return tuple(ids), tuple(digests), tuple(classes)


def _definition_identity(definition: SealedChallengeDefinition) -> str:
    return _sha(definition.to_payload())


def _realization_root(sealed: SealedRealizationSet) -> str:
    if not (
        type(sealed.realization_ids) is tuple
        and type(sealed.content_sha256s) is tuple
        and type(sealed.challenge_classes) is tuple
        and len(sealed.realization_ids) == len(sealed.content_sha256s) == len(sealed.challenge_classes) == sealed.budget
    ):
        raise Task4ChallengeCustodyError("sealed realization set has invalid shape")
    return _sha({
        "campaign_identity": sealed.campaign_identity,
        "definition_sha256": sealed.definition_sha256,
        "realization_ids": sealed.realization_ids,
        "content_sha256s": sealed.content_sha256s,
        "challenge_classes": sealed.challenge_classes,
        "budget": sealed.budget,
    })


def _validate_bound_definition(campaign: QualificationCampaign, definition: SealedChallengeDefinition) -> None:
    if definition.campaign_identity != campaign.campaign_identity:
        raise Task4ChallengeCustodyError("sealed definition campaign identity mismatch")
    actual = _definition_identity(definition)
    if campaign.sealed_definition_sha256 is None or actual != campaign.sealed_definition_sha256:
        raise Task4ChallengeCustodyError("challenge definition differs from exact committed definition")


def _validate_bound_realization_set(campaign: QualificationCampaign, sealed: SealedRealizationSet) -> None:
    if sealed.campaign_identity != campaign.campaign_identity:
        raise Task4ChallengeCustodyError("sealed realization campaign identity mismatch")
    if campaign.sealed_definition_sha256 is None or sealed.definition_sha256 != campaign.sealed_definition_sha256:
        raise Task4ChallengeCustodyError("sealed realization set references a different challenge definition")
    if campaign.sealed_realization_root is None:
        raise Task4ChallengeCustodyError("campaign has no committed realization-set root")
    recomputed = _realization_root(sealed)
    if recomputed != sealed.sealed_root or sealed.sealed_root != campaign.sealed_realization_root:
        raise Task4ChallengeCustodyError("realization set differs from exact committed finite exam")



# A real trusted generator executor is not available in this repository.
# This closed, deterministic generator exercises DEVELOPMENT custody mechanics
# only. Neither its code SHA nor its in-process receipt is external authority.
_DEV_GENERATOR_POLICY_SHA = _sha({
    "schema": "TASK4_DEVELOPMENT_FIXTURE_GENERATOR_POLICY_V1",
    "domain": "SYNTHETIC_ONLY",
    "content": "SHA256_CANONICAL_SEEDED_ROWS",
})
_DEV_RNG_POLICY_SHA = _sha({
    "schema": "TASK4_DEVELOPMENT_FIXTURE_RNG_POLICY_V1",
    "algorithm": "SHA256_COUNTER_DERIVATION",
    "seed_sources": ["campaign_identity", "hidden_spec_sha256"],
})


def _development_fixture_generator(campaign_identity: str, hidden_spec: bytes, budget: int):
    """Freshly compute synthetic rows without reading sealed/caller-provided rows."""
    seed = _sha({
        "campaign_identity": campaign_identity,
        "hidden_spec_sha256": hashlib.sha256(hidden_spec).hexdigest(),
        "rng_policy_sha": _DEV_RNG_POLICY_SHA,
    })
    return tuple({
        "realization_id": f"r{ordinal}",
        "content_sha256": _sha({
            "seed": seed,
            "ordinal": ordinal,
            "generator_policy_sha": _DEV_GENERATOR_POLICY_SHA,
        }),
        "challenge_class": "SYNTHETIC_DEVELOPMENT",
    } for ordinal in range(budget))


# Pin this exact DEVELOPMENT generator object and the helpers its code resolves.
# Hashing inspect.getsource alone cannot distinguish a copied code object
# executing in an attacker-supplied global namespace. These process-local
# checks are defense in depth only: they are NOT an independent trust root.
_PINNED_DEV_GENERATOR_FUNCTION = _development_fixture_generator
_PINNED_DEV_GENERATOR_CODE = _development_fixture_generator.__code__
_PINNED_DEV_ROW_HASH = _sha
_PINNED_DEV_SHA256 = hashlib.sha256


def development_fixture_generator_identities() -> dict[str, str]:
    """Pin actual fixture implementation source, policy and RNG contract."""
    return {
        "challenge_generator_code_sha": hashlib.sha1(
            inspect.getsource(_development_fixture_generator).encode("utf-8")
        ).hexdigest(),
        "challenge_generator_policy_sha": _DEV_GENERATOR_POLICY_SHA,
        "rng_policy_sha": _DEV_RNG_POLICY_SHA,
    }


def _assert_development_generator_contract(campaign: QualificationCampaign) -> None:
    if campaign.namespace != "DEVELOPMENT" or campaign.promotion_authority != "NONE":
        raise Task4ChallengeCustodyError("in-process fixture generator is DEVELOPMENT-only and non-authorizing")
    if (
        _development_fixture_generator is not _PINNED_DEV_GENERATOR_FUNCTION
        or _development_fixture_generator.__code__ is not _PINNED_DEV_GENERATOR_CODE
        or _development_fixture_generator.__globals__ is not globals()
        or _sha is not _PINNED_DEV_ROW_HASH
        or hashlib.sha256 is not _PINNED_DEV_SHA256
    ):
        raise Task4ChallengeCustodyError(
            "DEVELOPMENT generator execution environment differs from the pinned module implementation"
        )
    expected = development_fixture_generator_identities()
    if any(campaign.dependencies[key] != val for key, val in expected.items()):
        raise Task4ChallengeCustodyError("generator source/policy/RNG differs from frozen DEVELOPMENT fixture contract")


def generate_development_fixture_rows(
    campaign: QualificationCampaign,
    definition: SealedChallengeDefinition,
    *,
    hidden_spec: bytes,
):
    """Generate a fresh synthetic realization inventory before first exposure."""
    _assert_lifecycle_current(campaign)
    if campaign.state is not CampaignState.DEFINITION_SEALED:
        raise Task4ChallengeCustodyError("synthetic inventory generation requires sealed definition before exposure")
    _validate_bound_definition(campaign, definition)
    if type(hidden_spec) is not bytes or hashlib.sha256(hidden_spec).hexdigest() != definition.hidden_spec_commitment:
        raise Task4ChallengeCustodyError("synthetic generator input differs from committed hidden specification")
    _assert_development_generator_contract(campaign)
    return _development_fixture_generator(campaign.campaign_identity, hidden_spec, campaign.dependencies["qualification_budget"])


def seal_realization_set(campaign: QualificationCampaign, definition: SealedChallengeDefinition, rows: Iterable[Mapping[str, object]], *, budget: int, authority_harness: Task4AuthorityHarness | None = None):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    if campaign.state is not CampaignState.DEFINITION_SEALED:
        raise Task4ChallengeCustodyError("realization set requires matching sealed definition")
    _validate_bound_definition(campaign, definition)
    if budget != campaign.dependencies["qualification_budget"]:
        raise Task4ChallengeCustodyError("realization budget differs from frozen campaign qualification budget")
    ids, digests, classes = _validated_rows(rows, budget)
    definition_sha = _definition_identity(definition)
    root = _sha({
        "campaign_identity": campaign.campaign_identity,
        "definition_sha256": definition_sha,
        "realization_ids": ids,
        "content_sha256s": digests,
        "challenge_classes": classes,
        "budget": budget,
    })
    sealed = SealedRealizationSet(campaign.campaign_identity, definition_sha, ids, digests, classes, budget, root)
    return _advance_campaign(
        campaign,
        state=CampaignState.REALIZATION_SET_SEALED,
        sealed_budget=budget,
        sealed_realization_root=root,
    ), sealed


def _issued_exposure_is_exact(campaign: QualificationCampaign, exposure: ExposureRecord) -> bool:
    return exposure.campaign_identity == campaign.campaign_identity and exposure.identity_tuple() in campaign.issued_exposures


def issue_exposure(campaign: QualificationCampaign, sealed: SealedRealizationSet, *, realization_id: str, method_scientific_identity: str, authority_harness: Task4AuthorityHarness | None = None):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    if campaign.state not in {CampaignState.REALIZATION_SET_SEALED, CampaignState.EXPOSURE_ACTIVE}:
        raise Task4ChallengeCustodyError("exposure is not legal in current campaign state")
    _validate_bound_realization_set(campaign, sealed)
    if realization_id not in sealed.realization_ids:
        raise Task4ChallengeCustodyError("realization is not in this committed finite exam")
    if realization_id in campaign.exposed_realization_ids:
        raise Task4ChallengeCustodyError("committed realization already exposed; rename/rerun cannot reset exposure")
    if not _hex(method_scientific_identity, 64):
        raise Task4ChallengeCustodyError("method scientific identity must be exact lowercase SHA-256")
    idx = sealed.realization_ids.index(realization_id)
    ordinal = campaign.exposures_consumed + 1
    exposure = ExposureRecord(campaign.campaign_identity, f"exp-{ordinal}", realization_id, sealed.content_sha256s[idx], method_scientific_identity, ordinal)
    return _advance_campaign(
        campaign,
        state=CampaignState.EXPOSURE_ACTIVE,
        exposures_consumed=ordinal,
        exposed_realization_ids=campaign.exposed_realization_ids + (realization_id,),
        issued_exposures=campaign.issued_exposures + (exposure.identity_tuple(),),
    ), exposure


def record_exposure_terminal(campaign: QualificationCampaign, exposure: ExposureRecord, *, terminal_status: str, authority_harness: Task4AuthorityHarness | None = None):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    if campaign.state not in {CampaignState.EXPOSURE_ACTIVE, CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN}:
        raise Task4ChallengeCustodyError("terminal exposure accounting is closed after hidden material reveal")
    allowed = {"EVALUATED", "TECHNICAL_FAILURE", "UNSUPPORTED_NOT_ESTIMABLE", "DEFECT_INVALIDATED"}
    if terminal_status not in allowed or not _issued_exposure_is_exact(campaign, exposure):
        raise Task4ChallengeCustodyError("invalid or hand-constructed terminal exposure accounting")
    existing = dict(campaign.terminal_statuses)
    if exposure.realization_id in existing and existing[exposure.realization_id] != terminal_status:
        raise Task4ChallengeCustodyError("terminal accounting cannot be rewritten")
    existing[exposure.realization_id] = terminal_status
    return _advance_campaign(campaign, terminal_statuses=tuple(sorted(existing.items())))


def freeze_method_output(campaign: QualificationCampaign, exposure: ExposureRecord, *, output_sha256: str, authority_harness: Task4AuthorityHarness | None = None):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    if campaign.state is not CampaignState.EXPOSURE_ACTIVE or not _hex(output_sha256, 64) or not _issued_exposure_is_exact(campaign, exposure):
        raise Task4ChallengeCustodyError("invalid or hand-constructed output freeze")
    frozen = dict(campaign.frozen_outputs)
    if exposure.realization_id in frozen:
        raise Task4ChallengeCustodyError("output already frozen and cannot mutate")
    frozen[exposure.realization_id] = output_sha256
    state = CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN if len(frozen) == campaign.sealed_budget else CampaignState.EXPOSURE_ACTIVE
    receipt = MethodOutputFreezeReceipt(exposure.exposure_id, exposure.realization_id, exposure.method_scientific_identity, output_sha256)
    return _advance_campaign(campaign, state=state, frozen_outputs=tuple(sorted(frozen.items()))), receipt


def reveal_hidden_material(campaign: QualificationCampaign, definition: SealedChallengeDefinition, sealed: SealedRealizationSet, *, hidden_spec: bytes, authority_harness: Task4AuthorityHarness | None = None):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    if campaign.state is not CampaignState.ALL_REQUIRED_OUTPUTS_FROZEN:
        raise Task4ChallengeCustodyError("hidden material reveal preconditions not met")
    _validate_bound_definition(campaign, definition)
    _validate_bound_realization_set(campaign, sealed)
    realized = set(sealed.realization_ids)
    if set(dict(campaign.terminal_statuses)) != realized:
        raise Task4ChallengeCustodyError("hidden material reveal requires complete pre-reveal terminal accounting")
    digest = hashlib.sha256(hidden_spec).hexdigest()
    if digest != definition.hidden_spec_commitment:
        raise Task4ChallengeCustodyError("hidden material does not match sealed commitment")
    return _advance_campaign(campaign, state=CampaignState.HIDDEN_MATERIAL_REVEALED), SealedQualificationReveal(campaign.campaign_identity, digest, sealed.sealed_root)


def verify_regeneration(
    campaign: QualificationCampaign,
    sealed: SealedRealizationSet,
    regenerated_rows: Iterable[Mapping[str, object]] | None = None,
    *,
    definition: SealedChallengeDefinition | None = None,
    hidden_spec: bytes | None = None,
    authority_harness: Task4AuthorityHarness | None = None,
):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    if campaign.state is not CampaignState.HIDDEN_MATERIAL_REVEALED:
        raise Task4ChallengeCustodyError("regeneration verification requires lawful hidden reveal")
    _validate_bound_realization_set(campaign, sealed)
    # Comparing an arbitrary list with the sealed root proves equality, not
    # regeneration. An injected generator, assertion or receipt is no proof either.
    if regenerated_rows is not None:
        raise Task4ChallengeCustodyError("caller-supplied rows are not regeneration execution evidence")
    if not isinstance(definition, SealedChallengeDefinition) or type(hidden_spec) is not bytes:
        raise Task4ChallengeCustodyError("committed challenge definition and revealed hidden input required")
    _validate_bound_definition(campaign, definition)
    if hashlib.sha256(hidden_spec).hexdigest() != definition.hidden_spec_commitment:
        raise Task4ChallengeCustodyError("regeneration hidden input differs from sealed challenge definition")
    _assert_development_generator_contract(campaign)
    # This is a fresh invocation of the exact pinned synthetic source. The
    # source/policy/RNG checks are process-local mechanics, NOT independent
    # attestation and NEVER valid for FINAL or biological authority.
    computed_rows = _development_fixture_generator(campaign.campaign_identity, hidden_spec, sealed.budget)
    ids, digests, classes = _validated_rows(computed_rows, sealed.budget)
    root = _sha({
        "campaign_identity": campaign.campaign_identity,
        "definition_sha256": sealed.definition_sha256,
        "realization_ids": ids,
        "content_sha256s": digests,
        "challenge_classes": classes,
        "budget": sealed.budget,
    })
    if root != sealed.sealed_root:
        raise Task4ChallengeCustodyError("actual synthetic regeneration differs from exact sealed realization root")
    identities = development_fixture_generator_identities()
    event_digest = _sha({
        "object_role": "DEVELOPMENT_REGENERATION_EXECUTION_V1",
        "campaign_identity": campaign.campaign_identity,
        "definition_sha256": sealed.definition_sha256,
        "sealed_root": sealed.sealed_root,
        "generator_code_sha": identities["challenge_generator_code_sha"],
        "generator_policy_sha": identities["challenge_generator_policy_sha"],
        "rng_policy_sha": identities["rng_policy_sha"],
        "hidden_spec_sha256": hashlib.sha256(hidden_spec).hexdigest(),
        "authority_effect": "NONE",
    })
    advanced = _advance_campaign(campaign, state=CampaignState.REGENERATION_VERIFIED)
    token = advanced._lifecycle_token
    assert token is not None
    _REGENERATION_EXECUTIONS[token] = event_digest
    return advanced, RegenerationVerification(
        campaign.campaign_identity, root, True,
        identities["challenge_generator_code_sha"],
        identities["challenge_generator_policy_sha"],
        identities["rng_policy_sha"],
        event_digest,
    )


def finalize_custody(campaign: QualificationCampaign, sealed: SealedRealizationSet, *, authority_harness: Task4AuthorityHarness | None = None):
    _guard_final(campaign, authority_harness)
    _assert_lifecycle_current(campaign)
    _validate_bound_realization_set(campaign, sealed)
    realized = set(sealed.realization_ids)
    if campaign.namespace != "DEVELOPMENT" or campaign._lifecycle_token not in _REGENERATION_EXECUTIONS:
        raise Task4ChallengeCustodyError("no lawfully executed DEVELOPMENT regeneration event exists")
    if (
        campaign.state is not CampaignState.REGENERATION_VERIFIED
        or set(campaign.exposed_realization_ids) != realized
        or set(dict(campaign.frozen_outputs)) != realized
        or set(dict(campaign.terminal_statuses)) != realized
    ):
        raise Task4ChallengeCustodyError("custody finalization requires complete verified realization accounting")
    receipt = {
        "object_role": "SEALED_CUSTODY_RECEIPT_V1",
        "campaign_identity": campaign.campaign_identity,
        "sealed_root": sealed.sealed_root,
        "exposures_consumed": campaign.exposures_consumed,
        "promotion_authority": "NONE",
    }
    evidence = {
        "object_role": "QUALIFICATION_EVIDENCE_PACKAGE_V1",
        "campaign_identity": campaign.campaign_identity,
        "claim_scope": "POOLED_DONOR_LEVEL_ONLY",
        "realization_ids": list(sealed.realization_ids),
        "frozen_outputs": [list(x) for x in campaign.frozen_outputs],
        "terminal_statuses": [list(x) for x in campaign.terminal_statuses],
        "authority_effect": "NONE",
    }
    return _advance_campaign(campaign, state=CampaignState.CUSTODY_COMPLETE), receipt, evidence