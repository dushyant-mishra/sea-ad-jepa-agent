"""SEA-AD spatial metadata pathology firewall (Lane R4, 2026-09-28).

Purpose
-------
The SEA-AD public spatial AnnData objects (MTG MERFISH, CaH Xenium) carry the
full donor neuropathology / cognition table inline in ``obs``.  A structural
feasibility audit is authorised to record that those columns EXIST and is NOT
authorised to read their values.

This module makes that exclusion *executable* rather than declarative.  Nothing
in the audit reads an ``obs`` column directly; every read goes through
``load_allowlisted_obs`` / ``assert_frame_is_clean``, which fail closed.

Design
------
Three disjoint classes, evaluated against a normalised column name:

``PROTECTED``           neuropathology, staging, cognition, disease-group
                        proxies and genetic risk.  Reading a value is a
                        governance violation.  Existence may be recorded.
``DENY_NOT_NEEDED``     donor demographics / tissue covariates.  Not protected
                        outcomes, but not required by a structural audit, so
                        they are refused too.  Kept as a separate class so the
                        report does not overclaim that demographics are
                        "protected pathology".
``ALLOW``               assay identity, specimen/donor identity, cell-type
                        annotation, segmentation geometry and QC counters.

Matching is *substring on a normalised name*, not equality, so that release-to-
release column renames ("Braak" -> "Braak stage" -> "braak_stage") stay caught.
Because substring matching is broad, ALLOW is an explicit enumeration and the
resolver is deny-by-default: a column that matches nothing at all is REFUSED,
not admitted.

Fail-closed contract
--------------------
``load_allowlisted_obs`` raises ``PathologyFirewallViolation`` if *any*
requested column is not in ALLOW, and additionally re-screens the materialised
frame so that a column smuggled in by a loader alias cannot survive.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

__all__ = [
    "PathologyFirewallViolation",
    "PROTECTED_PATTERNS",
    "DENY_NOT_NEEDED_PATTERNS",
    "ALLOW_PATTERNS",
    "normalise",
    "classify_column",
    "screen_columns",
    "assert_frame_is_clean",
    "load_allowlisted_obs",
]


class PathologyFirewallViolation(RuntimeError):
    """Raised when protected or non-allow-listed metadata would be read."""


# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------
# Neuropathology staging, cognition, disease group, genetic risk.
PROTECTED_PATTERNS: tuple[str, ...] = (
    "braak",
    "cerad",
    "thal",
    "adnc",
    "neuropathological change",
    "neuropathologic change",
    "cognitive status",
    "dementia",
    "diagnosis",
    "mmse",
    "casi",
    "moca",
    "lewy body",
    "late",  # SEA-AD column "LATE" = limbic-predominant age-related TDP-43
    "caa",
    "arteriolosclerosis",
    "atherosclerosis",
    "microinfarct",
    "pseudo-progression",
    "pseudoprogression",
    "apoe",
    "neurotypical reference",  # disease-group membership proxy
    "primary study name",      # SEA-AD vs reference cohort => group proxy
    "secondary study name",
)

# Donor demographics / tissue covariates: not protected outcomes, but not
# needed by a structural audit, so also refused.
DENY_NOT_NEEDED_PATTERNS: tuple[str, ...] = (
    "age at death",
    "sex",
    "gender",
    "race",
    "hispanic",
    "education",
    "pmi",
    "brain ph",
    "fresh brain weight",
)

# Assay identity, cell-type annotation, segmentation geometry, QC counters.
ALLOW_PATTERNS: tuple[str, ...] = (
    # identity
    "donor id",
    "specimen barcode",
    "specimen_id",
    "lims2_barcode",
    "merscope",
    "section",
    "brain region",
    "region",
    "organism",
    "cell id",
    "cell_id",
    "barcode",
    "uuid",
    "_index",
    # cell-type annotation
    "class",
    "subclass",
    "supertype",
    "cell_labels",
    "neighborhood",
    # segmentation geometry / counts
    "cell volume",
    "cell_area",
    "nucleus_area",
    "nucleus_count",
    "genes detected",
    "number of spots",
    "total_counts",
    "transcript_counts",
    "control_probe_counts",
    "control_codeword_counts",
    "genomic_control_counts",
    "unassigned_codeword_counts",
    "deprecated_codeword_counts",
    "z_level",
    "segmentation_method",
    # spatial position within tissue
    "layer annotation",
    "depth from pia",
    # QC / processing
    "detection_qc",
    "final_qc",
    "tissue_qc",
    "sampling_qc",
    "needs_mask_qc",
    "qc_notes",
    "used in analysis",
    "exclusion_masked_cells",
    "aligned_",
    "annotated_",
    "imaging_date",
    "image_loc",
)

_WS = re.compile(r"\s+")


def normalise(name: str) -> str:
    """Lower-case and collapse separators so renames stay matchable."""
    s = str(name).strip().lower()
    s = s.replace("-", " ").replace(".", " ")
    s = _WS.sub(" ", s)
    return s


def _matches(norm: str, patterns: Iterable[str]) -> list[str]:
    hits = []
    for p in patterns:
        pn = normalise(p)
        # Underscored patterns must match the underscored form too.
        if pn in norm or normalise(p).replace(" ", "_") in norm.replace(" ", "_"):
            hits.append(p)
    return hits


def classify_column(name: str) -> tuple[str, list[str]]:
    """Return ``(verdict, matched_patterns)``.

    Verdict is one of ``PROTECTED``, ``DENY_NOT_NEEDED``, ``ALLOW``,
    ``REFUSED_UNKNOWN``.  PROTECTED is checked first so that a column which
    matches both a protected and an allow pattern (e.g. a hypothetical
    "Braak region") is refused, never admitted.
    """
    norm = normalise(name)

    hits = _matches(norm, PROTECTED_PATTERNS)
    if hits:
        return "PROTECTED", hits

    hits = _matches(norm, DENY_NOT_NEEDED_PATTERNS)
    if hits:
        return "DENY_NOT_NEEDED", hits

    hits = _matches(norm, ALLOW_PATTERNS)
    if hits:
        return "ALLOW", hits

    return "REFUSED_UNKNOWN", []


def screen_columns(columns: Sequence[str]) -> dict[str, list[str]]:
    """Classify every column name.  Pure inspection; reads no values."""
    out: dict[str, list[str]] = {
        "PROTECTED": [],
        "DENY_NOT_NEEDED": [],
        "ALLOW": [],
        "REFUSED_UNKNOWN": [],
    }
    for c in columns:
        verdict, _ = classify_column(c)
        out[verdict].append(str(c))
    return out


def assert_frame_is_clean(frame_columns: Sequence[str]) -> None:
    """Fail closed if any column in a materialised frame is not ALLOW."""
    screened = screen_columns(frame_columns)
    bad = (
        screened["PROTECTED"]
        + screened["DENY_NOT_NEEDED"]
        + screened["REFUSED_UNKNOWN"]
    )
    if bad:
        raise PathologyFirewallViolation(
            "refused: frame carries non-allow-listed columns "
            f"{sorted(bad)!r} (protected={screened['PROTECTED']!r})"
        )


def load_allowlisted_obs(h5ad_path: str, columns: Sequence[str]) -> "object":
    """Read only ``columns`` from ``h5ad_path``'s ``obs``, decoding categoricals.

    Every requested column is screened *before* the file is opened, and the
    resulting frame is screened again afterwards.  ``X`` is never touched.
    """
    import h5py
    import numpy as np
    import pandas as pd

    requested = list(columns)
    screened = screen_columns(requested)
    refused = (
        screened["PROTECTED"]
        + screened["DENY_NOT_NEEDED"]
        + screened["REFUSED_UNKNOWN"]
    )
    if refused:
        raise PathologyFirewallViolation(
            f"refused: requested non-allow-listed columns {sorted(refused)!r} "
            f"(protected={screened['PROTECTED']!r}) from {h5ad_path}"
        )

    data: dict[str, object] = {}
    with h5py.File(h5ad_path, "r") as f:
        obs = f["obs"]
        for col in requested:
            if col not in obs:
                continue
            node = obs[col]
            if isinstance(node, h5py.Group):  # categorical
                cats = node["categories"][...]
                codes = node["codes"][...]
                cats = np.asarray(
                    [c.decode() if isinstance(c, bytes) else c for c in cats],
                    dtype=object,
                )
                vals = np.where(codes >= 0, cats[np.clip(codes, 0, None)], None)
                data[col] = vals
            else:
                arr = node[...]
                if arr.dtype.kind in ("S", "O"):
                    arr = np.asarray(
                        [a.decode() if isinstance(a, bytes) else a for a in arr],
                        dtype=object,
                    )
                data[col] = arr

    frame = pd.DataFrame(data)
    assert_frame_is_clean(list(frame.columns))
    return frame
