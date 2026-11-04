"""Read-only V43 research primitive for STRUCTURED same-cell teacher targets.

This is NOT model training, learned feature fusion, q-validity certification,
a regulator prior, a validated rarity detector or a current-V5 authority.
Only RNA components from the same exact original cell can enter this v1 target.
Separate-nucleus ATAC may be used only in a future explicit population-level
protocol, never joined by shared donor identity to make a fictitious single cell.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Optional, Sequence

HEADS = ("CORE", "FINE", "RARE")


class TargetProvenanceError(ValueError):
    """A proposed target misrepresents evidence or merges incompatible cells."""


@dataclass(frozen=True)
class TeacherComponent:
    head: str
    canonical_cell_key: str
    query_address_id: int
    source_sha256: str
    values: tuple[float, ...]
    assay: str = "RNA"
    correspondence: str = "SAME_ORIGINAL_CELL"
    observed_support: bool = True
    biological_eligibility: bool = True

    def __post_init__(self) -> None:
        if self.head not in HEADS:
            raise TargetProvenanceError("unregistered teacher head")
        if not self.canonical_cell_key:
            raise TargetProvenanceError("missing exact original same-cell identity")
        if type(self.query_address_id) is not int or not 0 <= self.query_address_id < 41238:
            raise TargetProvenanceError("query address outside frozen canonical registry")
        if len(self.source_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.source_sha256):
            raise TargetProvenanceError("missing exact source SHA256")
        if self.assay != "RNA" or self.correspondence != "SAME_ORIGINAL_CELL":
            raise TargetProvenanceError("cross-cell / unpaired assay cannot make a same-cell target")
        if type(self.observed_support) is not bool or type(self.biological_eligibility) is not bool:
            raise TargetProvenanceError("support and eligibility must be explicit booleans")
        if self.observed_support and self.biological_eligibility:
            if not self.values or not all(math.isfinite(v) for v in self.values):
                raise TargetProvenanceError("observed component has empty/nonfinite state")
        elif self.values:
            raise TargetProvenanceError("unsupported or ineligible component cannot emit a zero or fake vector")


@dataclass(frozen=True)
class StructuredTeacherTarget:
    canonical_cell_key: str
    query_address_id: int
    shared: tuple[float, ...]
    fine: Optional[tuple[float, ...]]
    rare: Optional[tuple[float, ...]]
    support: Mapping[str, bool]
    source_roots: Mapping[str, str]
    copied_specialist_diagnostic: Mapping[str, Optional[bool]]
    # Diagnostics do not reweight, suppress or select a teacher.
    consensus_gating_used: bool = False


def assemble_same_cell_target(
    components: Sequence[TeacherComponent],
    *,
    routing_rule: str = "FROZEN_SUPPORT_AND_ELIGIBILITY_ONLY",
) -> StructuredTeacherTarget:
    """Retain per-head target; abstain when absent; NEVER average via consensus.

    The caller is responsible for independent biological eligibility certification;
    a caller-supplied True here is NOT evidence that a rare state is real.
    """
    if routing_rule != "FROZEN_SUPPORT_AND_ELIGIBILITY_ONLY":
        raise TargetProvenanceError("data-dependent / expert-consensus gate prohibited")
    by_head: dict[str, TeacherComponent] = {}
    for component in components:
        if not isinstance(component, TeacherComponent):
            raise TargetProvenanceError("untyped teacher component")
        if component.head in by_head:
            raise TargetProvenanceError("duplicate head / silent expert cloning")
        by_head[component.head] = component
    if "CORE" not in by_head or not by_head["CORE"].observed_support or not by_head["CORE"].biological_eligibility:
        raise TargetProvenanceError("missing supported CORE teacher target")
    core = by_head["CORE"]
    if any((x.canonical_cell_key, x.query_address_id) != (core.canonical_cell_key, core.query_address_id) for x in by_head.values()):
        raise TargetProvenanceError("teacher components refer to different cells or different queries")
    support = {head: bool(head in by_head and by_head[head].observed_support and by_head[head].biological_eligibility) for head in HEADS}
    state = {head: (by_head[head].values if support[head] else None) for head in HEADS}
    roots = {head: by_head[head].source_sha256 for head in HEADS if head in by_head}
    copied = {
        head: (state[head] == state["CORE"] if state[head] is not None else None)
        for head in ("FINE", "RARE")
    }
    return StructuredTeacherTarget(
        canonical_cell_key=core.canonical_cell_key,
        query_address_id=core.query_address_id,
        shared=core.values,
        fine=state["FINE"],
        rare=state["RARE"],
        support=support,
        source_roots=roots,
        copied_specialist_diagnostic=copied,
        consensus_gating_used=False,
    )


def verify_independent_rare_donor_support(
    donor_keys: Sequence[str],
    *,
    prospectively_frozen_min_independent_donors: Optional[int],
) -> bool:
    """Only test caller-frozen donor criterion; this helper sets NO minimum."""
    if prospectively_frozen_min_independent_donors is None:
        raise TargetProvenanceError("rare donor recurrence threshold not scientifically frozen")
    k = prospectively_frozen_min_independent_donors
    if type(k) is not int or k < 2:
        raise TargetProvenanceError("rare donor threshold invalid; not independently replicated")
    if any(not isinstance(d, str) or not d for d in donor_keys):
        raise TargetProvenanceError("invalid donor identifiers")
    return len(set(donor_keys)) >= k
