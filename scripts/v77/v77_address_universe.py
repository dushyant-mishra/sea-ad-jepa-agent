#!/usr/bin/env python3
"""The canonical 41,238-address universe, with background realism derived FROM THE REGISTRY.

The point of this module is that the background is not invented. Every structural property
below is read out of the frozen foundation molecular address registry:

* `biotype` (54 classes, 45.8% protein_coding, 15.0% lincRNA, 11.9% antisense, ...) drives
  the abundance prior and the detectability prior. A lincRNA is not a protein-coding gene
  and must not be drawn from the same distribution.
* `contributing_source_feature_count` (41.9% at 9, 24.1% at 8, 14.2% at 1) is a real
  measurement-breadth signal and drives gene-specific detectability.
* `contributing_source_families` says WHICH COHORT actually measured each address. 42.6% of
  addresses are in all three families, 31.8% in NPH52|SEA-AD only, 11.5% in SEA-AD only,
  11.3% in NPH52 only. Structural unmeasurement therefore becomes a real, source-dependent
  fact instead of a per-operator hash.

IDENTITY BOUNDARY. Using the registry's ORDER and identifiers makes the synthetic world
tokenizer-compatible: address index k is the same vocabulary slot the production encoder
indexes. It does NOT assert that the synthetic biology planted at address k is the real
biology of that gene. Modules are allocated by a seeded permutation with no biological
knowledge of the symbols, so a synthetic program landing on APOE says nothing about APOE.
Any downstream artifact must carry that caveat.

This is NOT the blocked 96-feature-to-canonical-address mapping: nothing from the 96-feature
world is projected onto these slots.
"""
from __future__ import annotations
import csv, hashlib, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v64"))
import build_v73_sharded_master_truth as T

N_ADDRESSES = 41238
REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
# Row order of AddressUniverse.source_support. This is NOT World A's SOURCE_ORDER, which is
# ('SEA_AD', 'NPH52', 'HVS') and is the order truth shards use for source_index. A comment here
# once claimed the two matched. They never did, and indexing source_support with a truth
# source_index silently swapped HVS and SEA-AD coverage in every canonical V2 world (defect
# S146). Map by NAME with family_rows_for_source_names(); never index by position.
SOURCE_FAMILIES = ("HVS", "NPH52", "SEA_AD")


def family_rows_for_source_names(source_names) -> np.ndarray:
    """Row of source_support for each truth source_index, matched by NAME, never by position."""
    names = [str(s).replace("SEA-AD", "SEA_AD") for s in source_names]
    unknown = sorted(set(names) - set(SOURCE_FAMILIES))
    if unknown:
        raise ValueError(f"truth source names with no registry family: {unknown}")
    return np.array([SOURCE_FAMILIES.index(s) for s in names], dtype=np.int64)

# Abundance and detectability priors by biotype family. These are the one genuinely external
# choice in this module: they encode that ribosomal/mitochondrial transcripts dominate counts,
# protein-coding genes are mid-abundance, and non-coding classes are low and poorly detected.
# They are stated here rather than tuned against any outcome.
_BT = {
    "very_high": (dict(mu=+2.6, sd=1.0, det=+2.2), ("rRNA", "Mt_rRNA", "Mt_tRNA")),
    "coding":    (dict(mu=+0.0, sd=1.6, det=+0.6), ("protein_coding",)),
    "lnc":       (dict(mu=-1.8, sd=1.3, det=-0.8), ("lincRNA", "antisense", "sense_intronic",
                                                    "sense_overlapping", "processed_transcript",
                                                    "3prime_overlapping_ncRNA", "non_coding",
                                                    "bidirectional_promoter_lncRNA", "TEC")),
    "small":     (dict(mu=-2.2, sd=1.5, det=-1.4), ("snRNA", "snoRNA", "miRNA", "misc_RNA",
                                                    "scaRNA", "scRNA", "vaultRNA", "ribozyme")),
    "pseudo":    (dict(mu=-2.5, sd=1.2, det=-1.8), ("unprocessed_pseudogene", "processed_pseudogene",
                                                    "transcribed_unprocessed_pseudogene",
                                                    "transcribed_processed_pseudogene",
                                                    "transcribed_unitary_pseudogene",
                                                    "unitary_pseudogene", "polymorphic_pseudogene",
                                                    "IG_V_pseudogene", "TR_V_pseudogene")),
    "immune":    (dict(mu=-1.5, sd=1.4, det=-0.6), ("IG_V_gene", "IG_C_gene", "TR_V_gene",
                                                    "TR_C_gene", "TR_J_gene", "LRG_gene")),
    "unknown":   (dict(mu=-1.5, sd=1.5, det=-0.5), ("",)),
}
_BT_LOOKUP = {name: fam for fam, (_, names) in _BT.items() for name in names}


def _family_of(biotype: str) -> str:
    if biotype in _BT_LOOKUP:
        return _BT_LOOKUP[biotype]
    first = biotype.split("|")[0] if biotype else ""
    return _BT_LOOKUP.get(first, "unknown")


def find_registry(start: Path | None = None) -> Path:
    """Locate the frozen registry and verify its digest."""
    cands = []
    here = (start or Path(__file__).resolve()).parents
    for p in list(here)[:6]:
        cands.append(p / "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv")
    cands.append(Path("D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv"))
    for c in cands:
        if c.exists():
            h = hashlib.sha256()
            with open(c, "rb") as fh:
                for b in iter(lambda: fh.read(1 << 20), b""):
                    h.update(b)
            if h.hexdigest() != REGISTRY_SHA256:
                raise RuntimeError(f"registry digest mismatch at {c}: {h.hexdigest()}")
            return c
    raise FileNotFoundError("foundation molecular address registry not found")


class AddressUniverse:
    """The 41,238-address vocabulary plus its registry-derived background structure."""

    def __init__(self, seed: int, registry: Path | None = None):
        path = registry or find_registry()
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        if len(rows) != N_ADDRESSES:
            raise RuntimeError(f"expected {N_ADDRESSES} addresses, found {len(rows)}")
        self.registry_path = str(path)
        self.registry_sha256 = REGISTRY_SHA256
        self.seed = seed
        self.address_id = np.array([r["molecular_address_id"] for r in rows])
        self.symbol = np.array([r["symbol"] for r in rows])
        self.biotype = np.array([r["biotype"] for r in rows])
        self.bt_family = np.array([_family_of(b) for b in self.biotype])
        self.feature_count = np.array(
            [int(r["contributing_source_feature_count"] or 0) for r in rows], dtype=np.int32)

        # --- source-family support: a REAL fact, not a hash -------------------------------
        fam = [set((r["contributing_source_families"] or "").replace("SEA-AD", "SEA_AD").split("|"))
               for r in rows]
        self.source_support = np.zeros((len(SOURCE_FAMILIES), N_ADDRESSES), dtype=bool)
        for si, s in enumerate(SOURCE_FAMILIES):
            self.source_support[si] = np.array([s in f for f in fam])

        aid = np.arange(N_ADDRESSES, dtype=np.uint64)

        # --- abundance prior: heavy-tailed, biotype-conditional --------------------------
        mu = np.array([_BT[f][0]["mu"] for f in self.bt_family])
        sd = np.array([_BT[f][0]["sd"] for f in self.bt_family])
        self.log_abundance = (mu + sd * T.normal(seed + 7700, aid, 7700)).astype(np.float32)

        # --- detectability prior: biotype + measurement breadth --------------------------
        dbt = np.array([_BT[f][0]["det"] for f in self.bt_family])
        breadth = np.clip(self.feature_count, 1, 9) / 9.0
        self.logit_detect = (dbt + 1.6 * (breadth - 0.5)
                             + 0.7 * T.normal(seed + 7800, aid, 7800)).astype(np.float32)

    # -------------------------------------------------------------- background programs
    def background_programs(self, n_programs: int = 60, genes_per: int = 600):
        """Sparse correlated background factors over the whole address space.

        These are the 'thousands of correlated substitutes' a model can exploit instead of
        learning biological state. They are deliberately NOT planted biology: they carry no
        truth label and exist so that broad covariance is not a free win.
        """
        rows, cols, vals = [], [], []
        for p in range(n_programs):
            s = T.u01(self.seed + 7900 + p, np.arange(N_ADDRESSES, dtype=np.uint64), 7900 + p)
            sel = np.argsort(s, kind="stable")[:genes_per]
            w = T.normal(self.seed + 7950 + p, sel.astype(np.uint64), 7950 + p)
            rows.append(np.full(len(sel), p)); cols.append(sel); vals.append(w)
        return (np.concatenate(rows), np.concatenate(cols),
                np.concatenate(vals).astype(np.float32), n_programs)

    # -------------------------------------------------------------- module allocation
    def module_allocator(self, seed_offset: int = 9100):
        return _Allocator(self, seed_offset)

    def summary(self) -> dict:
        import collections
        return dict(
            registry_path=self.registry_path, registry_sha256=self.registry_sha256,
            n_addresses=N_ADDRESSES,
            biotype_family_counts=dict(collections.Counter(self.bt_family.tolist())),
            source_support_fraction={s: float(self.source_support[i].mean())
                                     for i, s in enumerate(SOURCE_FAMILIES)},
            addresses_supported_by_all_sources=int(self.source_support.all(axis=0).sum()),
            addresses_supported_by_one_source=int((self.source_support.sum(axis=0) == 1).sum()),
            log_abundance_quantiles=[float(x) for x in
                                     np.quantile(self.log_abundance, [.01, .25, .5, .75, .99])],
            identity_boundary=("registry order and identifiers are used so the vocabulary matches "
                               "the production tokenizer. Planted biology is allocated by seeded "
                               "permutation with no knowledge of symbols, so synthetic signal at a "
                               "real gene identity asserts nothing about that gene."))


class _Allocator:
    """Allocates module address sets with CONTROLLED overlap.

    Strict disjointness was an over-correction: real pathways share genes, and partial
    redundancy is exactly what lets a model substitute one gene for another. Modules are
    therefore grouped into FAMILIES, and members of a family overlap by a declared fraction
    while different families stay disjoint.
    """

    def __init__(self, uni: AddressUniverse, seed_offset: int):
        self.uni = uni
        order = np.argsort(T.u01(uni.seed + seed_offset,
                                 np.arange(N_ADDRESSES, dtype=np.uint64), seed_offset),
                           kind="stable")
        self._pool = order
        self._cursor = 0
        self.assigned: dict[str, list[int]] = {}
        self.families: dict[str, list[str]] = {}

    def take(self, name: str, k: int) -> np.ndarray:
        if name in self.assigned:
            return np.asarray(self.assigned[name])
        if self._cursor + k > len(self._pool):
            raise RuntimeError("address allocator exhausted")
        sel = np.sort(self._pool[self._cursor:self._cursor + k])
        self._cursor += k
        self.assigned[name] = sel.tolist()
        return sel

    def take_redundant(self, family: str, name: str, k: int, overlap: float,
                       parent: str | None = None) -> np.ndarray:
        """A module that shares `overlap` of its addresses with its family parent."""
        if name in self.assigned:
            # the observer re-enters per shard; the address set is deterministic, but without
            # this guard the family membership list is appended once per shard and the member
            # counts are reported as n_shards times too large
            return np.asarray(self.assigned[name])
        if parent is None or parent not in self.assigned:
            sel = self.take(name, k)
            self.families.setdefault(family, []).append(name)
            return sel
        pa = np.asarray(self.assigned[parent])
        n_shared = int(round(overlap * k))
        n_shared = min(n_shared, len(pa))
        s = T.u01(self.uni.seed + 9300, pa.astype(np.uint64), 9300)
        shared = pa[np.argsort(s, kind="stable")[:n_shared]]
        fresh = self.take(name + "__private", k - n_shared)
        sel = np.sort(np.concatenate([shared, fresh]))
        self.assigned[name] = sel.tolist()
        self.families.setdefault(family, []).append(name)
        return sel

    @property
    def used(self) -> int:
        return self._cursor
