import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/validate_regulatory_program_crosswalk_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("cw",P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def program():
    m=mod()
    p=dict(program_id="P1",program_version="v1",definition_source="GSE214979_SCENICPLUS_SUBMITTED_PEAKS",
           tf_ids=["TF1"],target_gene_ids=["G1","G2"],region_ids=["chr1:10-20"],region_build="hg38",
           construction_population={"lineage":"microglia","donors":9},construction_method="SCENIC+",
           membership_sha256="",status="FROZEN_STRUCTURAL")
    p["membership_sha256"]=m.membership_sha(p); return p

def crosswalk(p,source="NIH_CARD_STAGE4"):
    return dict(program_id=p["program_id"],program_version=p["program_version"],
      program_membership_sha256=p["membership_sha256"],source_id=source,source_feature_namespace="source-v1",
      gene_support={"status":"MEASURED","n_program_genes":2,"n_measured_genes":2,"fraction_measured":1.0},
      region_support={"status":"MEASURED","n_program_regions":1,"n_measured_regions":1,"fraction_measured":1.0},
      tf_support={"status":"MEASURED","n_program_tfs":1,"n_measured_tfs":1,"fraction_measured":1.0},
      structural_eligibility="ELIGIBLE",
      missingness={"unresolved_gene_ids":[],"unresolved_region_ids":[],"unresolved_tf_ids":[],
                   "build_mismatch_unresolved":False,"structurally_unmeasured_features":[]},
      mapping_receipts={"program_namespace":"v69","region_build_mapping":None},
      limitations=[],program_region_build="hg38",region_build="hg38",biological_effect=None)

def test_valid_bundle_passes():
    p=program(); assert mod().validate_bundle({"programs":[p],"crosswalks":[crosswalk(p)]})==[]

def test_membership_change_requires_new_digest():
    p=program(); p["target_gene_ids"].append("G3")
    assert "MEMBERSHIP_SHA_MISMATCH" in mod().validate_program(p)

def test_crosswalk_binds_exact_program_membership():
    p=program(); r=crosswalk(p); r["program_membership_sha256"]="0"*64
    e=mod().validate_bundle({"programs":[p],"crosswalks":[r]})
    assert any("PROGRAM_MEMBERSHIP_BINDING_MISMATCH" in x for x in e)

def test_fraction_must_match_counts():
    p=program(); r=crosswalk(p); r["gene_support"]["fraction_measured"]=0.5
    assert any("GENE_FRACTION_MISMATCH" in x for x in mod().validate_crosswalk(r))

def test_structural_crosswalk_cannot_carry_effect():
    p=program(); r=crosswalk(p); r["biological_effect"]={"delta":1.0}
    assert "STRUCTURAL_CROSSWALK_CANNOT_CARRY_BIOLOGICAL_EFFECT" in mod().validate_crosswalk(r)

def test_build_change_needs_mapping_receipt():
    p=program(); r=crosswalk(p); r["region_build"]="hg19"; r["mapping_receipts"]["region_build_mapping"]=None
    assert "REGION_BUILD_MAPPING_RECEIPT_REQUIRED" in mod().validate_crosswalk(r)

def test_full104_sources_cannot_be_silently_pooled():
    p=program(); r=crosswalk(p,"FULL104_HVS"); r["pooled_full104_sources"]=True
    assert "FULL104_SOURCE_POOLING_FORBIDDEN" in mod().validate_crosswalk(r)

def test_duplicate_program_source_rejected():
    p=program(); r=crosswalk(p)
    e=mod().validate_bundle({"programs":[p],"crosswalks":[r,r.copy()]})
    assert any("DUPLICATE_CROSSWALK" in x for x in e)
