import json
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v77"))
sys.path.insert(0, str(ROOT / "scripts" / "v79"))


def test_supported_strata_preserve_summary_pair_count_and_analysis_role(tmp_path):
    import run_v79_detection_localization as D

    rng = np.random.default_rng(19)
    n, g = 800, 90
    cls = np.array(["A"] * 400 + ["B"] * 400)
    lam = np.tile(np.linspace(.2, 5.0, g), (n, 1))
    lam[cls == "A", :20] *= 2.0
    lam[cls == "B", 20:40] *= 2.0
    lam *= np.concatenate([np.linspace(.5, 1.5, 400), np.linspace(.6, 1.6, 400)])[:, None]
    counts = rng.poisson(lam).astype(float)
    counts[:, 0] = 1.0
    counts[:, 1] = 0.0
    universe = np.arange(g)
    source = np.array(["S1"] * 400 + ["S2"] * 400)
    operator = np.array(["op1"] * 200 + ["op2"] * 200 + ["op3"] * 200 + ["op4"] * 200)
    donor = np.array(["D1"] * 100 + ["D2"] * 100 + ["D3"] * 100 + ["D4"] * 100 +
                     ["D1"] * 100 + ["D2"] * 100 + ["D3"] * 100 + ["D4"] * 100)
    gate = {"status": "READY", "blockers": [], "training_authorized": False}

    rec = D.run_localization(sparse.csr_matrix(counts), universe, cls, source, operator, donor,
                             gate, n_hvg=70, output_dir=tmp_path)
    canonical_rows = [r for r in rec["canonical"]["L1"]["strata"] if r["support"]["supported"]]
    assert canonical_rows
    assert all("summary" in r for r in canonical_rows)
    assert all(r["n_pairwise_correlations"] == 70 * 69 // 2 for r in canonical_rows)
    assert all(r["canonical"] is True and r["sensitivity_only"] is False for r in canonical_rows)

    sensitivity_rows = [r for r in rec["sensitivity"]["library_depth_L2"]["strata"]
                        if r["support"]["supported"]]
    assert sensitivity_rows
    assert all("summary" in r for r in sensitivity_rows)
    assert all(r["canonical"] is False and r["sensitivity_only"] is True for r in sensitivity_rows)

    text = json.dumps(rec["canonical"]["L5"]).lower()
    for forbidden in ["gene_id", "gene_name", "edge_pairs", "selected_positions", "registry_id"]:
        assert forbidden not in text
