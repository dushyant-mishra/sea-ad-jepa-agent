"""Preterminal FULL104 masking RNG authority V3.

V2 derived the global seed from the target-panel authority. That makes changing
the eventual panel size re-roll every base mask and PREFIX3 inner grouping, and
prevents an outcome-blind burden audit from binding the exact mask geometry
before H3/G5 have selected a terminal panel.

V3 removes that dependency. The seed is derived only from stable current FULL104
roots that already exist before panel selection:
- physical FULL104 substrate;
- canonical molecular-address registry;
- frozen donor split receipt;
- current masking-parameter authority;
- current burden-ladder authority.

Target identity and outer fold remain in the per-mask keyed seed downstream.
Thus selecting a later target subset only SUBSETS an already-defined family of
masks; it does not re-roll them.

This authority does not authorize terminal masking or training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

SEED_NAMESPACE_ID = "V5_COMMON_RANDOM_BASE_MASK_PREPANEL_ROOT_DERIVED_V3"
METHOD_EXCLUSION_POLICY_ID = "MASK_POLICY_ID_ABSENT_FROM_BASE_MASK_SEED_V1"
REPLAY_POLICY_ID = "DETERMINISTIC_EXACT_MASK_REPLAY_V1"

FULL104_SUBSTRATE_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CANONICAL_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


@dataclass(frozen=True)
class MaskingRngReplayAuthorityV3:
    authority_id: str
    full104_substrate_sha256: str
    canonical_registry_sha256: str
    outer_split_receipt_sha256: str
    qualification_parameters_authority_sha256: str
    burden_ladder_authority_sha256: str
    seed_namespace_id: str = SEED_NAMESPACE_ID
    method_exclusion_policy_id: str = METHOD_EXCLUSION_POLICY_ID
    replay_policy_id: str = REPLAY_POLICY_ID
    terminal_outcomes_inspected_before_freeze: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        if _sha(self.full104_substrate_sha256, "full104_substrate_sha256") != FULL104_SUBSTRATE_SHA256:
            raise ValueError("RNG authority binds a different FULL104 substrate")
        if _sha(self.canonical_registry_sha256, "canonical_registry_sha256") != CANONICAL_REGISTRY_SHA256:
            raise ValueError("RNG authority binds a different canonical registry")
        roots = (
            self.full104_substrate_sha256,
            self.canonical_registry_sha256,
            _sha(self.outer_split_receipt_sha256, "outer_split_receipt_sha256"),
            _sha(
                self.qualification_parameters_authority_sha256,
                "qualification_parameters_authority_sha256",
            ),
            _sha(self.burden_ladder_authority_sha256, "burden_ladder_authority_sha256"),
        )
        if len(set(roots)) != len(roots):
            raise ValueError("RNG authority roots must be role-distinct")
        if self.seed_namespace_id != SEED_NAMESPACE_ID:
            raise ValueError("seed_namespace_id mismatch")
        if self.method_exclusion_policy_id != METHOD_EXCLUSION_POLICY_ID:
            raise ValueError("method_exclusion_policy_id mismatch")
        if self.replay_policy_id != REPLAY_POLICY_ID:
            raise ValueError("replay_policy_id mismatch")
        if self.terminal_outcomes_inspected_before_freeze is not False:
            raise ValueError("RNG authority must freeze before terminal outcomes")
        if self.training_authorized is not False:
            raise ValueError("RNG authority cannot authorize training")

    @property
    def global_seed(self) -> int:
        self.validate()
        payload = {
            "schema": "V5_MASKING_ROOT_DERIVED_GLOBAL_SEED_V3",
            "seed_namespace_id": self.seed_namespace_id,
            "full104_substrate_sha256": self.full104_substrate_sha256,
            "canonical_registry_sha256": self.canonical_registry_sha256,
            "outer_split_receipt_sha256": self.outer_split_receipt_sha256,
            "qualification_parameters_authority_sha256":
                self.qualification_parameters_authority_sha256,
            "burden_ladder_authority_sha256": self.burden_ladder_authority_sha256,
        }
        return int.from_bytes(
            hashlib.sha256(_canonical(payload)).digest()[:8],
            "big",
            signed=False,
        )

    def derive_seed(self, *, target_id: str, outer_fold: int, cell_key: str) -> int:
        self.validate()
        if not isinstance(target_id, str) or not target_id:
            raise ValueError("target_id must be nonempty")
        if isinstance(outer_fold, bool) or not isinstance(outer_fold, int) or outer_fold < 0:
            raise ValueError("outer_fold must be a nonnegative integer")
        if not isinstance(cell_key, str) or not cell_key:
            raise ValueError("cell_key must be nonempty")
        payload = {
            "schema": "V5_COMMON_RANDOM_BASE_MASK_SEED_V3",
            "authority_sha256": self.canonical_digest(),
            "global_seed": self.global_seed,
            "target_id": target_id,
            "outer_fold": outer_fold,
            "cell_key": cell_key,
        }
        return int.from_bytes(
            hashlib.sha256(_canonical(payload)).digest()[:8],
            "big",
            signed=False,
        )

    def canonical_digest(self) -> str:
        self.validate()
        return _digest(
            {
                "schema": "V5_MASKING_RNG_REPLAY_AUTHORITY_V3",
                **asdict(self),
                "global_seed": self.global_seed,
            }
        )
