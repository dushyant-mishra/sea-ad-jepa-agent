"""Audit-B N1 runtime RNG composition authority V1.

RNG-V3 freezes the root-derived global seed before target-panel selection. Its
typed derive_seed(target_id, fold, cell_key) helper, however, is not called by
the B4-frozen mask planner. The planner uses that same global seed with the
explicit downstream namespace preimages frozen below.

No Audit-B mask has been executed. This authority closes the runtime ambiguity
prospectively without rerolling the B4-frozen mask family.

Runtime authority is the composition of:
1. exact RNG-V3 authority/root global seed;
2. exact B4-bound plan-generator and streaming-planner sources;
3. exact legacy downstream namespace preimages pinned below;
4. target identity = integer molecular address column.

The standalone RNG-V3 derive_seed helper is explicitly NOT the N1 runtime seed
function.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

RNG_V3_AUTHORITY_SHA256 = (
    "775aba506982a9a8dbecccb454d8d3d68709e524bb7f67e9397bbf819b72c2fb"
)
RNG_V3_GLOBAL_SEED = 1267387626254385975
B4_CONTRACT_SHA256 = (
    "c68231e53ee08990949688013261c957fc205f9599bbc446780a12ba4d276927"
)
MASK_PLAN_GENERATOR_SHA256 = (
    "fdc0cec140132b71fd0c01af5ec97c323bac091055191754dfcf81111ee6441e"
)
STREAMING_PLANNER_SOURCE_SHA256 = (
    "143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d"
)

TARGET_ID_RULE_ID = "INTEGER_MOLECULAR_ADDRESS_COLUMN_V1"
ROOT_SEED_ROLE_ID = "RNG_V3_GLOBAL_SEED_ROOT_ONLY__DOWNSTREAM_RUNTIME_BRIDGED_V1"
TYPED_DERIVE_SEED_RUNTIME_ROLE_ID = "NOT_USED_FOR_N1_RUNTIME_MASK_GEOMETRY_V1"

BASE_MASK_NAMESPACE = "V5_COMMON_RANDOM_BASE_MASK"
BASE_MASK_PREIMAGE_ID = (
    "PIPE_JOIN_NAMESPACE_GLOBAL_SEED_OUTER_FOLD_INTEGER_TARGET_ADDRESS_UNIVERSE_SIZE_V1"
)
PREFIX3_NAMESPACE = "V5_PREFIX3_INNER"
PREFIX3_PREIMAGE_ID = "PIPE_JOIN_NAMESPACE_GLOBAL_SEED_SOURCE_NAME_V1"
REMOVAL_NAMESPACE = "V5_MASK_REMOVE"
REMOVAL_PREIMAGE_ID = (
    "PIPE_JOIN_NAMESPACE_GLOBAL_SEED_OUTER_FOLD_INTEGER_TARGET_ADDRESS_CANDIDATE_V1"
)
SEED_DIGEST_ID = "SHA256_FIRST8_BIG_ENDIAN_UNSIGNED_V1"
REMOVAL_ORDER_DIGEST_ID = "SHA256_FULL_DIGEST_LEXICOGRAPHIC_ASCENDING_V1"
METHOD_IN_BASE_MASK_SEED = False
TARGET_PANEL_IN_ANY_RUNTIME_SEED = False


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def pipe_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def base_mask_seed(*, outer_fold: int, target_address: int, universe_size: int) -> int:
    if outer_fold not in (0, 1, 2, 3):
        raise ValueError("outer_fold must be 0..3")
    if target_address < 0 or universe_size < 2:
        raise ValueError("invalid target/universe geometry")
    return pipe_seed(
        BASE_MASK_NAMESPACE,
        RNG_V3_GLOBAL_SEED,
        outer_fold,
        int(target_address),
        int(universe_size),
    )


def prefix3_inner_seed(*, source_name: str) -> int:
    if not isinstance(source_name, str) or not source_name:
        raise ValueError("source_name must be nonempty")
    return pipe_seed(PREFIX3_NAMESPACE, RNG_V3_GLOBAL_SEED, source_name)


def removal_order_digest(
    *,
    outer_fold: int,
    target_address: int,
    candidate_address: int,
) -> bytes:
    if outer_fold not in (0, 1, 2, 3):
        raise ValueError("outer_fold must be 0..3")
    if min(target_address, candidate_address) < 0:
        raise ValueError("addresses must be nonnegative")
    return hashlib.sha256(
        (
            f"{REMOVAL_NAMESPACE}|{RNG_V3_GLOBAL_SEED}|{outer_fold}|"
            f"{int(target_address)}|{int(candidate_address)}"
        ).encode("utf-8")
    ).digest()


@dataclass(frozen=True)
class AuditBN1RuntimeRngBridgeV1:
    authority_id: str
    rng_v3_authority_sha256: str = RNG_V3_AUTHORITY_SHA256
    rng_v3_global_seed: int = RNG_V3_GLOBAL_SEED
    b4_contract_sha256: str = B4_CONTRACT_SHA256
    mask_plan_generator_sha256: str = MASK_PLAN_GENERATOR_SHA256
    streaming_planner_source_sha256: str = STREAMING_PLANNER_SOURCE_SHA256

    target_id_rule_id: str = TARGET_ID_RULE_ID
    root_seed_role_id: str = ROOT_SEED_ROLE_ID
    typed_derive_seed_runtime_role_id: str = TYPED_DERIVE_SEED_RUNTIME_ROLE_ID

    base_mask_namespace: str = BASE_MASK_NAMESPACE
    base_mask_preimage_id: str = BASE_MASK_PREIMAGE_ID
    prefix3_namespace: str = PREFIX3_NAMESPACE
    prefix3_preimage_id: str = PREFIX3_PREIMAGE_ID
    removal_namespace: str = REMOVAL_NAMESPACE
    removal_preimage_id: str = REMOVAL_PREIMAGE_ID
    seed_digest_id: str = SEED_DIGEST_ID
    removal_order_digest_id: str = REMOVAL_ORDER_DIGEST_ID

    method_in_base_mask_seed: bool = METHOD_IN_BASE_MASK_SEED
    target_panel_in_any_runtime_seed: bool = TARGET_PANEL_IN_ANY_RUNTIME_SEED

    masks_executed_before_freeze: bool = False
    burden_outcomes_inspected_before_freeze: bool = False
    terminal_masking_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        expected_hashes = {
            "rng_v3_authority_sha256": RNG_V3_AUTHORITY_SHA256,
            "b4_contract_sha256": B4_CONTRACT_SHA256,
            "mask_plan_generator_sha256": MASK_PLAN_GENERATOR_SHA256,
            "streaming_planner_source_sha256": STREAMING_PLANNER_SOURCE_SHA256,
        }
        for name, expected in expected_hashes.items():
            if _sha(getattr(self, name), name) != expected:
                raise ValueError(f"{name} drifted")
        if self.rng_v3_global_seed != RNG_V3_GLOBAL_SEED:
            raise ValueError("rng_v3_global_seed drifted")
        expected = {
            "target_id_rule_id": TARGET_ID_RULE_ID,
            "root_seed_role_id": ROOT_SEED_ROLE_ID,
            "typed_derive_seed_runtime_role_id": TYPED_DERIVE_SEED_RUNTIME_ROLE_ID,
            "base_mask_namespace": BASE_MASK_NAMESPACE,
            "base_mask_preimage_id": BASE_MASK_PREIMAGE_ID,
            "prefix3_namespace": PREFIX3_NAMESPACE,
            "prefix3_preimage_id": PREFIX3_PREIMAGE_ID,
            "removal_namespace": REMOVAL_NAMESPACE,
            "removal_preimage_id": REMOVAL_PREIMAGE_ID,
            "seed_digest_id": SEED_DIGEST_ID,
            "removal_order_digest_id": REMOVAL_ORDER_DIGEST_ID,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"{name} drifted from B4-frozen runtime composition")
        if self.method_in_base_mask_seed is not False:
            raise ValueError("method must remain absent from common base-mask seed")
        if self.target_panel_in_any_runtime_seed is not False:
            raise ValueError("target panel must not reroll N1 runtime seeds")
        for name in (
            "masks_executed_before_freeze",
            "burden_outcomes_inspected_before_freeze",
            "terminal_masking_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    def canonical_digest(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_AUDIT_B_N1_RUNTIME_RNG_BRIDGE_V1",
                    **asdict(self),
                }
            )
        ).hexdigest()
