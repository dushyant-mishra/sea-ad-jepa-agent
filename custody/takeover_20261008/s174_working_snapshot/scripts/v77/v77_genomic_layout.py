#!/usr/bin/env python3
"""Genomic layout for the 41,238-address world: TSS positions and cis-regulatory regions.

WHY COORDINATES MATTER. The inherited 96-feature world tiled 256 ATAC regions uniformly
along chr1 and linked them to genes through a dense random matrix. No cis-regulatory question
was expressible there: nothing was near anything.

Here every address receives a chromosome and a TSS, and candidate regions are placed in a cis
window around those TSSs. That makes three things testable that were not before:

* distance-to-TSS is a real covariate, so a naive "nearest peak wins" baseline can be run and
  can be shown to be insufficient;
* DECOY regions can be placed NEAR a target gene while regulating nothing, which is the
  specific way accessibility-only methods generate false positives;
* a planted regulatory edge can be distal, so a method that only looks at promoters will miss
  it and that miss is measurable.

Coordinates are synthetic and are not claimed to be the real locus of the gene whose
identifier the address carries. The identity caveat from v77_address_universe applies here
too: geometry is matched, identity is not asserted.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v64"))
import build_v73_sharded_master_truth as T

S_LAYOUT = 3400

# Chromosome lengths in megabases, GRCh38 autosomes plus X, rounded. Used only to spread
# addresses realistically across a genome-sized coordinate space.
CHROM_MB = [248, 242, 198, 190, 181, 170, 159, 145, 138, 133, 135, 133,
            114, 107, 101, 90, 83, 80, 58, 64, 46, 50, 156]
CHROM_NAMES = [f"chr{i}" for i in range(1, 23)] + ["chrX"]

CIS_WINDOW_BP = 250_000          # candidate regulatory window either side of a TSS
REGIONS_PER_GENE = 1             # average; regions are shared across nearby genes
REGION_WIDTH = 500               # typical ATAC peak width


class GenomicLayout:
    """Assigns every address a TSS, and lays out ATAC regions in cis windows."""

    def __init__(self, seed: int, n_addresses: int, n_regions: int):
        self.seed = seed
        self.n_addresses = n_addresses
        self.n_regions = n_regions
        aid = np.arange(n_addresses, dtype=np.uint64)

        # --- addresses -> chromosome, proportional to chromosome length ---
        w = np.asarray(CHROM_MB, dtype=np.float64)
        w = w / w.sum()
        cuts = np.cumsum(w)
        u = T.u01(seed + S_LAYOUT, aid, S_LAYOUT)
        self.gene_chrom = np.searchsorted(cuts, u).astype(np.int16)
        self.gene_chrom = np.clip(self.gene_chrom, 0, len(CHROM_MB) - 1)

        # --- TSS position within the chromosome ---
        pos_frac = T.u01(seed + S_LAYOUT + 1, aid, S_LAYOUT + 1)
        chrom_len = np.asarray(CHROM_MB, dtype=np.float64)[self.gene_chrom] * 1_000_000
        self.gene_tss = (pos_frac * chrom_len).astype(np.int64)

        # --- regions placed in the cis window of a seeding address ---
        rid = np.arange(n_regions, dtype=np.uint64)
        seed_gene = (T.u01(seed + S_LAYOUT + 2, rid, S_LAYOUT + 2)
                     * n_addresses).astype(np.int64)
        seed_gene = np.clip(seed_gene, 0, n_addresses - 1)
        offset = ((T.u01(seed + S_LAYOUT + 3, rid, S_LAYOUT + 3) * 2 - 1)
                  * CIS_WINDOW_BP).astype(np.int64)
        self.region_chrom = self.gene_chrom[seed_gene]
        self.region_start = np.maximum(self.gene_tss[seed_gene] + offset, 0)
        self.region_end = self.region_start + REGION_WIDTH
        self.region_seed_gene = seed_gene

    # ------------------------------------------------------------------ cis lookup
    def cis_candidates(self, gene_idx: np.ndarray, window: int = CIS_WINDOW_BP):
        """Regions on the same chromosome within `window` bp of each gene's TSS.

        Returns a list of arrays, one per queried gene. This is the candidate set an
        accessibility-only method would consider; the planted graph marks which of them are
        genuinely regulatory and which are decoys.
        """
        out = []
        for g in np.atleast_1d(gene_idx):
            same = np.where(self.region_chrom == self.gene_chrom[g])[0]
            if len(same) == 0:
                out.append(same)
                continue
            d = np.abs(self.region_start[same] - self.gene_tss[g])
            out.append(same[d <= window])
        return out

    def distance_to_tss(self, region_idx, gene_idx):
        same = self.region_chrom[region_idx] == self.gene_chrom[gene_idx]
        d = np.abs(self.region_start[region_idx] - self.gene_tss[gene_idx]).astype(np.float64)
        return np.where(same, d, np.inf)

    def summary(self) -> dict:
        import collections
        return dict(
            n_addresses=int(self.n_addresses), n_regions=int(self.n_regions),
            n_chromosomes=len(CHROM_NAMES), cis_window_bp=CIS_WINDOW_BP,
            region_width_bp=REGION_WIDTH,
            addresses_per_chromosome=dict(
                collections.Counter(np.asarray(CHROM_NAMES)[self.gene_chrom].tolist())),
            regions_per_chromosome=dict(
                collections.Counter(np.asarray(CHROM_NAMES)[self.region_chrom].tolist())),
            coordinate_caveat=("coordinates are synthetic. A region near the address carrying "
                               "identifier X is NOT claimed to be near the real gene X."))
