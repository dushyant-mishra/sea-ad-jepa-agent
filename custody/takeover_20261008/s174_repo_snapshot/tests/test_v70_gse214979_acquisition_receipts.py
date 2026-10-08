import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"results/v64/V70_GSE214979_ROUTE_A_ACQUISITION_RECEIPT_V1.json"
M=ROOT/"results/v64/V70_SCENICPLUS_MOTIF_RESOURCE_RECEIPT_V1.json"

def load(p): return json.loads(p.read_text())

def test_route_a_source_bytes_and_hashes_are_frozen():
    r=load(A)
    assert r["source"]["metadata"]["bytes"]==8820297
    assert r["source"]["metadata"]["sha256"]=="8ce4e0c78747cfa6fb2a556468893df0d378e3f53085e52955f3ecdcc944394b"
    assert r["source"]["matrix"]["bytes"]==1369492123
    assert r["source"]["matrix"]["sha256"]=="8f4315b59c252c8e907dbc7cd9a46b3acfe4878b7fff7e65309027d281581bb2"

def test_matrix_shape_and_feature_types_reconcile():
    r=load(A)
    assert r["matrix"]["shape_features_by_cells"]==[187215,105332]
    assert r["matrix"]["feature_type_counts"]["Gene Expression"]==36601
    assert r["matrix"]["feature_type_counts"]["Peaks"]==150614
    assert sum(r["matrix"]["feature_type_counts"].values())==187215
    assert r["metadata"]["rows"]==105332
    assert r["metadata"]["barcode_exact_matches"]==105332

def test_microglia_population_is_exact_not_historical_approximation():
    r=load(A)
    assert r["metadata"]["celltype_column"]=="predicted.id"
    assert r["metadata"]["celltype_value"]=="Microglia"
    assert r["metadata"]["donor_column"]=="id"
    assert r["subsets"]["all_microglia"]["cells"]==3179
    assert r["subsets"]["default_development_no_possible_morabito_overlap"]["cells"]==2534

def test_prospective_overlap_exclusion_is_exact():
    r=load(A)
    assert r["subsets"]["default_development_no_possible_morabito_overlap"]["excluded_donors"]==["1224","1230","1238"]
    assert set(r["metadata"]["diagnosis_pathology_columns_present_but_not_used"])=={"Braak","Diagnosis"}

def test_subsets_are_sha_pinned_and_shapes_match_counts():
    r=load(A)
    a=r["subsets"]["all_microglia"]; d=r["subsets"]["default_development_no_possible_morabito_overlap"]
    assert a["shape"]==[187215,3179]
    assert d["shape"]==[187215,2534]
    assert len(a["npz_sha256"])==64
    assert len(d["npz_sha256"])==64

def test_fragments_are_explicitly_route_b_not_silently_missing():
    r=load(A)
    f=r["source"]["fragments"]
    assert f["downloaded_here"] is False
    assert f["route_b_owner"]=="Macha"
    assert f["geo_reported_size"]=="59.3 GB"

def test_official_motif_resource_is_sha_pinned():
    m=load(M)
    assert m["resource"]["zip_bytes"]==89706219
    assert m["resource"]["zip_sha256"]=="70dab42794f42471a3c22f5efe78ec2c8af96127656607cb0a929b4adffc2b97"
    h=m["resource"]["human_annotation"]
    assert h["bytes"]==98718421
    assert h["sha256"]=="81eb754118e27e854974301b1400fcf519489f8be5249239671fb288cb501c31"
