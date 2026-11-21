#!/usr/bin/env python3
"""Prospective DEV2048 V2 *address metadata*, no world, RNA, model or training.

Preserves PR328's FOUR 15-gene rare programmes and perturbation's overlap
with rare programme zero. A distinctly versioned role/panel policy permits
shared observed non-query genes across *different* q-specific panels while
retaining eight distinct OTHER genes for *each* query. No outcome is accessed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.v79.dev2048_v2_pregeneration_feasibility_v1 import (
    N_GENES, N_VIEWS, VIEW_SIZE, GENES_PER_RARE_PROGRAM,
    N_QUERIES_V2_PROPOSED, PANEL_SIZE, support_only_roles,
    verify_original_sources,
)

SCHEMA = "DEV2048_V2_PROSPECTIVE_SHARED_NONQUERY_PANELS_SOURCE_ONLY_V1"
SEED = 20261121
SALT = "DEV2048_V2_ROLE_ALLOCATION_FROZEN_BEFORE_WORLD_V1"
SEED_COMMITMENT_SHA256 = hashlib.sha256(
    f"{SEED}|{SALT}".encode("utf-8")).hexdigest()
QUERY_LABELS = (
    "RARE_0", "PERTURB_0", "PERTURB_0",
    "RARE_1", "RARE_2", "RARE_3", "NULL_0", "NULL_1",
)


def _ranked(addresses: list[int], label: str) -> list[int]:
    """Seeded ordering independent of expression, activity or model scores."""
    return sorted(addresses, key=lambda a: (
        hashlib.sha256(f"{SEED}|{SALT}|{label}|{a}".encode()).digest(), a
    ))


def frozen_metadata_plan() -> dict[str, object]:
    physical = support_only_roles()
    views = physical["views"]
    queries = physical["queries"]
    if len(views) != N_VIEWS or len(queries) != N_QUERIES_V2_PROPOSED:
        raise ValueError("original prospective support roles changed")
    if len(set(queries)) != 8:
        raise ValueError("query addresses not distinct")
    common = [
        i for i in range(N_GENES)
        if all((i + o) % 37 != 0 for o in (0, 5, 11))
    ]
    # Views are RESERVED for programme assignment, not already taken by
    # biological members. Track q first; the remaining source-common tail
    # excludes all physically reserved view addresses.
    reserved_views = set(sum(views, []))
    used = set(queries)
    tail = [i for i in common if i not in reserved_views and i not in used]
    program: list[list[int]] = []
    for p in range(4):
        members = []
        for vi, view in enumerate(views):
            in_view = _ranked(view, f"rare{p}-view{vi}")
            # Do not choose an address already planted for another program.
            selected = [a for a in in_view if a not in used][:3]
            if len(selected) != 3:
                raise ValueError("could not place rare members in view")
            members.extend(selected)
            used.update(selected)  # views are preassigned, this is safe
        program.append(members)

    # Source mechanism is NOT changed: PERTURB uses RARE_0's members.
    # Three queries in the SAME rare-0 programme are needed for 1 rare +
    # 2 perturb contrasts. Only queries 0-5 have planted programme truth.
    q_program = [0, 0, 0, 1, 2, 3, None, None]
    for qi, p in enumerate(q_program):
        if p is not None:
            program[p].append(queries[qi])

    # Each programme retains 15 genes total. Rare0: 9 in views + 3 q
    # + 3 *shared* panel members = 15. Other programmes: 9 views + 1 q
    # + 3 panel members + 2 reserve = 15. Tail programme genes are
    # allocated from real structurally common addresses, not readouts.
    def take(n: int, label: str) -> list[int]:
        candidates = [a for a in _ranked(tail, label) if a not in used]
        if len(candidates) < n:
            raise ValueError("not enough unused physically common addresses")
        found = candidates[:n]
        used.update(found)
        return found

    panel_program = [take(3, f"rare{p}-panel") for p in range(4)]
    for p in range(4):
        program[p].extend(panel_program[p])
    for p in (1, 2, 3):
        program[p].extend(take(2, f"rare{p}-reserve"))

    panels = []
    for qi, label in enumerate(QUERY_LABELS):
        p = q_program[qi]
        if p is None:
            # A null query has NO planted programme membership, but its
            # measured other8 deliberately includes programme genes.
            planted = panel_program[1 if qi == 6 else 2]
        else:
            planted = panel_program[p]
        filler = take(PANEL_SIZE - len(planted), f"other8-filler-q{qi}")
        panels.append([*planted, *filler])

    result = {
        "schema": SCHEMA,
        "status": "PROSPECTIVE_ADDRESS_LAYOUT_FEASIBLE__WORLD_NOT_GENERATED",
        "seed": SEED,
        "salt_commitment_sha256": SEED_COMMITMENT_SHA256,
        "parent_v1_unchanged": True,
        "mechanism": "PR328_4_RARE_15GENE_PROGRAMS__PERTURB_OVERLAPS_RARE0",
        "view_address_ids": views,
        "query_address_ids": queries,
        "query_labels": list(QUERY_LABELS),
        "query_program": q_program,
        "query_other8_panels": panels,
        "rare_program_address_ids": program,
        "rare_program_panel_gene_ids": panel_program,
        "shared_cross_query_panel_policy": "ALLOWED_ONLY_WITHIN_V2__Q_NEVER_PANEL",
        "same_query_panel_distinct_8": True,
        "student_must_exclude_all_8_q": True,
        "student_must_exclude_q_locus_atac": True,
        "physical_common_address_count": len(common),
        "rare_donor_active_source_split": "NOT_MEASURED__CONTROLLER_ONLY",
        "real_data_similarity": "NOT_EVALUATED",
        "C1_C6_scored": False,
        "generator_authorized": False,
        "world_generated": False,
        "model_trained": False,
    }
    validate_plan(result)
    return result


def _require_role(ok: bool, reason: str) -> None:
    """Never use assert for a future boundary: Python -O removes assertions."""
    if not ok:
        raise ValueError("DEV2048_V2_ROLE_REFUSAL:" + reason)


def validate_plan(plan: dict[str, object]) -> None:
    """Fail-closed, source-only checks of the proposed *unapproved* V2 layout."""
    q = plan["query_address_ids"]
    panels = plan["query_other8_panels"]
    views = plan["view_address_ids"]
    genes = plan["rare_program_address_ids"]
    labels = plan["query_labels"]
    q_program = plan["query_program"]
    planted = plan["rare_program_panel_gene_ids"]

    source_roles = support_only_roles()
    _require_role(plan["schema"] == SCHEMA, "SCHEMA")
    _require_role(plan["seed"] == SEED and
                  plan["salt_commitment_sha256"] == SEED_COMMITMENT_SHA256,
                  "FROZEN_SEED")
    _require_role(plan["status"] ==
                  "PROSPECTIVE_ADDRESS_LAYOUT_FEASIBLE__WORLD_NOT_GENERATED",
                  "STATUS_NOT_SOURCE_ONLY")
    _require_role(plan["parent_v1_unchanged"] is True, "V1_PRESERVATION")
    _require_role(plan["mechanism"] ==
                  "PR328_4_RARE_15GENE_PROGRAMS__PERTURB_OVERLAPS_RARE0",
                  "PLANTED_MECHANISM")
    _require_role(labels == list(QUERY_LABELS), "QUERY_LABELS")
    _require_role(q_program == [0, 0, 0, 1, 2, 3, None, None],
                  "QUERY_PROGRAM")
    _require_role(views == source_roles["views"], "VIEWS_NOT_FROZEN")
    _require_role(q == source_roles["queries"], "QUERIES_NOT_FROZEN")
    _require_role(len(views) == N_VIEWS and
                  all(len(v) == VIEW_SIZE for v in views), "VIEW_SIZE")
    view_union = sum(views, [])
    panel_union = sum(panels, [])
    _require_role(len(set(view_union)) == N_VIEWS * VIEW_SIZE,
                  "VIEWS_NOT_DISJOINT")
    _require_role(len(q) == len(set(q)) == len(panels) == len(labels) == 8,
                  "QUERY_COUNT")
    _require_role(not set(q).intersection(view_union), "QUERY_IN_VIEW")
    _require_role(all(len(panel) == len(set(panel)) == PANEL_SIZE
                      for panel in panels), "PANEL_SIZE_OR_DUPLICATE")
    _require_role(not set(q).intersection(panel_union), "Q_LEAKS_IN_PANEL")
    _require_role(not set(view_union).intersection(panel_union), "PANEL_IN_VIEW")
    _require_role(all(type(a) is int and 0 <= a < N_GENES and
                      all((a + offset) % 37 != 0 for offset in (0, 5, 11))
                      for seq in [*views, *panels, q] for a in seq),
                  "UNMEASURED_OR_INVALID_ADDRESS")

    _require_role(len(genes) == 4, "PROGRAM_COUNT")
    _require_role(all(len(g) == len(set(g)) == GENES_PER_RARE_PROGRAM
                      for g in genes), "PROGRAM_SIZE")
    _require_role(len(set(sum(genes, []))) ==
                  4 * GENES_PER_RARE_PROGRAM, "PROGRAM_MEMBERS_OVERLAP")
    _require_role(all(len(set(g).intersection(v)) == 3
                      for g in genes for v in views), "PROGRAM_VIEW_QUOTAS")
    _require_role([len(set(g).intersection(q)) for g in genes] ==
                  [3, 1, 1, 1], "PROGRAM_QUERY_QUOTAS")
    _require_role(len(planted) == 4 and all(
                  len(p) == len(set(p)) == 3 and set(p).issubset(genes[i]) and
                  not set(p).intersection(q) and
                  not set(p).intersection(view_union)
                  for i, p in enumerate(planted)), "PANEL_PROGRAM")

    for idx, p in enumerate(q_program):
        expected = (1 if idx == 6 else 2) if p is None else p
        if p is None:
            _require_role(q[idx] not in set(sum(genes, [])),
                          "NULL_QUERY_IS_PLANTED")
        else:
            _require_role(q[idx] in genes[p],
                          "POSITIVE_QUERY_NOT_IN_PROGRAM")
        _require_role(set(planted[expected]).issubset(panels[idx]) and
                      len(set(panels[idx]).intersection(genes[expected])) == 3,
                      "QUERY_PANEL_PROGRAM_BINDING")

    # Only the explicitly prospective shared NON-q members can overlap
    # between the three rare0 q panels and rare/null counterpart panels.
    for i in range(8):
        for j in range(i + 1, 8):
            allowed = set()
            if i in (0, 1, 2) and j in (0, 1, 2):
                allowed = set(planted[0])
            elif (i, j) == (3, 6):
                allowed = set(planted[1])
            elif (i, j) == (4, 7):
                allowed = set(planted[2])
            _require_role(set(panels[i]).intersection(panels[j]) == allowed,
                          "UNDECLARED_CROSS_QUERY_PANEL_REUSE")

    _require_role(plan["shared_cross_query_panel_policy"] ==
                  "ALLOWED_ONLY_WITHIN_V2__Q_NEVER_PANEL",
                  "UNAPPROVED_PANEL_POLICY")
    for flag in ("same_query_panel_distinct_8", "student_must_exclude_all_8_q",
                 "student_must_exclude_q_locus_atac"):
        _require_role(plan[flag] is True, "MISSING_RIGHTS_FLAG:" + flag)
    _require_role(plan["physical_common_address_count"] ==
                  source_roles["common_measured_addresses"],
                  "PHYSICAL_SUPPORT_COUNT")
    for key in ("world_generated", "generator_authorized", "model_trained",
                "C1_C6_scored"):
        _require_role(plan[key] is False, "UNLAWFUL_AUTHORITY:" + key)
    _require_role(plan["real_data_similarity"] == "NOT_EVALUATED",
                  "REALISM_NOT_EVALUATED")

def main() -> None:
    verify_original_sources()
    print(json.dumps(frozen_metadata_plan(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
