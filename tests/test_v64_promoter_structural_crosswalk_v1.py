from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_promoter_crosswalk_does_not_fuzzy_map_annotation_drift():
    p=json.loads((ROOT/"results/v64/V64_PROMOTER_STRUCTURAL_CROSSWALK_PREFLIGHT_V1.json").read_text())
    assert p["mapping_rule"]["fuzzy_tss_threshold_frozen"] is False
    assert "ID_PRESENT_SAME_GENE_CHROM_STRAND_SHIFTED_TSS" in p["mapping_rule"]["external_transcript_mapping_states"]
    assert p["gencode_v50"]["unique_gene_exact_tss_candidates"]==389280
    assert p["gencode_v50"]["genes_with_multiple_exact_tss_candidates"]==34598

def test_brain_atlas_is_evidence_not_denominator():
    p=json.loads((ROOT/"results/v64/V64_PROMOTER_STRUCTURAL_CROSSWALK_PREFLIGHT_V1.json").read_text())
    assert p["governance"]["promoter_selection_executed"] is False
    assert p["dong_roussos_supplementary_data_7"]["transcript_id_overlap_fraction"]>0.97
    assert p["dong_roussos_supplementary_data_7"]["exact_same_tss_fraction_among_overlapping_ids"]<0.9
