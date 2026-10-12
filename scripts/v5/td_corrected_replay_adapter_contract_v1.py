"""Prospective corrected-replay adapter contract.

This module validates only metadata/custody readiness for the frozen TD56/TD57B/
TD57C/TD59 corrected replay. It never authorizes corrected value reads, target
selection, TD60, Stage 4, or training.
"""
from __future__ import annotations


class ReplayAdapterContractError(ValueError):
    pass


SCHEMA = "JEPA_TD_CORRECTED_REPLAY_ADAPTER_CONTRACT_V1"
STAGES = ("TD56", "TD57B", "TD57C", "TD59")
EXPECTED_SOURCE_COUNTS = {"HVS": 1129, "NPH52": 1310, "SEA_AD": 22561}
REQUIRED_METADATA_FIELDS = (
    "global_row",
    "sample_row",
    "source",
    "donor_id",
    "operator_id",
    "cell_id",
    "source_library",
    "detected_count",
)
ALLOWED_METADATA_FIELDS = frozenset(REQUIRED_METADATA_FIELDS)
EXECUTOR_SHA256 = {
    "TD56_HVS": "a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43",
    "TD56_NPH52": "090134f0cc129559286f06d80a31a880c07c9841a7ef3f446b914a78c8cd7162",
    "TD56_SEA_AD": "c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866",
    "TD57B": "1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e",
    "TD57B_FAST": "808fb293a87d0020adc0f332742f3fa9b99c9c8ec5a88e50504a719ad4183a70",
    "TD57C": "530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c",
    "TD59_SUCCESSOR": "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085",
}
TD59_ORIGINAL_EXECUTOR_SHA256 = "3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0"
NO_AUTHORITY = {
    "corrected_replay_authorized": False,
    "target_selected": False,
    "representation_selected": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReplayAdapterContractError(message)


def validate_and_classify(manifest: dict) -> dict:
    _require(isinstance(manifest, dict), "manifest must be a mapping")
    _require(manifest.get("schema") == SCHEMA, "wrong schema")
    _require(manifest.get("sample_label") == "A_NATURAL_MIXTURE", "wrong sample_label")
    _require(manifest.get("row_count") == 25000, "row_count must be 25000")
    _require(
        manifest.get("global_row_start") == 0 and manifest.get("global_row_end") == 24999,
        "global_row range must be exactly 0..24999",
    )
    _require(manifest.get("source_counts") == EXPECTED_SOURCE_COUNTS, "source_counts mismatch")
    _require(manifest.get("replay_address_count") == 9216, "replay_address_count must be 9216")

    fields = manifest.get("metadata_fields")
    _require(isinstance(fields, list), "metadata_fields must be a list")
    _require(
        set(fields) == ALLOWED_METADATA_FIELDS and len(fields) == len(ALLOWED_METADATA_FIELDS),
        "metadata_fields must expose exactly the frozen non-biological fields",
    )

    _require(manifest.get("executor_sha256") == EXECUTOR_SHA256, "executor_sha256 mismatch")
    _require(
        manifest.get("td59_original_executor_sha256") == TD59_ORIGINAL_EXECUTOR_SHA256,
        "TD59 original executor SHA mismatch",
    )
    _require(
        manifest.get("td59_original_executor_bytes_recovered") is False,
        "TD59 original executor bytes must remain unrecovered",
    )

    equivalence = manifest.get("historical_fixture_equivalence")
    _require(
        isinstance(equivalence, dict) and set(equivalence) == set(STAGES),
        "historical_fixture_equivalence must contain exactly TD56/TD57B/TD57C/TD59",
    )
    _require(
        all(v in {"PASS", "PENDING"} for v in equivalence.values()),
        "historical_fixture_equivalence values must be PASS or PENDING",
    )

    for key, expected in NO_AUTHORITY.items():
        _require(manifest.get(key) is expected, "all authority flags must remain false")

    g7_ok = (
        manifest.get("g7_terminal") == "PASS_TD_G7_S174_EXACT_OVERLAP"
        and manifest.get("g7_externally_accepted") is True
    )
    if not g7_ok:
        terminal = "BLOCKED_G7_NOT_EXTERNALLY_ACCEPTED__NO_REPLAY_AUTHORITY"
        ready = False
    elif any(equivalence[stage] != "PASS" for stage in STAGES):
        terminal = "BLOCKED_ADAPTER_EQUIVALENCE_INCOMPLETE__NO_REPLAY_AUTHORITY"
        ready = False
    else:
        terminal = "READY_FOR_SEPARATE_OWNER_CORRECTED_REPLAY_AUTHORIZATION__NO_REPLAY_AUTHORITY"
        ready = True

    return {
        "schema": SCHEMA,
        "adapter_contract_valid": True,
        "replay_package_ready_for_owner_authorization": ready,
        "terminal": terminal,
        "historical_fixture_equivalence": dict(equivalence),
        **dict(NO_AUTHORITY),
    }
