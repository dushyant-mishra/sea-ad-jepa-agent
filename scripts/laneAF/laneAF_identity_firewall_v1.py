#!/usr/bin/env python3
"""Lane A+F identity firewall.

This module is the single executable authority for what a Lane A+F frame is
allowed to carry. It exists so that the exclusion of pathology / outcome
columns happens BEFORE any join, not after, and so that the exclusion is
testable rather than asserted in prose.

Scope of this lane: IDENTITY AND PROVENANCE ONLY. No expression value, no
accessibility value, no pathology measurement, no project outcome.
"""
from __future__ import annotations

import re
import unicodedata

__all__ = [
    "ForbiddenFieldError",
    "FORBIDDEN_PATTERNS",
    "ALLOWED_IDENTITY_FIELDS",
    "normalize_field_name",
    "forbidden_columns",
    "assert_identity_only",
    "select_identity_columns",
]


class ForbiddenFieldError(RuntimeError):
    """Raised when a forbidden field reaches, or would reach, a joined frame."""


# Each entry is (rule_id, compiled regex over the NORMALIZED column name).
# Normalization lowercases, strips accents, and collapses every run of
# non-alphanumeric characters to a single underscore, so that "CERAD score",
# "cerad_score", "CERAD-Score" and "ceradScore" all normalize to the same
# token stream. Patterns are matched with re.search against that token stream.
_RAW_FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    ("adnc", r"(^|_)adnc(_|$)"),
    ("ad_neuropathologic_change", r"neuropath"),
    ("braak", r"braak"),
    ("cerad", r"cerad"),
    ("thal", r"(^|_)thal(_|$)"),
    ("cognitive_status", r"cognitive"),
    ("dementia", r"dementia"),
    ("mmse", r"mmse"),
    ("casi", r"casi"),
    ("moca", r"moca"),
    ("late_tdp43", r"(^|_)late(_|$)"),
    ("lewy_body", r"lewy"),
    ("caa", r"(^|_)caa(_|$)"),
    ("microinfarct", r"microinfarct"),
    ("arteriolosclerosis", r"arteriolosclerosis"),
    ("atherosclerosis", r"atherosclerosis"),
    ("apoe", r"apoe"),
    ("pathology_generic", r"patholog"),
    ("plaque", r"plaque"),
    ("tangle", r"tangle"),
    ("tau_at8", r"(^|_)at8(_|$)"),
    ("amyloid", r"amyloid|abeta|a_beta"),
    ("severely_affected", r"severely_affected"),
    ("pseudoprogression", r"pseudo_?progression|continuous_pseudo"),
    ("diagnosis", r"diagnos"),
    ("disease_state", r"(^|_)disease(_|$)"),
    ("outcome_generic", r"(^|_)outcome(s)?(_|$)"),
    ("target_outcome", r"relational_target|teacher_latent|td60"),
    ("education_proxy", r"years_of_education|highest_level_of_education"),
    # Expression / accessibility VALUES are also out of scope for this lane.
    ("expression_value", r"(^|_)(counts?|umis?|expression|logcp10k|lognorm|x_scvi|latent)(_|$)"),
    ("library_size_value", r"source_library|library_size|raw_library_total|n_counts|total_counts"),
    ("accessibility_value", r"fragment_counts|peak_counts|tile_counts|gene_score"),
)

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (rule_id, re.compile(pattern)) for rule_id, pattern in _RAW_FORBIDDEN_PATTERNS
)

# The closed whitelist of identity / provenance fields this lane may carry.
ALLOWED_IDENTITY_FIELDS: frozenset[str] = frozenset(
    {
        "index",
        "selection_row",
        "operator_index",
        "matrix_id",
        "source",
        "source_path",
        "source_row",
        "row_locator",
        "locator_kind",
        "donor_id",
        "canonical_donor_id",
        "cell_id",
        "canonical_cell_id",
        "exp_component_name",
        "atac_cell_id",
        "barcode",
        "library_prep",
        "library_token",
        "library_prefix",
        "ar_id",
        "sample_id",
        "sample_name",
        "load_name",
        "method",
        "assay_origin",
        "assay_origin_evidence",
        "region",
        "brain_region",
        "atac_paired",
        "atac_row",
        "atac_method",
        "eligibility_status",
        "reader_partition",
        "foundation_split",
    }
)


def normalize_field_name(name: str) -> str:
    """Collapse a column name to a comparable token stream."""
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def forbidden_columns(columns) -> list[tuple[str, str]]:
    """Return [(column_name, rule_id), ...] for every forbidden column present."""
    hits: list[tuple[str, str]] = []
    for column in columns:
        token = normalize_field_name(column)
        for rule_id, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(token):
                hits.append((str(column), rule_id))
                break
    return hits


def assert_identity_only(columns, context: str, *, enforce_whitelist: bool = True) -> None:
    """Fail closed if any column is forbidden, or (optionally) not whitelisted."""
    hits = forbidden_columns(columns)
    if hits:
        rendered = ", ".join(f"{name}[{rule}]" for name, rule in hits)
        raise ForbiddenFieldError(
            f"forbidden field(s) reached frame '{context}': {rendered}"
        )
    if enforce_whitelist:
        unknown = [
            str(column)
            for column in columns
            if normalize_field_name(column) not in ALLOWED_IDENTITY_FIELDS
        ]
        if unknown:
            raise ForbiddenFieldError(
                f"non-whitelisted field(s) reached frame '{context}': {', '.join(sorted(unknown))}"
            )


def select_identity_columns(columns, context: str) -> list[str]:
    """Return the whitelisted subset, refusing outright if anything forbidden is asked for."""
    hits = forbidden_columns(columns)
    if hits:
        rendered = ", ".join(f"{name}[{rule}]" for name, rule in hits)
        raise ForbiddenFieldError(
            f"refusing to select forbidden field(s) for '{context}': {rendered}"
        )
    return [c for c in columns if normalize_field_name(c) in ALLOWED_IDENTITY_FIELDS]
