import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/build_regulatory_program_coverage_tensor_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("t",P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def support(n,m):
    return {"status":"MEASURED" if m==n else "PARTIAL","n_program_genes":n,"n_measured_genes":m,"fraction_measured":m/n if n else None}

def rec(source,frac=1.0,eligible="ELIGIBLE"):
    n=10; m=int(round(n*frac))
    return dict(program_id="P1",program_version="v1",source_id=source,
      structural_eligibility=eligible,
      gene_support={"status":"MEASURED" if m==n else "PARTIAL","n_program_genes":n,"n_measured_genes":m,"fraction_measured":m/n},
      region_support={"status":"NOT_APPLICABLE","n_program_regions":0,"n_measured_regions":0,"fraction_measured":None},
      tf_support={"status":"MEASURED","n_program_tfs":1,"n_measured_tfs":1,"fraction_measured":1.0},
      limitations=[])

def program():
    return dict(program_id="P1",program_version="v1",membership_sha256="a"*64,definition_source="GSE214979_SCENICPLUS_SUBMITTED_PEAKS")

def test_tensor_keeps_full104_sources_separate():
    b={"programs":[program()],"crosswalks":[rec("FULL104_HVS",0.6),rec("FULL104_NPH52",0.8),rec("FULL104_SEA_AD",1.0)]}
    row=mod().build_tensor(b)["rows"][0]
    assert row["full104_transport_ceiling"]["HVS"]==0.6
    assert row["full104_transport_ceiling"]["NPH52"]==0.8
    assert row["full104_transport_ceiling"]["SEA_AD"]==1.0
    assert row["full104_transport_ceiling"]["all_three_source_families_minimum"]==0.6

def test_tensor_does_not_invent_missing_source_record():
    b={"programs":[program()],"crosswalks":[]}
    t=mod().build_tensor(b)
    assert t["rows"][0]["sources"]["NIH_CARD_STAGE4"]["status"]=="NO_RECORD"

def test_direct_multimodal_label_is_structural_only():
    b={"programs":[program()],"crosswalks":[rec("NIH_CARD_STAGE4"),rec("MORABITO_GSE174367")]}
    t=mod().build_tensor(b)
    row=t["rows"][0]
    assert set(row["direct_multimodal_sources"])=={"NIH_CARD_STAGE4","MORABITO_GSE174367"}
    assert "no biological result implied" in t["semantics"]["direct_multimodal_sources"]

def test_partial_source_not_promoted_to_direct_eligible():
    b={"programs":[program()],"crosswalks":[rec("SEAAD_PUBLIC_MULTIOME",0.5,"PARTIALLY_ELIGIBLE")]}
    row=mod().build_tensor(b)["rows"][0]
    assert "SEAAD_PUBLIC_MULTIOME" not in row["direct_multimodal_sources"]
    assert "SEAAD_PUBLIC_MULTIOME" in row["structurally_eligible_sources"]

def test_transport_ceiling_not_called_recoverability():
    t=mod().build_tensor({"programs":[program()],"crosswalks":[]})
    assert "actual RNA recoverability may be lower" in t["semantics"]["full104_transport_ceiling"]
