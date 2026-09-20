"""Streaming/sufficient-statistics executor for FULL104 masking qualification.

This module is the production-scale adapter for the canonical in-memory reference in
full104_masking_qualification_runner_v1.  It consumes authenticated Phase-2 Level-4
CSR blocks, applies the frozen log1p10K normalization exactly once from raw counts and
per-row full-source libraries, and reproduces the primary masking estimand without
constructing a monolithic FULL104 x common-core matrix.

The algorithm intentionally mirrors the canonical reference:
- partner screening/fitting uses outer-training donors only;
- all four policy arms use the same ridge expression-proxy attacker;
- masks share the same common-random base and preserve exact burden;
- heldout scores are donor-centered correlation squared and source-balanced.

Only sufficient statistics are retained across block passes.  The heavy substrate
remains read-only and training/protected outcomes are never authorized here.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import csv
import hashlib
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np
import scipy.sparse as sp

from .full104_masking_qualification_runner_v1 import apply_burden_preserving_swaps


_EPS = 1e-12
_MANIFEST_COLUMNS = (
    "block_key",
    "source",
    "operator_index",
    "matrix_id",
    "rows",
    "nnz",
    "counts_path",
    "counts_sha256",
    "meta_path",
    "meta_sha256",
)
_META_COLUMNS = (
    "selection_row",
    "canonical_cell_id",
    "donor_id",
    "expression_row",
    "primary_row_weight",
    "source_library",
)
_METHODS = (
    "UNIFORM_RANDOM",
    "TOP8_CORRELATION",
    "RIDGE8_CONDITIONAL",
    "PREFIX3_SELECTIVE",
)


def _parse_source_library(raw: object) -> int:
    """Parse positive integral source-library semantics exactly."""

    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid source_library") from exc
    if not value.is_finite() or value <= 0 or value != value.to_integral_value():
        raise ValueError("invalid source_library")
    return int(value)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_int_vector(value: Any, name: str) -> np.ndarray:
    out = np.asarray(value)
    if out.ndim != 1 or not np.issubdtype(out.dtype, np.integer):
        raise ValueError(f"{name} must be a one-dimensional integer array")
    return out.astype(np.int64, copy=False)


def _seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _rank_by_score(cols: np.ndarray, scores: np.ndarray, count: int) -> np.ndarray:
    if cols.size != scores.size:
        raise ValueError("columns and scores must align")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("count must be a nonnegative integer")
    order = np.lexsort((cols, -scores))
    return cols[order[: min(count, cols.size)]]


def _resolve_under_root(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError("block manifest paths must be relative")
    path = (root / rel).resolve()
    resolved_root = root.resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("block manifest path escapes block_root") from exc
    return path


@dataclass(frozen=True)
class StreamingBlock:
    selection_rows: np.ndarray
    donor_code: np.ndarray
    X: sp.csr_matrix


class Full104ManifestStreamV1:
    """Authenticated read-only stream over Phase-2 expression blocks."""

    def __init__(
        self,
        *,
        manifest_path: Path | str,
        block_root: Path | str,
        expected_manifest_sha256: str,
        donor_id_to_code: Mapping[str, int],
        source_by_donor: np.ndarray,
        fold_by_donor: np.ndarray,
        universe_cols: np.ndarray,
        target_cols: np.ndarray,
        target_ids: np.ndarray,
        expected_cell_count: int,
        verify_block_hashes: bool = True,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.block_root = Path(block_root)
        self.expected_manifest_sha256 = str(expected_manifest_sha256)
        self.donor_id_to_code = {str(k): int(v) for k, v in donor_id_to_code.items()}
        self.source_by_donor = np.asarray(source_by_donor, dtype=object)
        self.fold_by_donor = _as_int_vector(fold_by_donor, "fold_by_donor")
        self.universe_cols = _as_int_vector(universe_cols, "universe_cols")
        self.target_cols = _as_int_vector(target_cols, "target_cols")
        self.target_ids = np.asarray(target_ids, dtype=object)
        if isinstance(expected_cell_count, bool) or not isinstance(expected_cell_count, int) or expected_cell_count < 1:
            raise ValueError("expected_cell_count must be a positive integer")
        self.expected_cell_count = expected_cell_count
        if verify_block_hashes is not True:
            raise ValueError("verify_block_hashes must be True for authenticated FULL104 execution")
        self.verify_block_hashes = True
        self._manifest_rows: list[dict[str, str]] | None = None
        self._validated = False
        self._matrix_width: int | None = None

    def _validate_metadata_vectors(self) -> None:
        if self.source_by_donor.ndim != 1 or self.source_by_donor.size == 0:
            raise ValueError("source_by_donor must be a nonempty one-dimensional array")
        if self.fold_by_donor.size != self.source_by_donor.size:
            raise ValueError("fold_by_donor must align with source_by_donor")
        values = sorted(self.donor_id_to_code.values())
        if values != list(range(self.source_by_donor.size)):
            raise ValueError("donor_id_to_code must map one-to-one onto contiguous donor codes")
        if len(self.donor_id_to_code) != self.source_by_donor.size:
            raise ValueError("donor_id_to_code cardinality must match donor metadata")
        if self.universe_cols.size < 2 or np.unique(self.universe_cols).size != self.universe_cols.size:
            raise ValueError("universe_cols must contain at least two unique columns")
        if self.universe_cols.min() < 0:
            raise ValueError("universe_cols cannot contain negative indices")
        if self.target_cols.size == 0 or np.unique(self.target_cols).size != self.target_cols.size:
            raise ValueError("target_cols must be nonempty and unique")
        if self.target_ids.ndim != 1 or self.target_ids.size != self.target_cols.size:
            raise ValueError("target_ids must align one-to-one with target_cols")
        if not set(map(int, self.target_cols)).issubset(set(map(int, self.universe_cols))):
            raise ValueError("every target must belong to universe_cols")

    def _load_manifest(self) -> list[dict[str, str]]:
        if self._manifest_rows is not None:
            return self._manifest_rows
        if not self.manifest_path.is_file():
            raise ValueError("block manifest is missing")
        if _sha256_file(self.manifest_path) != self.expected_manifest_sha256:
            raise ValueError("block manifest hash mismatch")
        with self.manifest_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _MANIFEST_COLUMNS:
                raise ValueError("block manifest schema mismatch")
            rows = [dict(row) for row in reader]
        if not rows:
            raise ValueError("block manifest is empty")
        if len({row["block_key"] for row in rows}) != len(rows):
            raise ValueError("block manifest contains duplicate block_key values")
        self._manifest_rows = rows
        return rows

    @staticmethod
    def _read_meta(path: Path) -> tuple[np.ndarray, list[str], np.ndarray, np.ndarray, np.ndarray]:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise ValueError("block metadata schema mismatch")
            selection: list[int] = []
            donor_ids: list[str] = []
            expression_rows: list[int] = []
            weights: list[float] = []
            libraries: list[int] = []
            for row in reader:
                selection.append(int(row["selection_row"]))
                donor_ids.append(str(row["donor_id"]))
                expression_rows.append(int(row["expression_row"]))
                weights.append(float(row["primary_row_weight"]))
                libraries.append(_parse_source_library(row["source_library"]))
        return (
            np.asarray(selection, dtype=np.int64),
            donor_ids,
            np.asarray(expression_rows, dtype=np.int64),
            np.asarray(weights, dtype=np.float64),
            np.asarray(libraries, dtype=np.int64),
        )

    def validate_layout(self) -> None:
        """Authenticate block geometry, hashes, row identity and raw-count semantics."""

        if self._validated:
            return
        self._validate_metadata_vectors()
        rows = self._load_manifest()
        seen_selection = np.zeros(self.expected_cell_count, dtype=np.bool_)
        donor_seen = np.zeros(self.source_by_donor.size, dtype=np.bool_)
        row_total = 0
        width: int | None = None

        for row in rows:
            counts_path = _resolve_under_root(self.block_root, row["counts_path"])
            meta_path = _resolve_under_root(self.block_root, row["meta_path"])
            if not counts_path.is_file() or not meta_path.is_file():
                raise ValueError(f"block file missing: {row['block_key']}")
            if _sha256_file(counts_path) != row["counts_sha256"]:
                raise ValueError(f"counts block hash mismatch: {row['block_key']}")
            if _sha256_file(meta_path) != row["meta_sha256"]:
                raise ValueError(f"metadata block hash mismatch: {row['block_key']}")

            matrix = sp.load_npz(counts_path).tocsr()
            expected_rows = int(row["rows"])
            expected_nnz = int(row["nnz"])
            if matrix.shape[0] != expected_rows or matrix.nnz != expected_nnz:
                raise ValueError(f"block geometry mismatch: {row['block_key']}")
            if width is None:
                width = int(matrix.shape[1])
            elif int(matrix.shape[1]) != width:
                raise ValueError("expression block widths are inconsistent")
            if matrix.data.size:
                raw = np.asarray(matrix.data)
                if not np.all(np.isfinite(raw)) or np.any(raw < 0) or not np.allclose(raw, np.rint(raw)):
                    raise ValueError(f"counts block is not nonnegative raw integer counts: {row['block_key']}")

            selection, donor_ids, expression_rows, weights, libraries = self._read_meta(meta_path)
            if selection.size != expected_rows:
                raise ValueError(f"metadata row count mismatch: {row['block_key']}")
            if np.any(selection < 0) or np.any(selection >= self.expected_cell_count):
                raise ValueError(f"selection_row out of range: {row['block_key']}")
            if np.unique(selection).size != selection.size or np.any(seen_selection[selection]):
                raise ValueError("duplicate selection_row across expression blocks")
            seen_selection[selection] = True
            if np.any(expression_rows < 0):
                raise ValueError(f"negative expression_row: {row['block_key']}")
            if np.any(~np.isfinite(weights)) or np.any(weights <= 0):
                raise ValueError(f"invalid primary_row_weight: {row['block_key']}")
            if np.any(libraries <= 0):
                raise ValueError(f"invalid source_library: {row['block_key']}")

            manifest_source = str(row["source"])
            for donor_id in donor_ids:
                if donor_id not in self.donor_id_to_code:
                    raise ValueError(f"unknown donor_id in expression block: {donor_id}")
                code = self.donor_id_to_code[donor_id]
                donor_seen[code] = True
                if str(self.source_by_donor[code]) != manifest_source:
                    raise ValueError("manifest source does not match donor source authority")
            row_total += expected_rows

        if row_total != self.expected_cell_count or not np.all(seen_selection):
            raise ValueError("stream does not close exactly over expected selection rows")
        if not np.all(donor_seen):
            raise ValueError("stream is missing one or more authorized donors")
        if width is None or int(self.universe_cols.max()) >= width:
            raise ValueError("authorized universe exceeds expression block width")
        self._matrix_width = width
        self._validated = True

    def revalidate_physical_inputs(self) -> str:
        """Re-hash authenticated Level-4 inputs without using the validation cache.

        Terminal execution calls this after evidence generation so a prior
        successful validate_layout() cannot hide later mutation of the manifest,
        counts blocks, or metadata blocks.
        """

        if not self.manifest_path.is_file():
            raise ValueError("block manifest is missing")
        manifest_digest = _sha256_file(self.manifest_path)
        if manifest_digest != self.expected_manifest_sha256:
            raise ValueError("block manifest hash mismatch during physical revalidation")
        rows = self._load_manifest()
        for row in rows:
            counts_path = _resolve_under_root(self.block_root, row["counts_path"])
            meta_path = _resolve_under_root(self.block_root, row["meta_path"])
            if not counts_path.is_file() or not meta_path.is_file():
                raise ValueError(
                    f"block file missing during physical revalidation: {row['block_key']}"
                )
            if _sha256_file(counts_path) != row["counts_sha256"]:
                raise ValueError(
                    f"counts block hash mismatch during physical revalidation: {row['block_key']}"
                )
            if _sha256_file(meta_path) != row["meta_sha256"]:
                raise ValueError(
                    f"metadata block hash mismatch during physical revalidation: {row['block_key']}"
                )
        return manifest_digest

    def iter_blocks(self, *, columns: np.ndarray) -> Iterator[StreamingBlock]:
        """Yield normalized sparse blocks for exactly the requested columns."""

        self.validate_layout()
        cols = _as_int_vector(columns, "columns")
        if cols.size == 0:
            raise ValueError("columns must be nonempty")
        if np.unique(cols).size != cols.size:
            raise ValueError("columns must be unique")
        if cols.min() < 0 or self._matrix_width is None or cols.max() >= self._matrix_width:
            raise ValueError("columns contain an out-of-range expression address")

        for row in self._load_manifest():
            counts_path = _resolve_under_root(self.block_root, row["counts_path"])
            meta_path = _resolve_under_root(self.block_root, row["meta_path"])
            raw = sp.load_npz(counts_path).tocsr()[:, cols].astype(np.float64)
            selection, donor_ids, _, _, libraries = self._read_meta(meta_path)
            donor_code = np.asarray([self.donor_id_to_code[donor_id] for donor_id in donor_ids], dtype=np.int64)
            out = raw.tocsr(copy=True)
            if out.data.size:
                data_rows = np.repeat(np.arange(out.shape[0], dtype=np.int64), np.diff(out.indptr))
                scale = 10000.0 / libraries[data_rows].astype(np.float64)
                out.data = np.log1p(out.data * scale)
            yield StreamingBlock(selection_rows=selection, donor_code=donor_code, X=out)


@dataclass
class _DonorStats:
    n: int
    sum_y: float
    sum_y2: float
    sum_x: np.ndarray
    sum_x2: np.ndarray
    sum_xy: np.ndarray
    sum_xx: np.ndarray | None


def _collect_stats(
    stream: Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    target_col: int,
    feature_cols: np.ndarray,
    need_xx: bool,
) -> dict[int, _DonorStats]:
    donors = _as_int_vector(donors, "donors")
    features = _as_int_vector(feature_cols, "feature_cols")
    if int(target_col) in set(map(int, features)):
        raise ValueError("feature_cols cannot contain target_col")
    requested = np.concatenate((np.asarray([int(target_col)], dtype=np.int64), features))
    wanted = set(map(int, donors))
    stats: dict[int, _DonorStats] = {}

    for block in stream.iter_blocks(columns=requested):
        present = sorted(set(map(int, block.donor_code)) & wanted)
        for donor in present:
            ix = block.donor_code == donor
            local = block.X[ix]
            n = int(local.shape[0])
            if n == 0:
                continue
            y = local[:, 0].toarray().reshape(-1)
            A = local[:, 1:].tocsr()
            sx = np.asarray(A.sum(axis=0)).reshape(-1)
            sx2 = np.asarray(A.power(2).sum(axis=0)).reshape(-1)
            sxy = np.asarray(A.T @ y).reshape(-1)
            sy = float(np.sum(y))
            sy2 = float(np.dot(y, y))
            sxx = (A.T @ A).toarray() if need_xx and features.size else (
                np.zeros((0, 0), dtype=np.float64) if need_xx else None
            )
            current = stats.get(donor)
            if current is None:
                stats[donor] = _DonorStats(
                    n=n,
                    sum_y=sy,
                    sum_y2=sy2,
                    sum_x=sx.astype(np.float64, copy=False),
                    sum_x2=sx2.astype(np.float64, copy=False),
                    sum_xy=sxy.astype(np.float64, copy=False),
                    sum_xx=None if sxx is None else np.asarray(sxx, dtype=np.float64),
                )
            else:
                current.n += n
                current.sum_y += sy
                current.sum_y2 += sy2
                current.sum_x += sx
                current.sum_x2 += sx2
                current.sum_xy += sxy
                if need_xx:
                    assert current.sum_xx is not None and sxx is not None
                    current.sum_xx += sxx

    missing = [int(donor) for donor in donors if int(donor) not in stats]
    if missing:
        raise ValueError(f"stream contains no rows for requested donors: {missing[:5]}")
    return stats


def _source_balanced_abs_corr_scores(
    stream: Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    target_col: int,
    candidate_cols: np.ndarray,
) -> np.ndarray:
    cols = _as_int_vector(candidate_cols, "candidate_cols")
    if cols.size == 0:
        return np.empty(0, dtype=np.float64)
    stats = _collect_stats(
        stream,
        donors=donors,
        target_col=target_col,
        feature_cols=cols,
        need_xx=False,
    )
    per_source: dict[object, list[np.ndarray]] = {}
    for donor in donors:
        d = int(donor)
        st = stats[d]
        vx = np.maximum(st.sum_x2 - (st.sum_x * st.sum_x) / st.n, 0.0)
        vy = max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
        cov = st.sum_xy - st.sum_x * (st.sum_y / st.n)
        den = np.sqrt(vx * vy)
        corr = np.divide(np.abs(cov), den, out=np.zeros_like(cov), where=den > _EPS)
        per_source.setdefault(stream.source_by_donor[d], []).append(corr)
    return np.mean(
        np.vstack([np.mean(np.vstack(values), axis=0) for values in per_source.values()]),
        axis=0,
    )


def _standardized_components(st: _DonorStats) -> tuple[np.ndarray, np.ndarray, float]:
    if st.sum_x.size == 0:
        return np.zeros((0, 0), dtype=np.float64), np.empty(0, dtype=np.float64), max(
            st.sum_y2 - (st.sum_y * st.sum_y) / st.n,
            0.0,
        )
    if st.sum_xx is None:
        raise ValueError("standardized sufficient statistics require sum_xx")
    mean_x = st.sum_x / st.n
    var_x = np.maximum(st.sum_x2 / st.n - mean_x * mean_x, 0.0)
    sd = np.sqrt(var_x)
    sd = np.where(sd > _EPS, sd, 1.0)
    centered_xx = st.sum_xx - np.outer(st.sum_x, st.sum_x) / st.n
    gram = centered_xx / (sd[:, None] * sd[None, :])
    centered_xy = st.sum_xy - st.sum_x * (st.sum_y / st.n)
    rhs = centered_xy / sd
    rss_y = max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
    return gram, rhs, rss_y


def _fit_ridge_weights(
    stream: Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    target_col: int,
    feature_cols: np.ndarray,
    alpha: float,
) -> np.ndarray:
    features = _as_int_vector(feature_cols, "feature_cols")
    if features.size == 0:
        return np.empty(0, dtype=np.float64)
    stats = _collect_stats(
        stream,
        donors=donors,
        target_col=target_col,
        feature_cols=features,
        need_xx=True,
    )
    gram = np.zeros((features.size, features.size), dtype=np.float64)
    rhs = np.zeros(features.size, dtype=np.float64)
    rss_y = 0.0
    n_total = 0
    for donor in donors:
        st = stats[int(donor)]
        local_gram, local_rhs, local_rss = _standardized_components(st)
        gram += local_gram
        rhs += local_rhs
        rss_y += local_rss
        n_total += st.n
    if n_total == 0:
        raise ValueError("ridge fit requires training rows")
    scale = float(np.sqrt(max(rss_y / n_total, 0.0)))
    if scale <= _EPS:
        return np.zeros(features.size, dtype=np.float64)
    regularized = gram + (float(alpha) * n_total) * np.eye(features.size, dtype=np.float64)
    return np.linalg.solve(regularized, rhs / scale)


def _source_balanced_prediction_score(
    stream: Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    target_col: int,
    feature_cols: np.ndarray,
    weights: np.ndarray,
) -> float:
    features = _as_int_vector(feature_cols, "feature_cols")
    stats = _collect_stats(
        stream,
        donors=donors,
        target_col=target_col,
        feature_cols=features,
        need_xx=True,
    )
    per_source: dict[object, list[float]] = {}
    for donor in donors:
        d = int(donor)
        gram, rhs, rss_y = _standardized_components(stats[d])
        pred_ss = float(weights @ gram @ weights)
        cov = float(weights @ rhs)
        den = float(np.sqrt(max(rss_y, 0.0) * max(pred_ss, 0.0)))
        r = 0.0 if den <= _EPS else cov / den
        per_source.setdefault(stream.source_by_donor[d], []).append(r * r)
    return float(np.mean([np.mean(values) for values in per_source.values()]))


def _single_partner_score(
    stream: Full104ManifestStreamV1,
    *,
    donors: np.ndarray,
    target_col: int,
    partner_col: int,
) -> float:
    features = np.asarray([int(partner_col)], dtype=np.int64)
    stats = _collect_stats(
        stream,
        donors=donors,
        target_col=target_col,
        feature_cols=features,
        need_xx=False,
    )
    per_source: dict[object, list[float]] = {}
    for donor in donors:
        d = int(donor)
        st = stats[d]
        vx = max(float(st.sum_x2[0] - (st.sum_x[0] * st.sum_x[0]) / st.n), 0.0)
        vy = max(st.sum_y2 - (st.sum_y * st.sum_y) / st.n, 0.0)
        cov = float(st.sum_xy[0] - st.sum_x[0] * (st.sum_y / st.n))
        den = float(np.sqrt(vx * vy))
        r = 0.0 if den <= _EPS else cov / den
        per_source.setdefault(stream.source_by_donor[d], []).append(r * r)
    return float(np.mean([np.mean(values) for values in per_source.values()]))


def _ridge_primary_score(
    stream: Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    heldout_donors: np.ndarray,
    target_col: int,
    mask: set[int],
    feature_count: int,
    alpha: float,
) -> float:
    visible = np.asarray(
        [int(col) for col in stream.universe_cols if int(col) not in mask and int(col) != int(target_col)],
        dtype=np.int64,
    )
    if visible.size == 0:
        return 0.0
    screen = _source_balanced_abs_corr_scores(
        stream,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=visible,
    )
    features = _rank_by_score(visible, screen, int(feature_count))
    weights = _fit_ridge_weights(
        stream,
        donors=train_donors,
        target_col=target_col,
        feature_cols=features,
        alpha=float(alpha),
    )
    return _source_balanced_prediction_score(
        stream,
        donors=heldout_donors,
        target_col=target_col,
        feature_cols=features,
        weights=weights,
    )


def _top_partners(
    stream: Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    target_col: int,
    cap: int,
) -> tuple[int, ...]:
    candidates = np.asarray(
        [int(col) for col in stream.universe_cols if int(col) != int(target_col)],
        dtype=np.int64,
    )
    score = _source_balanced_abs_corr_scores(
        stream,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=candidates,
    )
    return tuple(map(int, _rank_by_score(candidates, score, int(cap))))


def _ridge_partners(
    stream: Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    target_col: int,
    candidate_pool_count: int,
    cap: int,
    alpha: float,
) -> tuple[int, ...]:
    candidates = np.asarray(
        [int(col) for col in stream.universe_cols if int(col) != int(target_col)],
        dtype=np.int64,
    )
    screen = _source_balanced_abs_corr_scores(
        stream,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=candidates,
    )
    pool = _rank_by_score(candidates, screen, int(candidate_pool_count))
    weights = _fit_ridge_weights(
        stream,
        donors=train_donors,
        target_col=target_col,
        feature_cols=pool,
        alpha=float(alpha),
    )
    order = np.lexsort((pool, -np.abs(weights)))
    return tuple(map(int, pool[order[: min(int(cap), pool.size)]]))


def _inner_donor_groups(
    stream: Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    global_seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    groups: list[list[int]] = [[], [], []]
    sources = np.asarray(stream.source_by_donor, dtype=object)
    for source in sorted(set(sources[train_donors]), key=str):
        donors = train_donors[sources[train_donors] == source]
        rng = np.random.default_rng(_seed("V5_PREFIX3_INNER", global_seed, source))
        perm = rng.permutation(donors)
        for index, donor in enumerate(perm):
            groups[index % 3].append(int(donor))
    if any(len(group) == 0 for group in groups):
        return None
    return tuple(np.asarray(sorted(group), dtype=np.int64) for group in groups)  # type: ignore[return-value]


def _prefix3_partners(
    stream: Full104ManifestStreamV1,
    *,
    train_donors: np.ndarray,
    target_col: int,
    candidate_count: int,
    cap: int,
    floor: float,
    reduction: float,
    global_seed: int,
) -> tuple[int, ...]:
    groups = _inner_donor_groups(stream, train_donors=train_donors, global_seed=global_seed)
    if groups is None:
        return ()
    universe = np.asarray(
        [int(col) for col in stream.universe_cols if int(col) != int(target_col)],
        dtype=np.int64,
    )
    selected_sets: list[tuple[int, ...]] = []
    for rotation in range(3):
        screen_donors = groups[rotation]
        rank_donors = groups[(rotation + 1) % 3]
        validate_donors = groups[(rotation + 2) % 3]
        screen = _source_balanced_abs_corr_scores(
            stream,
            donors=screen_donors,
            target_col=target_col,
            candidate_cols=universe,
        )
        candidates = _rank_by_score(universe, screen, int(candidate_count))
        if candidates.size == 0:
            selected_sets.append(())
            continue

        def remaining_proxy_score(remaining: np.ndarray) -> float:
            if remaining.size == 0:
                return 0.0
            rank_score = _source_balanced_abs_corr_scores(
                stream,
                donors=rank_donors,
                target_col=target_col,
                candidate_cols=remaining,
            )
            best = int(_rank_by_score(remaining, rank_score, 1)[0])
            return _single_partner_score(
                stream,
                donors=validate_donors,
                target_col=target_col,
                partner_col=best,
            )

        baseline = remaining_proxy_score(candidates)
        if baseline < float(floor):
            selected_sets.append(())
            continue
        chosen: tuple[int, ...] = ()
        for k in range(1, min(int(cap), candidates.size) + 1):
            remaining = candidates[k:]
            if remaining_proxy_score(remaining) <= (1.0 - float(reduction)) * baseline:
                chosen = tuple(map(int, candidates[:k]))
                break
        selected_sets.append(chosen)

    support: dict[int, int] = {}
    for selected in selected_sets:
        for col in set(selected):
            support[col] = support.get(col, 0) + 1
    if not support:
        return ()
    items = np.asarray(sorted(support), dtype=np.int64)
    evidence = _source_balanced_abs_corr_scores(
        stream,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=items,
    )
    support_count = np.asarray([support[int(col)] for col in items], dtype=np.int64)
    order = np.lexsort((items, -evidence, -support_count))
    return tuple(map(int, items[order[: min(int(cap), items.size)]]))


def _base_uniform_mask(
    universe_cols: np.ndarray,
    *,
    target_col: int,
    co_mask_count: int,
    fold_index: int,
    target_id: object,
    global_seed: int,
) -> set[int]:
    universe = _as_int_vector(universe_cols, "universe_cols")
    pool = universe[universe != int(target_col)]
    if co_mask_count < 0 or co_mask_count > pool.size:
        raise ValueError("co-mask burden is infeasible for the supplied universe")
    rng = np.random.default_rng(
        _seed("V5_COMMON_RANDOM_BASE_MASK", global_seed, fold_index, target_id, universe.size)
    )
    chosen = rng.choice(pool, size=co_mask_count, replace=False) if co_mask_count else np.empty(0, dtype=np.int64)
    return {int(target_col), *map(int, chosen)}


def _removable_order(
    base_mask: set[int],
    *,
    target_col: int,
    fold_index: int,
    target_id: object,
    global_seed: int,
) -> tuple[int, ...]:
    candidates = [int(col) for col in base_mask if int(col) != int(target_col)]
    candidates.sort(
        key=lambda col: hashlib.sha256(
            f"V5_MASK_REMOVE|{global_seed}|{fold_index}|{target_id}|{col}".encode("utf-8")
        ).digest()
    )
    return tuple(candidates)


def run_primary_fold_streaming(
    *,
    stream: Full104ManifestStreamV1,
    fold_index: int,
    parameters: Any,
    evidence_budget: Any,
    global_seed: int,
) -> list[dict[str, Any]]:
    """Run one canonical outer fold from authenticated blocks using sufficient statistics."""

    stream.validate_layout()
    parameters.validate()
    evidence_budget.validate()
    if isinstance(fold_index, bool) or not isinstance(fold_index, int):
        raise ValueError("fold_index must be an integer")
    heldout_donors = np.flatnonzero(stream.fold_by_donor == fold_index).astype(np.int64)
    train_donors = np.flatnonzero(stream.fold_by_donor != fold_index).astype(np.int64)
    if heldout_donors.size == 0 or train_donors.size == 0:
        raise ValueError("outer fold must contain both training and heldout donors")

    eligible_non_target = int(stream.universe_cols.size - 1)
    co_mask_count = int(evidence_budget.mask_count(eligible_non_target))
    if int(parameters.targeted_partner_cap) > co_mask_count:
        raise ValueError("targeted partner cap exceeds the authorized co-mask burden")

    rows: list[dict[str, Any]] = []
    for target_index, (raw_target, target_id) in enumerate(zip(stream.target_cols, stream.target_ids)):
        target_col = int(raw_target)
        base_mask = _base_uniform_mask(
            stream.universe_cols,
            target_col=target_col,
            co_mask_count=co_mask_count,
            fold_index=fold_index,
            target_id=target_id,
            global_seed=int(global_seed),
        )
        uniform_score = _ridge_primary_score(
            stream,
            train_donors=train_donors,
            heldout_donors=heldout_donors,
            target_col=target_col,
            mask=base_mask,
            feature_count=int(parameters.ridge_score_feature_count),
            alpha=float(parameters.ridge_alpha),
        )
        policy_targets = {
            "UNIFORM_RANDOM": (),
            "TOP8_CORRELATION": _top_partners(
                stream,
                train_donors=train_donors,
                target_col=target_col,
                cap=int(parameters.targeted_partner_cap),
            ),
            "RIDGE8_CONDITIONAL": _ridge_partners(
                stream,
                train_donors=train_donors,
                target_col=target_col,
                candidate_pool_count=int(parameters.ridge_candidate_pool_count),
                cap=int(parameters.targeted_partner_cap),
                alpha=float(parameters.ridge_alpha),
            ),
            "PREFIX3_SELECTIVE": _prefix3_partners(
                stream,
                train_donors=train_donors,
                target_col=target_col,
                candidate_count=int(parameters.prefix_candidate_count),
                cap=int(parameters.targeted_partner_cap),
                floor=float(parameters.prefix_floor),
                reduction=float(parameters.prefix_reduction),
                global_seed=int(global_seed),
            ),
        }
        removable = _removable_order(
            base_mask,
            target_col=target_col,
            fold_index=fold_index,
            target_id=target_id,
            global_seed=int(global_seed),
        )
        for method in _METHODS:
            targeted = tuple(map(int, policy_targets[method]))
            if method == "UNIFORM_RANDOM":
                mask = set(base_mask)
                score = uniform_score
            else:
                mask = apply_burden_preserving_swaps(
                    base_mask=base_mask,
                    target_col=target_col,
                    targeted_cols=targeted,
                    removable_order=removable,
                )
                score = _ridge_primary_score(
                    stream,
                    train_donors=train_donors,
                    heldout_donors=heldout_donors,
                    target_col=target_col,
                    mask=mask,
                    feature_count=int(parameters.ridge_score_feature_count),
                    alpha=float(parameters.ridge_alpha),
                )
            effective = len([col for col in targeted if col not in base_mask and col != target_col])
            rows.append(
                {
                    "fold": int(fold_index),
                    "target_index": int(target_index),
                    "target_col": target_col,
                    "target_id": target_id,
                    "method": method,
                    "primary_attacker_id": parameters.primary_attacker_id,
                    "primary_score_id": parameters.primary_score_id,
                    "score": float(score),
                    "uniform_score": float(uniform_score),
                    "delta": float(uniform_score - score),
                    "targeted_cols": targeted,
                    "targeted_n": len(targeted),
                    "effective_targeted_n": int(effective),
                    "mask_cardinality": len(mask),
                    "uniform_mask_cardinality": len(base_mask),
                }
            )
    return rows


def run_all_primary_folds_streaming(
    *,
    stream: Full104ManifestStreamV1,
    parameters: Any,
    evidence_budget: Any,
    global_seed: int,
) -> list[dict[str, Any]]:
    """Execute every declared outer fold represented by donor metadata."""

    stream.validate_layout()
    output: list[dict[str, Any]] = []
    for fold_index in sorted(set(map(int, stream.fold_by_donor))):
        output.extend(
            run_primary_fold_streaming(
                stream=stream,
                fold_index=fold_index,
                parameters=parameters,
                evidence_budget=evidence_budget,
                global_seed=global_seed,
            )
        )
    return output
