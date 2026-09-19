"""Fresh-runtime envelope for non-terminal FULL104 shakedown.

This guard is deliberately operational, not scientific authority.  Its purpose
is to prevent accidental reuse of Stage81/T1/discovery/smaller-run outputs as
current FULL104 runtime inputs.  A runtime root must begin absent or empty and
is then sealed to the current physical FULL104 roots.

The envelope cannot authorize target-panel calibration, terminal masking,
protected outcomes, or training.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

FULL104_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
CANONICAL_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
SENTINEL_NAME = "FULL104_RUNTIME_ENVELOPE_V1.json"
RUNTIME_ROLE_ID = "FRESH_CURRENT_FULL104_NONTERMINAL_SHAKEDOWN_RUNTIME_V1"
SPILLOVER_POLICY_ID = (
    "NO_HISTORICAL_OR_SMALLER_RUN_RUNTIME_INPUT_WITHOUT_EXPLICIT_CURRENT_FULL104_REAUTHORIZATION_V1"
)

FORBIDDEN_PATH_FRAGMENTS = (
    "stage81",
    "t1_checkpoint",
    "post_u0_t1",
    "discovery",
    "ridge8",
    "qualification_800",
    "qualification_2000",
    "qualification_6000",
    "outer5200",
    "corrected_real_train",
    "placeholder",
    "foundation_calibration_bundle",
    "foundation_discovery_expression",
)

# Exact historical/supporting roots already present in the project provenance
# chain.  These values are blocked only as runtime files; the historical source
# files may remain in the repository as supporting provenance.
FORBIDDEN_RUNTIME_SHA256 = frozenset(
    {
        "a649a4bd220851423679a3ee47fdc096691056eea0cfb09984de64caceb3ad88",
        "eb32280d90cf2bdc7ab2fed86e1a5af41c4e0293d89d61cc6f2641b9a1fb3511",
        "7a33785c774485363ea0f57d90acdee2a1d64c81772da1a35f1bef24c5b3a5dc",
        "6b972a20e49876b5f77b35ab836b5ce9d416cc1e671aa80dcd5d8461e5a6f038",
        "73c5125cb79555401836159d861f1775bce7e23879ab0dbada8350813d6ae89a",
        "b43676f7d95bd8599ad7be47b2b121a6f02b4314d4507f537d4e59b7c68d01c4",
        "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444",
        "63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7",
        "ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c",
        "0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c",
    }
)


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def canonical_sha(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class Full104RuntimeEnvelopeV1:
    scientific_anchor_sha256: str
    full104_block_manifest_sha256: str
    canonical_registry_sha256: str
    observation_state_sha256: str
    runtime_role_id: str = RUNTIME_ROLE_ID
    spillover_policy_id: str = SPILLOVER_POLICY_ID
    target_panel_ladder_authorized: bool = False
    terminal_masking_authorized: bool = False
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        _sha(self.scientific_anchor_sha256, "scientific_anchor_sha256")
        if _sha(self.full104_block_manifest_sha256, "full104_block_manifest_sha256") != FULL104_BLOCK_MANIFEST_SHA256:
            raise ValueError("runtime envelope binds a different FULL104 block manifest")
        if _sha(self.canonical_registry_sha256, "canonical_registry_sha256") != CANONICAL_REGISTRY_SHA256:
            raise ValueError("runtime envelope binds a different canonical registry")
        if _sha(self.observation_state_sha256, "observation_state_sha256") != OBSERVATION_STATE_SHA256:
            raise ValueError("runtime envelope binds a different observation state")
        if self.runtime_role_id != RUNTIME_ROLE_ID:
            raise ValueError("runtime_role_id mismatch")
        if self.spillover_policy_id != SPILLOVER_POLICY_ID:
            raise ValueError("spillover_policy_id mismatch")
        for name in (
            "target_panel_ladder_authorized",
            "terminal_masking_authorized",
            "protected_outcomes_authorized",
            "training_authorized",
        ):
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain False in non-terminal shakedown")

    def canonical_digest(self) -> str:
        self.validate()
        return canonical_sha(
            {"schema": "V5_FULL104_RUNTIME_ENVELOPE_V1", **asdict(self)}
        )


def assert_runtime_path_names_clean(root: Path) -> None:
    root = Path(root)
    if not root.exists():
        return
    for path in root.rglob("*"):
        rel = str(path.relative_to(root)).replace("\\", "/").lower()
        if path.is_symlink():
            raise ValueError(f"runtime envelope forbids symlinks: {rel}")
        for fragment in FORBIDDEN_PATH_FRAGMENTS:
            if fragment in rel:
                raise ValueError(
                    f"historical/smaller-run spillover token {fragment!r} in runtime path {rel!r}"
                )


def assert_no_known_historical_runtime_hashes(
    root: Path,
    *,
    max_hash_bytes: int = 1 << 30,
) -> None:
    """Reject known historical artifacts if copied into the runtime root.

    Files larger than max_hash_bytes are not blindly hashed here because the
    physical FULL104 substrate is outside the fresh runtime root.  Path-token
    and current-root guards remain active for all files.
    """

    root = Path(root)
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file() or path.name == SENTINEL_NAME:
            continue
        if path.stat().st_size > max_hash_bytes:
            continue
        observed = sha256_file(path)
        if observed in FORBIDDEN_RUNTIME_SHA256:
            raise ValueError(
                f"known historical/supporting artifact copied into FULL104 runtime: {path}"
            )


def prepare_fresh_runtime(
    root: Path,
    *,
    scientific_anchor_sha256: str,
    full104_block_manifest_sha256: str,
    canonical_registry_sha256: str,
    observation_state_sha256: str,
) -> Full104RuntimeEnvelopeV1:
    root = Path(root)
    if root.exists():
        existing = list(root.iterdir())
        if existing:
            raise ValueError(
                "FULL104 shakedown runtime must start absent or empty; "
                "refuse to reuse a directory containing prior artifacts"
            )
    else:
        root.mkdir(parents=True, exist_ok=False)

    envelope = Full104RuntimeEnvelopeV1(
        scientific_anchor_sha256=scientific_anchor_sha256,
        full104_block_manifest_sha256=full104_block_manifest_sha256,
        canonical_registry_sha256=canonical_registry_sha256,
        observation_state_sha256=observation_state_sha256,
    )
    envelope.validate()
    payload = {
        "schema": "V5_FULL104_RUNTIME_ENVELOPE_V1",
        **asdict(envelope),
        "runtime_envelope_sha256": envelope.canonical_digest(),
    }
    (root / SENTINEL_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return envelope


def validate_runtime_envelope(
    root: Path,
    *,
    expected_scientific_anchor_sha256: str,
) -> Full104RuntimeEnvelopeV1:
    root = Path(root)
    payload_path = root / SENTINEL_NAME
    if not payload_path.is_file():
        raise ValueError("FULL104 runtime envelope sentinel is missing")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_RUNTIME_ENVELOPE_V1":
        raise ValueError("FULL104 runtime envelope schema mismatch")
    names = set(Full104RuntimeEnvelopeV1.__dataclass_fields__)
    if not names.issubset(payload):
        raise ValueError("FULL104 runtime envelope is missing required fields")
    envelope = Full104RuntimeEnvelopeV1(
        **{name: payload[name] for name in names}
    )
    envelope.validate()
    if envelope.scientific_anchor_sha256 != expected_scientific_anchor_sha256:
        raise ValueError("FULL104 runtime envelope scientific anchor mismatch")
    if payload.get("runtime_envelope_sha256") != envelope.canonical_digest():
        raise ValueError("FULL104 runtime envelope digest mismatch")
    assert_runtime_path_names_clean(root)
    assert_no_known_historical_runtime_hashes(root)
    return envelope
