"""One-rung terminal FULL104 masking-qualification executor.

This is intentionally a single-rung executor. It cannot choose or advance the
burden ladder. A higher rung is lawful only when the caller supplies the exact
contiguous prefix of prior V2 rung receipts together with the bound execution
authority for every prior rung, and every prior execution failed.

The executor consumes authenticated FULL104 Level-4 streaming input. The
calibration cache is not an input and cannot be substituted for the terminal
stream.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import full104_masking_streaming_executor_v1 as streaming
from . import masking_control_executor_v1 as controls
from . import masking_donor_evidence_v1 as donor_evidence
from . import masking_nonlinear_challenge_executor_v1 as nonlinear
from .canonical_address_registry_authority_v1 import (
    CanonicalAddressRegistryAuthorityV1,
)
from .full104_census_receipt_v2 import canonical_sha
from .masking_qualification_decision_v1 import POLICIES
from .masking_qualification_decision_v2 import (
    MaskingRungDecisionReceiptV2,
    evaluate_rung_v2,
)
from .masking_qualification_execution_authority_v4 import (
    MaskingQualificationExecutionAuthorityV4,
)
from .masking_qualification_run_contract_v4 import (
    MaskingQualificationRunContractV4,
    TERMINAL_EXECUTION_INPUT_ROLE_ID,
)
from .masking_burden_ladder_authority_v2 import MaskingBurdenLadderAuthorityV2
from .outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from .precision_authority_v4 import QualificationPrecisionAuthorityV4
from .masking_terminal_evidence_assembly_v1 import (
    TerminalPolicyRawEvidenceV1,
    assemble_policy_decision_evidence,
)
from .masking_terminal_mechanical_controls_v1 import (
    TerminalMechanicalControlReceiptV1,
    assert_complete_policy_mask_grid,
    assert_no_privileged_metadata_interface,
    assert_untreated_input_identity,
    canonical_mask_sha256,
    mask_grid_digest,
    reconstruct_policy_mask_roots,
)
from .target_panel_selector_v2 import TargetPanelSelectionReceiptV2

RAW_RESULT_SCHEMA_ID = "V5_FULL104_TERMINAL_ONE_RUNG_RAW_RESULT_ARTIFACT_V2"
EXECUTOR_POLICY_ID = "EXACTLY_ONE_BURDEN_RUNG_PER_INVOCATION__NO_AUTO_ESCALATION_V1"
TERMINAL_SCIENTIFIC_BLOCKER_ID = "H3_EQUIVALENCE_POWER_AND_G5_MARGIN_BASIS_OPEN_V1"


def _assert_terminal_scientific_design_ready() -> None:
    """Fail closed until H3/G5 have prospective successor authorities."""

    raise ValueError(
        "STOP_H3_G5_TERMINAL_MASKING_UNAUTHORIZED: target-panel sizing is still "
        "capacity-only and the null-equivalence margin lacks a prospective "
        "scientific basis. Terminal burden execution remains closed."
    )


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _live_checkpoint_validation_errors(
    checkpoint_payload: Mapping[str, Any],
) -> list[str]:
    """Validate the checkpoint against its declared live worktree."""

    if not isinstance(checkpoint_payload, Mapping):
        return ["CHECKPOINT_PAYLOAD_NOT_MAPPING"]
    git = checkpoint_payload.get("git")
    if not isinstance(git, Mapping):
        return ["CHECKPOINT_GIT_SNAPSHOT_MISSING"]
    worktree_raw = git.get("worktree_path")
    if not isinstance(worktree_raw, str) or not worktree_raw.strip():
        return ["CHECKPOINT_WORKTREE_PATH_MISSING"]
    worktree = Path(worktree_raw)
    try:
        from scripts.agent.work_checkpoint import resolve_canonical_repo, validate_checkpoint
        repo = resolve_canonical_repo(worktree)
        return list(validate_checkpoint(dict(checkpoint_payload), repo, worktree))
    except Exception as exc:
        return [
            "CHECKPOINT_LIVE_VALIDATION_UNAVAILABLE:"
            f"{type(exc).__name__}:{exc}"
        ]


def _assert_live_machine_checkpoint(
    checkpoint_payload: Mapping[str, Any],
) -> None:
    errors = _live_checkpoint_validation_errors(checkpoint_payload)
    if errors:
        raise ValueError(
            "terminal executor requires a live-valid machine/worktree checkpoint: "
            + "; ".join(errors[:8])
        )


def _receipt_digest(payload: Mapping[str, Any], schema: str) -> str:
    if payload.get("schema") != schema:
        raise ValueError(f"expected receipt schema {schema}")
    declared = payload.get("receipt_sha256")
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    if declared != canonical_sha(semantic):
        raise ValueError(f"{schema} digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is True:
        raise ValueError(f"{schema} was produced after terminal outcome inspection")
    return _sha(str(declared), f"{schema} receipt_sha256")


def _load_registry_ids(
    path: Path,
    authority: CanonicalAddressRegistryAuthorityV1,
) -> tuple[str, ...]:
    authority.validate()
    if not path.is_file():
        raise ValueError("canonical address registry file is missing")
    digest = _sha256_file(path)
    if digest != authority.registry_sha256:
        raise ValueError("canonical address registry file hash mismatch")

    ids: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        if "molecular_address_index" not in fields or "molecular_address_id" not in fields:
            raise ValueError("canonical registry lacks model-facing address fields")
        for expected_index, row in enumerate(reader):
            observed_index = int(row["molecular_address_index"])
            if observed_index != expected_index:
                raise ValueError("canonical address registry ordering invariant failed")
            address_id = str(row["molecular_address_id"])
            if not address_id:
                raise ValueError("canonical address registry contains an empty address id")
            ids.append(address_id)

    unique = len(set(ids)) == len(ids)
    if not authority.verify_artifact(
        sha256=digest,
        row_count=len(ids),
        ordered=True,
        unique=unique,
    ):
        raise ValueError("canonical address registry invariants failed")
    return tuple(ids)


def _validate_split_binding(
    *,
    stream: streaming.Full104ManifestStreamV1,
    outer_split: OuterDonorSplitAuthorityV1,
    split_receipt: Mapping[str, Any],
    run_contract: MaskingQualificationRunContractV4,
) -> tuple[tuple[str, ...], np.ndarray, dict[int, str]]:
    outer_split.validate()
    if outer_split.canonical_digest() != run_contract.outer_split_authority_sha256:
        raise ValueError("outer split authority root mismatch")
    split_root = _receipt_digest(
        split_receipt,
        "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1",
    )
    if split_root != outer_split.fold_assignment_artifact_sha256:
        raise ValueError("outer split authority binds a different split receipt")

    donor_ids = tuple(map(str, split_receipt.get("donor_ids", ())))
    donor_source = np.asarray(split_receipt.get("donor_source_code", ()), dtype=np.int64)
    source_names_raw = tuple(map(str, split_receipt.get("source_names", ())))
    folds = np.asarray(split_receipt.get("fold_by_donor", ()), dtype=np.int64)
    if len(donor_ids) != 104 or len(set(donor_ids)) != 104:
        raise ValueError("terminal split receipt must contain 104 unique donors")
    if donor_source.shape != (104,) or folds.shape != (104,):
        raise ValueError("terminal split donor vectors must contain exactly 104 entries")
    if set(map(int, folds)) != {0, 1, 2, 3}:
        raise ValueError("terminal split must contain exactly four outer folds")
    if donor_source.min() < 0 or donor_source.max() >= len(source_names_raw):
        raise ValueError("terminal split contains an invalid source code")

    by_code = [None] * 104
    for donor_id, code in stream.donor_id_to_code.items():
        if code < 0 or code >= 104 or by_code[code] is not None:
            raise ValueError("terminal stream donor registry is not one-to-one")
        by_code[code] = str(donor_id)
    if tuple(by_code) != donor_ids:
        raise ValueError("terminal stream donor ids differ from frozen split receipt")
    if not np.array_equal(np.asarray(stream.fold_by_donor, dtype=np.int64), folds):
        raise ValueError("terminal stream folds differ from frozen split receipt")
    expected_source_labels = np.asarray(
        [source_names_raw[int(code)] for code in donor_source],
        dtype=object,
    )
    if not np.array_equal(np.asarray(stream.source_by_donor, dtype=object), expected_source_labels):
        raise ValueError("terminal stream donor sources differ from frozen split receipt")
    source_names = {index: name for index, name in enumerate(source_names_raw)}
    return donor_ids, donor_source, source_names


def _validate_target_binding(
    *,
    stream: streaming.Full104ManifestStreamV1,
    target_panel: Any,
    selection_receipt: TargetPanelSelectionReceiptV2,
    target_eligibility_receipt: Mapping[str, Any],
    registry_authority: CanonicalAddressRegistryAuthorityV1,
    registry_path: Path,
    run_contract: Any,
) -> tuple[tuple[str, ...], np.ndarray]:
    target_panel.validate()
    selection_receipt.validate()
    registry_authority.validate()

    if target_panel.canonical_digest() != run_contract.target_panel_authority_sha256:
        raise ValueError("target panel authority root mismatch")
    if registry_authority.canonical_digest() != target_panel.canonical_registry_authority_sha256:
        raise ValueError("target panel binds a different canonical address registry")
    if selection_receipt.canonical_digest() != target_panel.target_selection_receipt_sha256:
        raise ValueError("target selection receipt root mismatch")

    eligibility_root = _receipt_digest(
        target_eligibility_receipt,
        "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",
    )
    if eligibility_root != target_panel.target_eligibility_receipt_sha256:
        raise ValueError("target panel binds a different target-eligibility receipt")

    strict_core = np.asarray(
        target_eligibility_receipt.get("strict_core_cols", ()),
        dtype=np.int64,
    )
    eligible_targets = np.asarray(
        target_eligibility_receipt.get("eligible_target_cols_all_folds", ()),
        dtype=np.int64,
    )
    if strict_core.ndim != 1 or strict_core.size != 17186:
        raise ValueError("terminal strict common core must contain exactly 17,186 addresses")
    if np.unique(strict_core).size != strict_core.size:
        raise ValueError("terminal strict common core contains duplicate addresses")
    if not np.array_equal(np.asarray(stream.universe_cols, dtype=np.int64), strict_core):
        raise ValueError("terminal stream universe differs from frozen strict common core")

    selected = np.asarray(selection_receipt.selected_target_cols, dtype=np.int64)
    if selected.size != target_panel.target_count:
        raise ValueError("selected target count disagrees with target panel authority")
    if not set(map(int, selected)).issubset(set(map(int, eligible_targets))):
        raise ValueError("selected target panel contains an ineligible address")
    if not np.array_equal(np.asarray(stream.target_cols, dtype=np.int64), selected):
        raise ValueError("terminal stream targets differ from frozen selection receipt")

    registry_ids = _load_registry_ids(Path(registry_path), registry_authority)
    if selected.min() < 0 or selected.max() >= len(registry_ids):
        raise ValueError("selected target column is outside canonical address registry")
    expected_ids = tuple(registry_ids[int(col)] for col in selected)
    observed_ids = tuple(map(str, stream.target_ids))
    if observed_ids != expected_ids:
        raise ValueError("terminal stream target ids differ from canonical registry identity")
    return expected_ids, eligible_targets


def _validate_requested_rung(
    *,
    burden_ladder: MaskingBurdenLadderAuthorityV2,
    numerator: int,
    denominator: int,
    prior_rung_receipts: Sequence[MaskingRungDecisionReceiptV2],
    prior_rung_execution_authorities: Sequence[MaskingQualificationExecutionAuthorityV4],
    prior_rung_raw_result_artifacts: Sequence["TerminalOneRungRawResultArtifactV1"],
    expected_run_contract_sha256: str,
    expected_terminal_input_manifest_sha256: str,
) -> tuple[Fraction, tuple[str, ...], tuple[str, ...]]:
    burden_ladder.validate()
    requested = Fraction(int(numerator), int(denominator))
    verdicts: dict[Fraction, bool] = {}
    prior_roots: list[str] = []
    prior_execution_roots: list[str] = []
    expected_rungs = burden_ladder.ordered_rungs()
    expected_run_contract_sha256 = _sha(
        expected_run_contract_sha256, "expected_run_contract_sha256"
    )
    if not (
        len(prior_rung_receipts)
        == len(prior_rung_execution_authorities)
        == len(prior_rung_raw_result_artifacts)
    ):
        raise ValueError(
            "every prior rung must supply receipt, execution authority, and raw-result artifact"
        )

    expected_terminal_input_manifest_sha256 = _sha(
        expected_terminal_input_manifest_sha256,
        "expected_terminal_input_manifest_sha256",
    )

    for index, (receipt, execution, raw_artifact) in enumerate(
        zip(
            prior_rung_receipts,
            prior_rung_execution_authorities,
            prior_rung_raw_result_artifacts,
        )
    ):
        if not isinstance(receipt, MaskingRungDecisionReceiptV2):
            raise ValueError("prior terminal rung evidence must be a V2 rung decision receipt")
        receipt.validate()
        if not isinstance(execution, MaskingQualificationExecutionAuthorityV4):
            raise ValueError("prior rung authorization must be ExecutionAuthorityV4")
        execution.validate()
        if execution.run_contract_authority_sha256 != expected_run_contract_sha256:
            raise ValueError("prior rung execution binds a different run contract")
        if not isinstance(raw_artifact, TerminalOneRungRawResultArtifactV1):
            raise ValueError("prior rung raw evidence must be TerminalOneRungRawResultArtifactV1")
        raw_artifact.validate()
        execution.bind_raw_result_artifact(raw_artifact)
        execution.bind_rung_decision_receipt(receipt)
        if raw_artifact.terminal_input_manifest_sha256 != expected_terminal_input_manifest_sha256:
            raise ValueError("prior rung raw result binds a different authenticated FULL104 manifest")
        if tuple(raw_artifact.prior_rung_decision_receipt_sha256) != tuple(prior_roots):
            raise ValueError("prior rung raw result does not bind the exact preceding decision chain")
        if tuple(raw_artifact.prior_rung_execution_authority_sha256) != tuple(prior_execution_roots):
            raise ValueError("prior rung raw result does not bind the exact preceding execution chain")
        if execution.execution_status != "EXECUTED_FAIL":
            raise ValueError("higher burden requires a proven failed prior execution")
        rung = Fraction(receipt.burden_numerator, receipt.burden_denominator)
        if index >= len(expected_rungs) or rung != expected_rungs[index]:
            raise ValueError("prior rung receipts are not an exact ascending ladder prefix")
        if receipt.qualified is not False:
            raise ValueError("higher burden cannot open after a lower burden qualified")
        verdicts[rung] = False
        prior_roots.append(receipt.canonical_digest())
        prior_execution_roots.append(execution.canonical_digest())

    lawful_next = burden_ladder.next_rung(verdicts)
    if lawful_next is None or requested != lawful_next:
        raise ValueError(
            f"requested burden {requested} is not the only lawful next rung {lawful_next}"
        )
    return requested, tuple(prior_roots), tuple(prior_execution_roots)


def _fill_donor_values(
    matrix: np.ndarray,
    seen: np.ndarray,
    *,
    target_index: int,
    donor_pairs: Sequence[Sequence[Any]],
    label: str,
) -> None:
    for raw_donor, raw_value in donor_pairs:
        donor = int(raw_donor)
        if donor < 0 or donor >= matrix.shape[1]:
            raise ValueError(f"{label} contains an out-of-range donor")
        if seen[target_index, donor]:
            raise ValueError(f"duplicate {label} evidence for target/donor")
        value = float(raw_value)
        if not np.isfinite(value):
            raise ValueError(f"{label} evidence must be finite")
        matrix[target_index, donor] = value
        seen[target_index, donor] = True


def _require_complete(matrix: np.ndarray, seen: np.ndarray, label: str) -> None:
    if matrix.shape != seen.shape or not np.all(seen) or np.any(~np.isfinite(matrix)):
        missing = int(np.size(seen) - np.count_nonzero(seen))
        raise ValueError(f"{label} evidence is incomplete: missing={missing}")


@dataclass(frozen=True)
class TerminalOneRungRawResultArtifactV1:
    run_contract_sha256: str
    burden_numerator: int
    burden_denominator: int
    prior_rung_decision_receipt_sha256: tuple[str, ...]
    prior_rung_execution_authority_sha256: tuple[str, ...]
    terminal_input_manifest_sha256: str
    split_receipt_sha256: str
    target_eligibility_receipt_sha256: str
    target_selection_receipt_sha256: str
    mechanical_control_receipt_sha256: str
    raw_policy_evidence_sha256: Mapping[str, str]
    executor_policy_id: str = EXECUTOR_POLICY_ID
    protected_outcomes_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        _sha(self.run_contract_sha256, "run_contract_sha256")
        _sha(self.terminal_input_manifest_sha256, "terminal_input_manifest_sha256")
        _sha(self.split_receipt_sha256, "split_receipt_sha256")
        _sha(self.target_eligibility_receipt_sha256, "target_eligibility_receipt_sha256")
        _sha(self.target_selection_receipt_sha256, "target_selection_receipt_sha256")
        _sha(self.mechanical_control_receipt_sha256, "mechanical_control_receipt_sha256")
        if len(self.prior_rung_decision_receipt_sha256) != len(
            self.prior_rung_execution_authority_sha256
        ):
            raise ValueError("prior rung receipt/execution roots must be one-to-one")
        for root in self.prior_rung_decision_receipt_sha256:
            _sha(root, "prior_rung_decision_receipt_sha256")
        for root in self.prior_rung_execution_authority_sha256:
            _sha(root, "prior_rung_execution_authority_sha256")
        if set(self.raw_policy_evidence_sha256) != set(POLICIES):
            raise ValueError("raw result artifact must bind every policy arm exactly once")
        for policy, root in self.raw_policy_evidence_sha256.items():
            if policy not in POLICIES:
                raise ValueError("raw result artifact contains an unapproved policy")
            _sha(root, f"raw_policy_evidence_sha256[{policy}]")
        burden = Fraction(self.burden_numerator, self.burden_denominator)
        if not 0 < burden < 1:
            raise ValueError("raw result burden must lie strictly between zero and one")
        if self.executor_policy_id != EXECUTOR_POLICY_ID:
            raise ValueError("one-rung executor policy id mismatch")
        if self.protected_outcomes_authorized is not False:
            raise ValueError("raw terminal result cannot authorize protected outcomes")
        if self.training_authorized is not False:
            raise ValueError("raw terminal result cannot authorize training")

    def payload(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": RAW_RESULT_SCHEMA_ID,
            "run_contract_sha256": self.run_contract_sha256,
            "burden_numerator": self.burden_numerator,
            "burden_denominator": self.burden_denominator,
            "prior_rung_decision_receipt_sha256": list(
                self.prior_rung_decision_receipt_sha256
            ),
            "prior_rung_execution_authority_sha256": list(
                self.prior_rung_execution_authority_sha256
            ),
            "terminal_input_manifest_sha256": self.terminal_input_manifest_sha256,
            "split_receipt_sha256": self.split_receipt_sha256,
            "target_eligibility_receipt_sha256": self.target_eligibility_receipt_sha256,
            "target_selection_receipt_sha256": self.target_selection_receipt_sha256,
            "mechanical_control_receipt_sha256": self.mechanical_control_receipt_sha256,
            "raw_policy_evidence_sha256": dict(sorted(self.raw_policy_evidence_sha256.items())),
            "executor_policy_id": self.executor_policy_id,
            "protected_outcomes_authorized": False,
            "training_authorized": False,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.payload())

    def canonical_digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def write(self, path: Path) -> str:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.canonical_bytes()
        path.write_bytes(data)
        digest = _sha256_file(path)
        if digest != self.canonical_digest():
            raise ValueError("written raw-result artifact did not reproduce canonical digest")
        return digest

    def bind_raw_evidence(
        self,
        raw_by_policy: Mapping[str, TerminalPolicyRawEvidenceV1],
        controls_receipt: TerminalMechanicalControlReceiptV1,
    ) -> None:
        self.validate()
        controls_receipt.validate()
        if controls_receipt.canonical_digest() != self.mechanical_control_receipt_sha256:
            raise ValueError("raw result artifact binds a different mechanical-control receipt")
        if set(raw_by_policy) != set(POLICIES):
            raise ValueError("raw evidence map must contain every policy arm")
        for policy in POLICIES:
            raw = raw_by_policy[policy]
            raw.validate()
            if raw.policy_id != policy:
                raise ValueError("raw evidence policy key mismatch")
            if raw.mechanical_control_receipt_sha256 != self.mechanical_control_receipt_sha256:
                raise ValueError("raw policy evidence binds a different mechanical-control receipt")
            if raw.canonical_digest() != self.raw_policy_evidence_sha256[policy]:
                raise ValueError("raw policy evidence root mismatch")


@dataclass(frozen=True)
class TerminalOneRungExecutionResultV1:
    raw_evidence_by_policy: Mapping[str, TerminalPolicyRawEvidenceV1]
    mechanical_control_receipt: TerminalMechanicalControlReceiptV1
    raw_result_artifact: TerminalOneRungRawResultArtifactV1
    rung_decision_receipt: MaskingRungDecisionReceiptV2
    execution_authority: MaskingQualificationExecutionAuthorityV4


def execute_one_terminal_rung(
    *,
    run_contract: Any,
    machine_checkpoint_payload: Mapping[str, Any],
    qualification_design: Any,
    parameters: Any,
    evidence_budget_template: Any,
    burden_ladder: Any,
    burden_numerator: int,
    burden_denominator: int,
    prior_rung_receipts: Sequence[MaskingRungDecisionReceiptV2],
    prior_rung_execution_authorities: Sequence[MaskingQualificationExecutionAuthorityV4],
    prior_rung_raw_result_artifacts: Sequence[TerminalOneRungRawResultArtifactV1],
    rng_replay: Any,
    outer_split: Any,
    split_receipt: Mapping[str, Any],
    target_panel: Any,
    target_panel_sizing_plan: Any,
    target_panel_sizing_receipt: Any,
    target_selection_receipt: TargetPanelSelectionReceiptV2,
    target_eligibility_receipt: Mapping[str, Any],
    canonical_registry_authority: CanonicalAddressRegistryAuthorityV1,
    canonical_registry_path: Path,
    precision: QualificationPrecisionAuthorityV4,
    nonlinear_authority: Any,
    nonlinear_sampling_calibration_plan: Any,
    nonlinear_sampling_calibration_receipt: Any,
    stream: streaming.Full104ManifestStreamV1,
) -> TerminalOneRungExecutionResultV1:
    """Execute exactly one currently-lawful terminal burden rung."""

    _assert_terminal_scientific_design_ready()

    if not isinstance(stream, streaming.Full104ManifestStreamV1):
        raise ValueError("terminal executor requires Full104ManifestStreamV1")
    if not isinstance(run_contract, MaskingQualificationRunContractV4):
        raise ValueError("run_contract must be MaskingQualificationRunContractV4")
    if not isinstance(burden_ladder, MaskingBurdenLadderAuthorityV2):
        raise ValueError("burden_ladder must be MaskingBurdenLadderAuthorityV2")
    if not isinstance(outer_split, OuterDonorSplitAuthorityV1):
        raise ValueError("outer_split must be OuterDonorSplitAuthorityV1")
    if not isinstance(precision, QualificationPrecisionAuthorityV4):
        raise ValueError("precision must be QualificationPrecisionAuthorityV4")
    run_contract.validate()
    run_contract.assert_terminal_execution_input_role(TERMINAL_EXECUTION_INPUT_ROLE_ID)

    executor_root = _sha256_file(Path(__file__).resolve())
    if getattr(run_contract, "terminal_one_rung_executor_source_sha256", None) != executor_root:
        raise ValueError("run contract does not bind the live one-rung terminal executor")

    run_contract.bind_machine_checkpoint_semantic(machine_checkpoint_payload)
    _assert_live_machine_checkpoint(machine_checkpoint_payload)
    run_contract.bind_parameters(parameters)
    run_contract.bind_evidence_budget_template(evidence_budget_template)
    run_contract.bind_burden_ladder(burden_ladder)
    run_contract.bind_rng_replay(rng_replay)
    run_contract.bind_design(qualification_design)
    run_contract.bind_target_panel(
        target_panel,
        target_panel_sizing_plan,
        target_panel_sizing_receipt,
    )
    run_contract.bind_precision(precision)
    run_contract.bind_nonlinear(
        nonlinear_authority,
        nonlinear_sampling_calibration_plan,
        nonlinear_sampling_calibration_receipt,
    )

    qualification_design.bind_live_authorities(
        target_evidence_budget_template=evidence_budget_template,
        burden_ladder=burden_ladder,
        precision=precision,
        outer_split=outer_split,
        target_panel=target_panel,
        rng_replay=rng_replay,
    )
    target_panel.bind(
        target_panel_sizing_plan,
        target_panel_sizing_receipt,
        target_selection_receipt,
    )
    precision.bind_target_panel(target_panel, target_panel_sizing_receipt)
    nonlinear_authority.bind_sampling_calibration(
        nonlinear_sampling_calibration_plan,
        nonlinear_sampling_calibration_receipt,
    )

    if stream.expected_manifest_sha256 != run_contract.full104_block_manifest_sha256:
        raise ValueError("terminal stream binds a different FULL104 block manifest")
    before_manifest = stream.revalidate_physical_inputs()

    requested, prior_roots, prior_execution_roots = _validate_requested_rung(
        burden_ladder=burden_ladder,
        numerator=burden_numerator,
        denominator=burden_denominator,
        prior_rung_receipts=prior_rung_receipts,
        prior_rung_execution_authorities=prior_rung_execution_authorities,
        prior_rung_raw_result_artifacts=prior_rung_raw_result_artifacts,
        expected_run_contract_sha256=run_contract.canonical_digest(),
        expected_terminal_input_manifest_sha256=before_manifest,
    )
    budget = evidence_budget_template.with_fraction(
        requested.numerator,
        requested.denominator,
    )
    budget.validate()

    no_privileged = assert_no_privileged_metadata_interface(
        run_contract=run_contract,
        stream=stream,
    )

    donor_ids, donor_source, source_names = _validate_split_binding(
        stream=stream,
        outer_split=outer_split,
        split_receipt=split_receipt,
        run_contract=run_contract,
    )
    target_ids, eligible_proxy_cols = _validate_target_binding(
        stream=stream,
        target_panel=target_panel,
        selection_receipt=target_selection_receipt,
        target_eligibility_receipt=target_eligibility_receipt,
        registry_authority=canonical_registry_authority,
        registry_path=Path(canonical_registry_path),
        run_contract=run_contract,
    )

    target_count = len(target_ids)
    if target_count != precision.required_target_count:
        raise ValueError("terminal target count must exactly equal calibrated precision target count")
    if len(donor_ids) != 104:
        raise ValueError("terminal execution requires exactly 104 donors")
    if set(map(int, stream.fold_by_donor)) != {0, 1, 2, 3}:
        raise ValueError("terminal execution requires exactly four outer folds")

    shape = (target_count, 104)
    actual = {policy: np.full(shape, np.nan, dtype=np.float64) for policy in POLICIES}
    actual_seen = {policy: np.zeros(shape, dtype=bool) for policy in POLICIES}
    uniform = np.full(shape, np.nan, dtype=np.float64)
    uniform_seen = np.zeros(shape, dtype=bool)
    shuffled = {policy: np.full(shape, np.nan, dtype=np.float64) for policy in POLICIES}
    shuffled_seen = {policy: np.zeros(shape, dtype=bool) for policy in POLICIES}
    negative = np.full(shape, np.nan, dtype=np.float64)
    negative_seen = np.zeros(shape, dtype=bool)
    planted_detect = np.full(shape, np.nan, dtype=np.float64)
    planted_detect_seen = np.zeros(shape, dtype=bool)
    planted_after = np.full(shape, np.nan, dtype=np.float64)
    planted_after_seen = np.zeros(shape, dtype=bool)
    nl_actual = {policy: np.full(shape, np.nan, dtype=np.float64) for policy in POLICIES}
    nl_actual_seen = {policy: np.zeros(shape, dtype=bool) for policy in POLICIES}
    nl_shuffled = {policy: np.full(shape, np.nan, dtype=np.float64) for policy in POLICIES}
    nl_shuffled_seen = {policy: np.zeros(shape, dtype=bool) for policy in POLICIES}
    effective = {
        policy: np.full((target_count, 4), np.nan, dtype=np.float64)
        for policy in POLICIES
    }

    all_primary_rows: list[dict[str, Any]] = []
    global_seed = int(rng_replay.global_seed)

    for fold in range(4):
        rows = donor_evidence.run_streaming_fold_with_donor_evidence(
            stream=stream,
            fold_index=fold,
            parameters=parameters,
            evidence_budget=budget,
            global_seed=global_seed,
        )
        all_primary_rows.extend(rows)
        by_target: dict[int, dict[str, Mapping[str, Any]]] = {}
        for row in rows:
            target_index = int(row["target_index"])
            method = str(row["method"])
            if target_index < 0 or target_index >= target_count:
                raise ValueError("primary terminal row has out-of-range target index")
            if method not in POLICIES:
                raise ValueError("primary terminal row has unapproved policy")
            target_rows = by_target.setdefault(target_index, {})
            if method in target_rows:
                raise ValueError("duplicate primary policy row for target/fold")
            target_rows[method] = row
            _fill_donor_values(
                actual[method],
                actual_seen[method],
                target_index=target_index,
                donor_pairs=row["heldout_donor_scores"],
                label=f"actual[{method}]",
            )
            effective[method][target_index, fold] = float(row["effective_targeted_n"])

        if set(by_target) != set(range(target_count)):
            raise ValueError("primary terminal fold is missing one or more targets")
        for target_index in range(target_count):
            target_rows = by_target[target_index]
            if set(target_rows) != set(POLICIES):
                raise ValueError("primary terminal target is missing one or more policy arms")
            uniform_row = target_rows["UNIFORM_RANDOM"]
            _fill_donor_values(
                uniform,
                uniform_seen,
                target_index=target_index,
                donor_pairs=uniform_row["heldout_donor_scores"],
                label="uniform",
            )

            target_col = int(stream.target_cols[target_index])
            target_id = str(stream.target_ids[target_index])
            raw_y, donor_by_row = controls.materialize_stream_column(
                stream,
                column=target_col,
            )
            shuffled_y = controls.deterministic_within_donor_shuffle(
                raw_y,
                donor_by_row,
                target_id=target_id,
                global_seed=global_seed,
            )
            shuffled_replay = controls.deterministic_within_donor_shuffle(
                raw_y,
                donor_by_row,
                target_id=target_id,
                global_seed=global_seed,
            )
            if not np.array_equal(shuffled_y, shuffled_replay):
                raise ValueError("within-donor target shuffle did not replay exactly")

            heldout = np.flatnonzero(stream.fold_by_donor == fold).astype(np.int64)
            train = np.flatnonzero(stream.fold_by_donor != fold).astype(np.int64)
            co_mask_count = int(budget.mask_count(int(stream.universe_cols.size - 1)))

            for policy in POLICIES:
                row = target_rows[policy]
                mask = donor_evidence._mask_from_row(
                    universe_cols=stream.universe_cols,
                    target_col=target_col,
                    target_id=target_id,
                    fold_index=fold,
                    global_seed=global_seed,
                    co_mask_count=co_mask_count,
                    method=policy,
                    targeted_cols=tuple(map(int, row["targeted_cols"])),
                    base_mask_fn=streaming._base_uniform_mask,
                    removable_order_fn=streaming._removable_order,
                )
                _, shuffled_donor = controls._score_mask(
                    stream,
                    train_donors=train,
                    heldout_donors=heldout,
                    y_by_selection=shuffled_y,
                    target_col=target_col,
                    mask=mask,
                    parameters=parameters,
                )
                _fill_donor_values(
                    shuffled[policy],
                    shuffled_seen[policy],
                    target_index=target_index,
                    donor_pairs=tuple(sorted(shuffled_donor.items())),
                    label=f"shuffled[{policy}]",
                )

                real_nl = nonlinear.run_nonlinear_mask_score(
                    stream=stream,
                    fold_index=fold,
                    target_col=target_col,
                    target_id=target_id,
                    mask=mask,
                    authority=nonlinear_authority,
                    primary_parameters=parameters,
                )
                shuffled_nl = nonlinear.run_nonlinear_mask_score(
                    stream=stream,
                    fold_index=fold,
                    target_col=target_col,
                    target_id=target_id,
                    mask=mask,
                    authority=nonlinear_authority,
                    primary_parameters=parameters,
                    y_override_by_selection=shuffled_y,
                )
                _fill_donor_values(
                    nl_actual[policy],
                    nl_actual_seen[policy],
                    target_index=target_index,
                    donor_pairs=real_nl["donor_scores"],
                    label=f"nonlinear_actual[{policy}]",
                )
                _fill_donor_values(
                    nl_shuffled[policy],
                    nl_shuffled_seen[policy],
                    target_index=target_index,
                    donor_pairs=shuffled_nl["donor_scores"],
                    label=f"nonlinear_shuffled[{policy}]",
                )

            neg = controls.run_shuffled_negative_control_fold(
                stream=stream,
                fold_index=fold,
                parameters=parameters,
                evidence_budget=budget,
                target_col=target_col,
                target_id=target_id,
                global_seed=global_seed,
            )
            _fill_donor_values(
                negative,
                negative_seen,
                target_index=target_index,
                donor_pairs=neg["donor_delta"],
                label="negative_control",
            )

            plant = controls.run_planted_proxy_matched_shuffle_control_fold(
                stream=stream,
                fold_index=fold,
                parameters=parameters,
                evidence_budget=budget,
                target_col=target_col,
                target_id=target_id,
                eligible_proxy_cols=eligible_proxy_cols,
                global_seed=global_seed,
            )
            if plant.get("same_mask_shuffled_proxy") is not True:
                raise ValueError("planted control did not use a same-mask shuffled proxy")
            _fill_donor_values(
                planted_detect,
                planted_detect_seen,
                target_index=target_index,
                donor_pairs=plant["detect_donor_excess"],
                label="planted_detect",
            )
            _fill_donor_values(
                planted_after,
                planted_after_seen,
                target_index=target_index,
                donor_pairs=plant["after_mask_donor_excess"],
                label="planted_after_mask",
            )

    roots = reconstruct_policy_mask_roots(
        rows=all_primary_rows,
        stream=stream,
        evidence_budget=budget,
        global_seed=global_seed,
    )
    assert_complete_policy_mask_grid(
        roots=roots,
        policy_ids=POLICIES,
        target_count=target_count,
        outer_fold_count=4,
    )

    _require_complete(uniform, uniform_seen, "uniform")
    _require_complete(negative, negative_seen, "negative control")
    _require_complete(planted_detect, planted_detect_seen, "planted detect")
    _require_complete(planted_after, planted_after_seen, "planted after-mask")
    for policy in POLICIES:
        _require_complete(actual[policy], actual_seen[policy], f"actual[{policy}]")
        _require_complete(shuffled[policy], shuffled_seen[policy], f"shuffled[{policy}]")
        _require_complete(
            nl_actual[policy],
            nl_actual_seen[policy],
            f"nonlinear_actual[{policy}]",
        )
        _require_complete(
            nl_shuffled[policy],
            nl_shuffled_seen[policy],
            f"nonlinear_shuffled[{policy}]",
        )
        if np.any(~np.isfinite(effective[policy])):
            raise ValueError(f"effective targeting grid is incomplete for {policy}")

    untreated_identity = assert_untreated_input_identity(
        stream=stream,
        before_manifest_sha256=before_manifest,
    )
    mechanical_receipt = TerminalMechanicalControlReceiptV1(
        run_contract_sha256=run_contract.canonical_digest(),
        terminal_input_manifest_sha256=before_manifest,
        mask_grid_sha256=mask_grid_digest(roots),
        replay_exact=True,
        untreated_identity_exact=untreated_identity,
        no_privileged_metadata=no_privileged,
    )
    mechanical_receipt.validate()
    mechanical_root = mechanical_receipt.canonical_digest()

    raw_by_policy: dict[str, TerminalPolicyRawEvidenceV1] = {}
    decision_evidence = []
    for policy in POLICIES:
        mask_grid = tuple(
            tuple(roots[(policy, target, fold)] for fold in range(4))
            for target in range(target_count)
        )
        raw = TerminalPolicyRawEvidenceV1(
            policy_id=policy,
            burden_numerator=requested.numerator,
            burden_denominator=requested.denominator,
            target_ids=target_ids,
            donor_ids=donor_ids,
            donor_source_code=donor_source,
            donor_outer_fold=np.asarray(stream.fold_by_donor, dtype=np.int64),
            source_names=source_names,
            policy_mask_sha256_by_target_fold=mask_grid,
            mechanical_control_receipt_sha256=mechanical_root,
            actual_policy_scores=actual[policy],
            actual_uniform_scores=uniform,
            shuffled_same_mask_scores=shuffled[policy],
            negative_control_delta=negative,
            planted_detect_excess=planted_detect,
            planted_after_mask_excess=planted_after,
            nonlinear_actual_scores=nl_actual[policy],
            nonlinear_shuffled_same_mask_scores=nl_shuffled[policy],
            effective_targeted_n_by_target_fold=effective[policy],
            replay_exact=mechanical_receipt.replay_exact,
            untreated_identity_exact=mechanical_receipt.untreated_identity_exact,
            no_privileged_metadata=mechanical_receipt.no_privileged_metadata,
        )
        raw_by_policy[policy] = raw
        decision_evidence.append(
            assemble_policy_decision_evidence(
                raw_evidence=raw,
                precision=precision,
            )
        )

    rung_receipt = evaluate_rung_v2(decision_evidence, precision=precision)
    rung_receipt.validate()
    if (
        rung_receipt.burden_numerator,
        rung_receipt.burden_denominator,
    ) != (requested.numerator, requested.denominator):
        raise ValueError("rung decision receipt changed the requested burden")

    split_root = _receipt_digest(
        split_receipt,
        "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1",
    )
    eligibility_root = _receipt_digest(
        target_eligibility_receipt,
        "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",
    )
    artifact = TerminalOneRungRawResultArtifactV1(
        run_contract_sha256=run_contract.canonical_digest(),
        burden_numerator=requested.numerator,
        burden_denominator=requested.denominator,
        prior_rung_decision_receipt_sha256=prior_roots,
        prior_rung_execution_authority_sha256=prior_execution_roots,
        terminal_input_manifest_sha256=before_manifest,
        split_receipt_sha256=split_root,
        target_eligibility_receipt_sha256=eligibility_root,
        target_selection_receipt_sha256=target_selection_receipt.canonical_digest(),
        mechanical_control_receipt_sha256=mechanical_root,
        raw_policy_evidence_sha256={
            policy: raw_by_policy[policy].canonical_digest()
            for policy in POLICIES
        },
    )
    artifact.bind_raw_evidence(raw_by_policy, mechanical_receipt)

    execution = MaskingQualificationExecutionAuthorityV4(
        authority_id=(
            "JEPA_V5_FULL104_MASKING_EXECUTION_AUTHORITY_V4__"
            f"{requested.numerator}_OF_{requested.denominator}"
        ),
        run_contract_authority_sha256=run_contract.canonical_digest(),
        raw_result_artifact_sha256=artifact.canonical_digest(),
        rung_decision_receipt_sha256=rung_receipt.canonical_digest(),
        selected_policy_id=rung_receipt.selected_policy_id,
        selected_burden_numerator=requested.numerator,
        selected_burden_denominator=requested.denominator,
        execution_status=(
            "EXECUTED_PASS" if rung_receipt.qualified else "EXECUTED_FAIL"
        ),
    )
    execution.bind_raw_result_artifact(artifact)
    execution.bind_rung_decision_receipt(rung_receipt)

    return TerminalOneRungExecutionResultV1(
        raw_evidence_by_policy=raw_by_policy,
        mechanical_control_receipt=mechanical_receipt,
        raw_result_artifact=artifact,
        rung_decision_receipt=rung_receipt,
        execution_authority=execution,
    )
