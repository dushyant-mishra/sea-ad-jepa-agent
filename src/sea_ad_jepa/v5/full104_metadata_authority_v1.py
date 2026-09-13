"""Single frozen metadata authority for FULL104-derived V5 production artifacts.

Production callers may repeat the expected digest for explicitness, but they may
not choose it.  Synthetic/unit fixtures can provide a private override through
call sites that expose an underscored test-only parameter.
"""
from __future__ import annotations

EXPECTED_METADATA_SQLITE_SHA256 = (
    "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
)


def validate_requested_metadata_authority(
    requested_sha256: str,
    *,
    _expected_metadata_sha256_for_test: str | None = None,
) -> str:
    active = (
        EXPECTED_METADATA_SQLITE_SHA256
        if _expected_metadata_sha256_for_test is None
        else _expected_metadata_sha256_for_test
    )
    for value, name in ((active, "active metadata authority"), (requested_sha256, "requested metadata authority")):
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"{name} must be a SHA-256 hex digest")
        try:
            int(value, 16)
        except ValueError as exc:
            raise ValueError(f"{name} must be hexadecimal") from exc
    active = active.lower()
    if requested_sha256.lower() != active:
        raise ValueError("metadata authority SHA mismatch")
    return active
