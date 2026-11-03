"""Macha independent replication of #526's aggregate counts (does not import #526's diagnostic).

Rebuilds the exact PR328 world/fit from its frozen seeds, checks both receipt hashes, then counts
with independent code. Emits aggregates only: no counts, donors, latents or controller truth.
"""
import json
import sys
from pathlib import Path

import numpy as np

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from scripts.v79.unified_synthetic_integration_v1 import UnifiedBiologyConfig, build_unified_biology  # noqa: E402
from scripts.v79.unified_synthetic_fit_view_v1 import UnifiedObservationConfig, fit_view_sha256, observe_unified_world  # noqa: E402
from scripts.v79.v79_rare_biology_generator_v1 import VISIBILITY  # noqa: E402

receipt = json.loads((root / "results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_RECEIPT_V2.json").read_text(encoding="utf-8"))
world = build_unified_biology(UnifiedBiologyConfig(), seed=20261013)
fit = observe_unified_world(world, UnifiedObservationConfig(), seed=20261014)
out = {"numpy": np.__version__,
       "world_sha_matches_receipt": world.world_hash == receipt["world_sha256"],
       "fit_sha_matches_receipt": fit_view_sha256(fit) == receipt["fit_view_sha256"]}

values, support, source = np.asarray(fit.values), np.asarray(fit.support, dtype=bool), np.asarray(fit.source)
out["n_cells"], out["n_genes"] = int(values.shape[0]), int(values.shape[1])
q, panel = 0, list(range(1, 9))
per = {}
for s in ("HVS", "NPH52", "SEA_AD"):
    rows = source == s
    sup = support[rows]
    cols_supported = sup.all(axis=0)                     # support is a per-source structural mask
    full = sup[:, [q] + panel].all(axis=1)
    denom = values[rows][:, panel].astype(np.int64).sum(axis=1)
    per[s] = {
        "cells": int(rows.sum()),
        "support_is_constant_within_source": bool((sup == sup[0]).all()),
        "panel_genes_structurally_unmeasured": [g for g in [q] + panel if not cols_supported[g]],
        "full_panel_supported_cells": int(full.sum()),
        "estimable_cells_positive_denominator": int((full & (denom > 0)).sum()),
        "fraction_of_all_genes_structurally_measured": round(float(cols_supported.mean()), 4),
        "visibility_detection_fraction_at_panel": [float(VISIBILITY[s][g % 15]) for g in [q] + panel],
    }
out["per_source"] = per
common = support[source == "HVS"].all(axis=0) & support[source == "NPH52"].all(axis=0) & support[source == "SEA_AD"].all(axis=0)
out["genes_measured_in_all_three_sources"] = int(common.sum())
out["support_rule_in_fit_view"] = "support = VISIBILITY > 0 tiled by position (unified_synthetic_fit_view_v1.py:78-81)"
print(json.dumps(out, indent=1))
