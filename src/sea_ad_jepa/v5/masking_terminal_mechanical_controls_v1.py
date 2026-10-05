"""Mechanical terminal controls for current FULL104 masking qualification.

These controls convert three formerly named-only requirements into executable
fail-closed checks:

* deterministic replay: reconstruct every policy mask twice and require exact
  canonical mask-root equality;
* untreated mask identity: authenticated Level-4 input files must remain
  byte-identical before and after terminal evidence generation, and masking is
  represented only as address exclusion sets;
* no privileged metadata: terminal scoring interfaces and their exact frozen
  source bytes expose only expression addresses plus the donor/source/fold roles
  required for splitting, centering and source-balanced evaluation.

No terminal outcome is used to define these checks.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from . import full104_masking_streaming_executor_v1 as streaming
from . import masking_control_executor_v1 as controls
from . import masking_donor_evidence_v1 as donor_evidence
from . import masking_nonlinear_challenge_executor_v1 as nonlinear
from . import masking_terminal_evidence_assembly_v1 as evidence_assembly
from .masking_qualification_run_contract_v4 import TERMINAL_EXECUTION_INPUT_ROLE_ID

REPLAY_CONTROL_ID = "DETERMINISTIC_REPLAY_CONTROL_V1"
UNTREATED_IDENTITY_CONTROL_ID = "UNTREATED_MASK_IDENTITY_CONTROL_V1"
NO_PRIVILEGED_METADATA_CONTROL_ID = "NO_PRIVILEGED_METADATA_CONTROL_V1"
CONTROL_POLICY_ID = "CURRENT_FULL104_TERMINAL_MECHANICAL_CONTROLS_V1"

_EXPECTED_CALL_INTERFACES = {
    "primary_with_donor_evidence": (
        "stream", "fold_index", "parameters", "evidence_budget", "global_seed"
    ),
    "shuffled_negative_control": (
        "stream", "fold_index", "parameters", "evidence_budget",
        "target_col", "target_id", "global_seed"
    ),
    "planted_matched_shuffle_control": (
        "stream", "fold_index", "parameters", "evidence_budget",
        "target_col", "target_id", "eligible_proxy_cols", "global_seed"
    ),
    "nonlinear_mask_score": (
        "stream", "fold_index", "target_col", "target_id", "mask",
        "authority", "primary_parameters", "y_override_by_selection"
    ),
    "evidence_assembly": ("raw_evidence", "precision"),
}
_ALLOWED_STREAMING_BLOCK_FIELDS = ("selection_rows", "donor_code", "X")


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_mask_sha256(mask: Iterable[int]) -> str:
    values = sorted({int(value) for value in mask})
    if not values:
        raise ValueError("terminal mask cannot be empty")
    if values[0] < 0:
        raise ValueError("terminal mask cannot contain negative addresses")
    return _canonical_digest(
        {"schema": "V5_FULL104_TERMINAL_MASK_SET_V1", "masked_address_cols": values}
    )


def _signature_names(fn: Any) -> tuple[str, ...]:
    return tuple(inspect.signature(fn).parameters)


def _live_source_digest(module: Any) -> str:
    path = Path(module.__file__).resolve()
    if not path.is_file():
        raise ValueError(f"live source path is missing: {path}")
    return _sha256_file(path)


def assert_no_privileged_metadata_interface(
    *,
    run_contract: Any,
    stream: streaming.Full104ManifestStreamV1,
) -> bool:
    """Fail closed unless the runtime is the exact audited expression-only API."""

    run_contract.validate()
    run_contract.assert_terminal_execution_input_role(TERMINAL_EXECUTION_INPUT_ROLE_ID)
    stream.validate_layout()

    expected_sources = {
        "full104_streaming_execution_source_sha256": _live_source_digest(streaming),
        "donor_evidence_source_sha256": _live_source_digest(donor_evidence),
        "control_executor_source_sha256": _live_source_digest(controls),
        "nonlinear_executor_source_sha256": _live_source_digest(nonlinear),
        "terminal_evidence_assembly_source_sha256": _live_source_digest(evidence_assembly),
    }
    for field, observed in expected_sources.items():
        if getattr(run_contract, field, None) != observed:
            raise ValueError(f"{field} does not match the audited live source bytes")

    observed_interfaces = {
        "primary_with_donor_evidence": _signature_names(
            donor_evidence.run_streaming_fold_with_donor_evidence
        ),
        "shuffled_negative_control": _signature_names(
            controls.run_shuffled_negative_control_fold
        ),
        "planted_matched_shuffle_control": _signature_names(
            controls.run_planted_proxy_matched_shuffle_control_fold
        ),
        "nonlinear_mask_score": _signature_names(nonlinear.run_nonlinear_mask_score),
        "evidence_assembly": _signature_names(
            evidence_assembly.assemble_policy_decision_evidence
        ),
    }
    if observed_interfaces != _EXPECTED_CALL_INTERFACES:
        raise ValueError("terminal scoring interface drifted; privileged-metadata audit is invalid")

    block_fields = tuple(streaming.StreamingBlock.__dataclass_fields__)
    if block_fields != _ALLOWED_STREAMING_BLOCK_FIELDS:
        raise ValueError("streaming block interface exposes an unreviewed metadata field")

    forbidden_runtime_attributes = {
        "operator_by_cell",
        "operator_by_donor",
        "pathology_by_cell",
        "pathology_by_donor",
        "diagnosis_by_cell",
        "diagnosis_by_donor",
        "cell_type_by_cell",
        "age_by_donor",
        "sex_by_donor",
    }
    present = forbidden_runtime_attributes.intersection(vars(stream))
    if present:
        raise ValueError(
            "terminal stream exposes privileged metadata attributes: "
            + ",".join(sorted(present))
        )
    return True


def reconstruct_policy_mask_roots(
    *,
    rows: Iterable[Mapping[str, Any]],
    stream: streaming.Full104ManifestStreamV1,
    evidence_budget: Any,
    global_seed: int,
) -> dict[tuple[str, int, int], str]:
    """Reconstruct all primary masks twice and return exact canonical roots.

    Keys are (policy_id, target_index, fold). Missing/duplicate rows fail closed.
    """

    stream.validate_layout()
    evidence_budget.validate()
    co_mask_count = int(
        evidence_budget.mask_count(int(stream.universe_cols.size - 1))
    )
    expected_cardinality = co_mask_count + 1
    output: dict[tuple[str, int, int], str] = {}

    for row in rows:
        method = str(row["method"])
        target_index = int(row["target_index"])
        fold = int(row["fold"])
        target_col = int(row["target_col"])
        target_id = row["target_id"]
        targeted_cols = tuple(map(int, row["targeted_cols"]))
        key = (method, target_index, fold)
        if key in output:
            raise ValueError(f"duplicate terminal policy row: {key!r}")

        kwargs = dict(
            universe_cols=stream.universe_cols,
            target_col=target_col,
            target_id=target_id,
            fold_index=fold,
            global_seed=int(global_seed),
            co_mask_count=co_mask_count,
            method=method,
            targeted_cols=targeted_cols,
            base_mask_fn=streaming._base_uniform_mask,
            removable_order_fn=streaming._removable_order,
        )
        first = donor_evidence._mask_from_row(**kwargs)
        second = donor_evidence._mask_from_row(**kwargs)
        first_root = canonical_mask_sha256(first)
        second_root = canonical_mask_sha256(second)
        if first_root != second_root or first != second:
            raise ValueError("deterministic terminal mask replay failed")
        if target_col not in first:
            raise ValueError("terminal target is not masked")
        if len(first) != expected_cardinality:
            raise ValueError("terminal mask cardinality disagrees with frozen burden")
        if int(row["mask_cardinality"]) != expected_cardinality:
            raise ValueError("primary result row reports a different mask cardinality")
        if int(row["uniform_mask_cardinality"]) != expected_cardinality:
            raise ValueError("uniform base mask cardinality disagrees with frozen burden")
        output[key] = first_root

    if not output:
        raise ValueError("terminal replay control received no primary rows")
    return output


def assert_complete_policy_mask_grid(
    *,
    roots: Mapping[tuple[str, int, int], str],
    policy_ids: Iterable[str],
    target_count: int,
    outer_fold_count: int = 4,
) -> bool:
    expected = {
        (str(policy), target, fold)
        for policy in policy_ids
        for target in range(int(target_count))
        for fold in range(int(outer_fold_count))
    }
    observed = set(roots)
    missing = expected - observed
    extra = observed - expected
    if missing or extra:
        raise ValueError(
            "terminal mask replay grid is incomplete or contains unexpected rows: "
            f"missing={len(missing)} extra={len(extra)}"
        )
    return True


def assert_untreated_input_identity(
    *,
    stream: streaming.Full104ManifestStreamV1,
    before_manifest_sha256: str,
) -> bool:
    """Require authenticated Level-4 bytes to remain unchanged after execution."""

    if before_manifest_sha256 != stream.expected_manifest_sha256:
        raise ValueError("pre-run manifest root does not match authenticated stream")
    after = stream.revalidate_physical_inputs()
    if after != before_manifest_sha256:
        raise ValueError("authenticated Level-4 terminal input changed during execution")
    return True


@dataclass(frozen=True)
class TerminalMechanicalControlReceiptV1:
    run_contract_sha256: str
    terminal_input_manifest_sha256: str
    mask_grid_sha256: str
    replay_exact: bool
    untreated_identity_exact: bool
    no_privileged_metadata: bool
    replay_control_id: str = REPLAY_CONTROL_ID
    untreated_identity_control_id: str = UNTREATED_IDENTITY_CONTROL_ID
    no_privileged_metadata_control_id: str = NO_PRIVILEGED_METADATA_CONTROL_ID
    control_policy_id: str = CONTROL_POLICY_ID
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        for name in (
            "run_contract_sha256",
            "terminal_input_manifest_sha256",
            "mask_grid_sha256",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(f"{name} must be a SHA-256 digest")
            int(value, 16)
        if self.replay_exact is not True:
            raise ValueError("terminal deterministic replay control did not pass")
        if self.untreated_identity_exact is not True:
            raise ValueError("terminal untreated identity control did not pass")
        if self.no_privileged_metadata is not True:
            raise ValueError("terminal no-privileged-metadata control did not pass")
        if self.replay_control_id != REPLAY_CONTROL_ID:
            raise ValueError("replay control id mismatch")
        if self.untreated_identity_control_id != UNTREATED_IDENTITY_CONTROL_ID:
            raise ValueError("untreated identity control id mismatch")
        if self.no_privileged_metadata_control_id != NO_PRIVILEGED_METADATA_CONTROL_ID:
            raise ValueError("no privileged metadata control id mismatch")
        if self.control_policy_id != CONTROL_POLICY_ID:
            raise ValueError("terminal mechanical control policy id mismatch")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("mechanical controls cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("mechanical controls cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _canonical_digest(
            {
                "schema": "V5_FULL104_TERMINAL_MECHANICAL_CONTROL_RECEIPT_V1",
                **self.__dict__,
            }
        )


def mask_grid_digest(roots: Mapping[tuple[str, int, int], str]) -> str:
    normalized = [
        [policy, int(target), int(fold), str(root)]
        for (policy, target, fold), root in sorted(roots.items())
    ]
    return _canonical_digest(
        {"schema": "V5_FULL104_TERMINAL_MASK_GRID_V1", "rows": normalized}
    )
