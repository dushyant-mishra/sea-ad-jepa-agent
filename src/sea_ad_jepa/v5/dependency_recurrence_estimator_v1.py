"""DONOR_STRATIFIED_RANK_RECURRENCE_V1 -- dependency estimator for masking qualification.

Estimates address-address dependence as RECURRENCE of within-donor rank association across
independent donor strata, rather than as a single pooled FULL104 coefficient. A pooled
coefficient can be dominated by source, operator, donor, depth and composition; a
within-donor rank statistic removes per-donor mean structure by construction and is
invariant to per-address monotone scaling.

Every edge produced here is a statistical dependency under a declared estimator. It is NOT
a causal or biological claim.

Forbidden as input, by construction: hidden target values, target ranks or statistics, QC,
depth, detection, visibility, source/operator/donor/dataset labels as features, ontology,
pathway, coordinates, gene symbols, biotype. Source and donor codes enter ONLY as
stratification and balancing keys, never as predictive features.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

ESTIMATOR_ID = "DONOR_STRATIFIED_RANK_RECURRENCE_V1"


def _rankdata_columns(x: np.ndarray) -> np.ndarray:
    """Average-rank transform of each column, ties averaged."""
    n = x.shape[0]
    order = np.argsort(x, axis=0, kind="mergesort")
    ranks = np.empty_like(x, dtype=np.float64)
    rows = np.arange(n)[:, None]
    ranks[order, np.arange(x.shape[1])[None, :]] = rows.astype(np.float64)
    # average ties column-wise
    for j in range(x.shape[1]):
        col = x[:, j]
        o = order[:, j]
        sortedc = col[o]
        i = 0
        while i < n:
            k = i
            while k + 1 < n and sortedc[k + 1] == sortedc[i]:
                k += 1
            if k > i:
                ranks[o[i:k + 1], j] = (i + k) / 2.0
            i = k + 1
    return ranks


def _corr_from_ranks(r: np.ndarray) -> np.ndarray:
    c = r - r.mean(axis=0, keepdims=True)
    sd = np.sqrt((c * c).sum(axis=0))
    sd[sd == 0] = np.nan
    cn = c / sd
    return cn.T @ cn


@dataclass(frozen=True)
class DonorStratifiedRankRecurrenceV1:
    """top_k / recurrence_fraction come from the frozen grid.

    min_evaluable_strata is a STRUCTURAL guard, not a tuned threshold: an edge supported by
    fewer strata than this has no recurrence evidence by definition.
    """

    top_k: int
    recurrence_fraction: float
    min_evaluable_strata: int

    def __post_init__(self) -> None:
        if not isinstance(self.top_k, int) or self.top_k < 1:
            raise ValueError("top_k must be a positive int")
        if not (0.0 < float(self.recurrence_fraction) <= 1.0):
            raise ValueError("recurrence_fraction must be in (0, 1]")
        if not isinstance(self.min_evaluable_strata, int) or self.min_evaluable_strata < 2:
            raise ValueError("min_evaluable_strata must be an int >= 2")

    # ------------------------------------------------------------------ core
    def stratum_neighbours(self, values: np.ndarray, measurable: np.ndarray) -> Tuple[
            Dict[int, Tuple[int, ...]], np.ndarray]:
        """Top-k neighbours within one stratum, plus the evaluability mask of addresses.

        An address is evaluable in a stratum only if it is measurable there AND has nonzero
        within-stratum variance. A constant column carries no association evidence.
        """
        n_addr = values.shape[1]
        usable = np.asarray(measurable, dtype=bool).copy()
        if values.shape[0] < 3:
            return {}, np.zeros(n_addr, dtype=bool)
        var = values.var(axis=0)
        usable &= var > 0
        idx = np.flatnonzero(usable)
        if idx.size < 2:
            return {}, usable
        rho = _corr_from_ranks(_rankdata_columns(values[:, idx]))
        np.fill_diagonal(rho, np.nan)
        out: Dict[int, Tuple[int, ...]] = {}
        k = min(self.top_k, idx.size - 1)
        mag = np.abs(rho)
        for local, global_a in enumerate(idx):
            row = mag[local]
            finite = np.flatnonzero(np.isfinite(row))
            if finite.size == 0:
                continue
            # deterministic ordering: by -|rho| then by global address index
            order = sorted(finite, key=lambda j: (-float(row[j]), int(idx[j])))
            out[int(global_a)] = tuple(int(idx[j]) for j in order[:k])
        return out, usable

    def fit(
        self,
        *,
        values: np.ndarray,
        donor_codes: np.ndarray,
        measurable_by_donor: np.ndarray,
        source_by_donor: Optional[np.ndarray] = None,
    ) -> Dict[str, object]:
        """Recurrent directed edges (a -> b) with donor- and source-balanced votes."""
        values = np.asarray(values, dtype=np.float64)
        donor_codes = np.asarray(donor_codes)
        measurable_by_donor = np.asarray(measurable_by_donor, dtype=bool)
        n_addr = values.shape[1]
        donors = np.unique(donor_codes)

        if source_by_donor is None:
            weight_of_donor = {int(d): 1.0 for d in donors}
        else:
            source_by_donor = np.asarray(source_by_donor)
            per_source: Dict[object, int] = {}
            for d in donors:
                s = source_by_donor[int(d)]
                per_source[s] = per_source.get(s, 0) + 1
            n_sources = len(per_source)
            # each SOURCE contributes equally; donors split their source's weight evenly,
            # so a source cannot gain authority by having more donors or more cells.
            weight_of_donor = {
                int(d): 1.0 / (n_sources * per_source[source_by_donor[int(d)]]) for d in donors
            }

        votes: Dict[Tuple[int, int], float] = {}
        evaluable: Dict[Tuple[int, int], float] = {}
        strata_used = 0
        for d in donors:
            sel = donor_codes == d
            if int(sel.sum()) < 3:
                continue
            nbrs, usable = self.stratum_neighbours(values[sel], measurable_by_donor[int(d)])
            if not nbrs:
                continue
            strata_used += 1
            w = weight_of_donor[int(d)]
            live = np.flatnonzero(usable)
            # denominator: every ordered pair jointly evaluable in this stratum
            for a in live:
                for b in live:
                    if a != b:
                        key = (int(a), int(b))
                        evaluable[key] = evaluable.get(key, 0.0) + w
            for a, tops in nbrs.items():
                for b in tops:
                    key = (int(a), int(b))
                    votes[key] = votes.get(key, 0.0) + w

        # count raw strata per pair for the structural guard
        raw_strata: Dict[Tuple[int, int], int] = {}
        for d in donors:
            sel = donor_codes == d
            if int(sel.sum()) < 3:
                continue
            m = measurable_by_donor[int(d)]
            v = values[sel]
            ok = m & (v.var(axis=0) > 0)
            live = np.flatnonzero(ok)
            for a in live:
                for b in live:
                    if a != b:
                        key = (int(a), int(b))
                        raw_strata[key] = raw_strata.get(key, 0) + 1

        edges = []
        for key, ev in evaluable.items():
            if ev <= 0 or raw_strata.get(key, 0) < self.min_evaluable_strata:
                continue
            frac = votes.get(key, 0.0) / ev
            if frac >= self.recurrence_fraction:
                edges.append((key[0], key[1], float(frac), int(raw_strata[key])))
        edges.sort(key=lambda e: (-e[2], e[0], e[1]))   # deterministic ordering
        return {
            "estimator_id": ESTIMATOR_ID,
            "top_k": self.top_k,
            "recurrence_fraction": self.recurrence_fraction,
            "min_evaluable_strata": self.min_evaluable_strata,
            "n_addresses": int(n_addr),
            "strata_used": int(strata_used),
            "edges": edges,
            "undirected_edges": sorted({(min(a, b), max(a, b)) for a, b, _, _ in edges}),
        }

    # ------------------------------------------------------------------ vectorised
    def fit_dense(
        self,
        *,
        values: np.ndarray,
        donor_codes: np.ndarray,
        measurable_by_donor: np.ndarray,
        source_by_donor: Optional[np.ndarray] = None,
    ) -> Dict[str, object]:
        """Identical semantics to fit(), accumulated in dense arrays.

        fit() is the readable reference; this is what real analysis uses. Equivalence is
        asserted by test rather than assumed.
        """
        values = np.asarray(values, dtype=np.float64)
        donor_codes = np.asarray(donor_codes)
        measurable_by_donor = np.asarray(measurable_by_donor, dtype=bool)
        n_addr = values.shape[1]
        donors = np.unique(donor_codes)

        if source_by_donor is None:
            weight_of_donor = {int(d): 1.0 for d in donors}
        else:
            source_by_donor = np.asarray(source_by_donor)
            per_source: Dict[object, int] = {}
            for d in donors:
                s = source_by_donor[int(d)]
                per_source[s] = per_source.get(s, 0) + 1
            n_sources = len(per_source)
            weight_of_donor = {
                int(d): 1.0 / (n_sources * per_source[source_by_donor[int(d)]]) for d in donors
            }

        votes = np.zeros((n_addr, n_addr), dtype=np.float64)
        evaluable = np.zeros((n_addr, n_addr), dtype=np.float64)
        raw_strata = np.zeros((n_addr, n_addr), dtype=np.int32)
        strata_used = 0

        for d in donors:
            sel = donor_codes == d
            if int(sel.sum()) < 3:
                continue
            block = values[sel]
            usable = measurable_by_donor[int(d)].copy()
            usable &= block.var(axis=0) > 0
            live = np.flatnonzero(usable)
            if live.size < 2:
                continue
            rho = _corr_from_ranks(_rankdata_columns(block[:, live]))
            np.fill_diagonal(rho, np.nan)
            mag = np.abs(rho)
            strata_used += 1
            w = weight_of_donor[int(d)]

            grid = np.ix_(live, live)
            evaluable[grid] += w
            raw_strata[grid] += 1

            k = min(self.top_k, live.size - 1)
            # deterministic: primary -|rho| (NaN last), secondary global address index
            key = np.where(np.isfinite(mag), -mag, np.inf)
            order = np.lexsort((np.tile(live, (live.size, 1)), key), axis=1)
            chosen = order[:, :k]
            finite_ct = np.isfinite(mag).sum(axis=1)
            for local in range(live.size):
                kk = int(min(k, finite_ct[local]))
                if kk <= 0:
                    continue
                votes[live[local], live[chosen[local, :kk]]] += w

        np.fill_diagonal(evaluable, 0.0)
        np.fill_diagonal(raw_strata, 0)
        np.fill_diagonal(votes, 0.0)

        with np.errstate(invalid="ignore", divide="ignore"):
            frac = np.where(evaluable > 0, votes / evaluable, 0.0)
        ok = (frac >= self.recurrence_fraction) & (raw_strata >= self.min_evaluable_strata) \
            & (evaluable > 0)
        aa, bb = np.nonzero(ok)
        edges = [(int(a), int(b), float(frac[a, b]), int(raw_strata[a, b]))
                 for a, b in zip(aa, bb)]
        edges.sort(key=lambda e: (-e[2], e[0], e[1]))
        return {
            "estimator_id": ESTIMATOR_ID,
            "top_k": self.top_k,
            "recurrence_fraction": self.recurrence_fraction,
            "min_evaluable_strata": self.min_evaluable_strata,
            "n_addresses": int(n_addr),
            "strata_used": int(strata_used),
            "edges": edges,
            "undirected_edges": sorted({(min(a, b), max(a, b)) for a, b, _, _ in edges}),
        }
