from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pytest

from scripts.v79.unified_synthetic_integration_v1 import (
    UnifiedBiologyConfig, build_unified_biology, validate_integration_manifest,
)

MANIFEST = Path("results/v79/unified_synthetic/UNIFIED_SYNTHETIC_INTEGRATION_MANIFEST_V1.json")

def test_manifest_binds_exact_sources_and_authority_off():
    m=json.loads(MANIFEST.read_text())
    a=validate_integration_manifest(m)
    assert a.source_commits["stage81a3"] == "f5a8ebeddbcd52a94274a7f72ecda1f71b82d777"
    assert a.source_commits["v79_pr253"] == "1a0ab6e1108af924ca13e81caa3c70f3101d251c"
    assert a.source_commits["pr311"] == "2b6d3439105e087acdab53a318c57bbb468eae26"
    assert a.source_commits["pr315"] == "af03ef67d52651463944a6de3a08e101ad00e0ea"
    assert not any(a.authority.values())

def test_manifest_fails_closed_on_source_drift():
    m=json.loads(MANIFEST.read_text()); m["source_commits"]["pr311"]="0"*40
    with pytest.raises(ValueError, match="drift"):
        validate_integration_manifest(m)

def test_candidate_identifiers_are_rejected_from_config():
    with pytest.raises(ValueError, match="candidate"):
        UnifiedBiologyConfig(extra_metadata={"C2_relational": True})

def test_one_population_contains_common_and_rare_activity():
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=720,n_genes=64,n_donors=24), seed=77)
    assert w.rare_activity.sum() > 0
    assert (~w.rare_activity).sum() > 0
    assert np.all(w.rare_activity <= w.rare_eligible)
    assert len(np.unique(w.donor_id)) == 24
    assert w.expected_molecular_state.shape == (720,64)
    assert all("C1" not in name and "C2" not in name and "C3" not in name and "C4" not in name and "C5" not in name and "C6" not in name for name in w.__dataclass_fields__)
