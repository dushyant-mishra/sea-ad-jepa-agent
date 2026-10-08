#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math


def estimate(cells: int, genes: int, peaks: int, fragments_per_cell: int = 8000,
             bytes_per_nnz: int = 8, rna_density: float = 0.08, atac_density: float = 0.04):
    if cells <= 0 or genes <= 0 or peaks <= 0:
        raise ValueError("cells, genes and peaks must be positive")
    rna_nnz = cells * genes * rna_density
    atac_nnz = cells * peaks * atac_density
    sparse_bytes = (rna_nnz + atac_nnz) * bytes_per_nnz
    axis_bytes = cells * 96 + (genes + peaks) * 96
    fragment_records = cells * fragments_per_cell
    # Deliberately conservative compressed/raw planning envelope, not an empirical claim.
    fragment_compressed_bytes = fragment_records * 11
    fragment_text_bytes = fragment_records * 35
    working_bytes = sparse_bytes * 2.5 + axis_bytes + min(fragment_text_bytes, fragment_compressed_bytes * 4)
    return {
        "schema":"V72_SYNTHETIC_RESOURCE_ESTIMATE_V1",
        "inputs":{
            "cells":cells,"genes":genes,"peaks":peaks,
            "fragments_per_cell":fragments_per_cell,
            "rna_density":rna_density,"atac_density":atac_density,
            "bytes_per_nnz":bytes_per_nnz,
        },
        "estimated":{
            "rna_nnz":int(rna_nnz),
            "atac_nnz":int(atac_nnz),
            "sparse_matrix_bytes":int(sparse_bytes),
            "fragment_records":int(fragment_records),
            "fragment_compressed_bytes_planning":int(fragment_compressed_bytes),
            "fragment_text_bytes_planning":int(fragment_text_bytes),
            "working_set_bytes_planning":int(working_bytes),
        },
        "recommended":{
            "cell_shard_size":min(100_000, max(10_000, 10_000 * math.ceil(cells / max(math.ceil(cells/100_000),1) / 10_000))),
            "stream_fragments":True,
            "materialize_dense_full_matrix":False,
            "content_address_shards":True,
            "promotion_requires_measured_stress_receipt":True,
        },
        "scope":"PLANNING_ONLY__MEASURE_ON_STRESS_TWIN_BEFORE_FULL104_SCALE",
    }


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--cells",type=int,required=True)
    ap.add_argument("--genes",type=int,default=41238)
    ap.add_argument("--peaks",type=int,default=150614)
    ap.add_argument("--fragments-per-cell",type=int,default=8000)
    ap.add_argument("--out")
    a=ap.parse_args(argv)
    r=estimate(a.cells,a.genes,a.peaks,a.fragments_per_cell)
    s=json.dumps(r,indent=2)+"\n"
    if a.out:
        open(a.out,"w").write(s)
    print(s,end="")


if __name__=="__main__":
    main()
