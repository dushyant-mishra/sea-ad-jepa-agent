"""Prospective full-path packing cost model for Teacher/Student V5.

This module estimates execution work only.  It cannot select cells, scientific
weights, update size, evidence dose, or relational scientific weighting.  All
coefficients and the budget must come from a separate hardware calibration.
"""
from __future__ import annotations
from dataclasses import dataclass


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _positive_int(value: object, name: str) -> int:
    out=_nonnegative_int(value,name)
    if out < 1:
        raise ValueError(f"{name} must be a positive integer")
    return out


@dataclass(frozen=True)
class CellExecutionWorkV1:
    teacher_tokens: int
    student_visible_tokens_total: int
    predictor_target_queries_total: int
    relational_triplets: int

    def validate(self) -> None:
        _positive_int(self.teacher_tokens,"teacher_tokens")
        _positive_int(self.student_visible_tokens_total,"student_visible_tokens_total")
        _positive_int(self.predictor_target_queries_total,"predictor_target_queries_total")
        _nonnegative_int(self.relational_triplets,"relational_triplets")


@dataclass(frozen=True)
class LinearPackingCostModelV1:
    teacher_token_cost: int
    student_token_cost: int
    predictor_query_cost: int
    relational_triplet_cost: int

    def validate(self) -> None:
        _positive_int(self.teacher_token_cost,"teacher_token_cost")
        _positive_int(self.student_token_cost,"student_token_cost")
        _positive_int(self.predictor_query_cost,"predictor_query_cost")
        _nonnegative_int(self.relational_triplet_cost,"relational_triplet_cost")

    def cost(self, work: CellExecutionWorkV1) -> int:
        self.validate(); work.validate()
        return (
            work.teacher_tokens*self.teacher_token_cost
            + work.student_visible_tokens_total*self.student_token_cost
            + work.predictor_target_queries_total*self.predictor_query_cost
            + work.relational_triplets*self.relational_triplet_cost
        )


def pack_frozen_slots_by_cost(
    slot_costs: tuple[int,...],
    *,
    max_cost_per_microbatch: int,
) -> tuple[tuple[int,...],...]:
    """Deterministically partition an already frozen ordered cell set by cost.

    This never reorders, drops, duplicates, or reweights scientific slots.
    """
    if not slot_costs:
        raise ValueError("slot_costs cannot be empty")
    budget=_positive_int(max_cost_per_microbatch,"max_cost_per_microbatch")
    costs=tuple(_positive_int(v,f"slot_costs[{i}]") for i,v in enumerate(slot_costs))
    if max(costs) > budget:
        raise ValueError("at least one frozen scientific slot exceeds the calibrated microbatch budget")
    batches=[]; current=[]; used=0
    for slot,cost in enumerate(costs):
        if current and used+cost>budget:
            batches.append(tuple(current)); current=[]; used=0
        current.append(slot); used+=cost
    if current: batches.append(tuple(current))
    flat=tuple(i for batch in batches for i in batch)
    if flat != tuple(range(len(costs))):
        raise RuntimeError("packing altered frozen slot identity/order")
    return tuple(batches)
