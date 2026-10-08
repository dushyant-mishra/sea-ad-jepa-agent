import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/validate_multisource_regulatory_evidence_stack_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("v69",P)
    m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m

def base(source="NIH_CARD_STAGE4", cls="PRIMARY_CORRESPONDENCE", kind="DIRECT_MEASUREMENT"):
    return dict(
      program_id="P1",source_id=source,evidence_class=cls,
      population={"unit":"donor","n_units":10,"lineage":"microglia","region":None},
      feature_support={"genes_measured":10,"regions_measured":20,"support_fraction":1.0,"missing_reason":None},
      direct_measurement={"rna":True,"atac":True,"perturbation":False,"spatial":False},
      independence_axes={"unit":"donor","assay":"RNA_ATAC","cohort_lab":"source_specific","feature_definition":"frozen","technical_environment":"source_specific","causal_direction":"observational","tissue_context":"nuclei","outcome_exposure":"UNOPENED"},
      exposure_state="UNOPENED",effect_summary={"delta":0.1},uncertainty_summary={"lcb":0.01},
      limitations=[],measured_vs_predicted=kind
    )

def test_valid_direct_record_passes():
    assert mod().validate_stack([base()])==[]

def test_non_nihcard_cannot_define_primary_stage4():
    r=base("MORABITO_GSE174367","SEPARATE_NUCLEUS_REPLICATION")
    r["may_define_primary_stage4_pass"]=True
    e=mod().validate_stack([r])
    assert any("NON_NIHCARD_SOURCE_CANNOT_DEFINE_PRIMARY_STAGE4" in x for x in e)

def test_cross_source_pooling_forbidden():
    r=base(); r["pooled_with_other_sources"]=True
    assert any("CROSS_SOURCE_POOLING_FORBIDDEN" in x for x in mod().validate_stack([r]))

def test_predicted_cannot_masquerade_as_direct():
    r=base(kind="RNA_PREDICTED")
    e=mod().validate_stack([r])
    assert any("PREDICTED_CANNOT_MASQUERADE_AS_DIRECT" in x for x in e)
    assert any("RNA_PREDICTED_REQUIRES_RECOVERABILITY_QUALIFICATION" in x for x in e)

def test_structural_only_cannot_carry_effect():
    r=base("MORABITO_CROSSWALK","SEPARATE_NUCLEUS_REPLICATION","STRUCTURAL_ONLY")
    r["effect_summary"]={"delta":999}
    assert any("STRUCTURAL_ONLY_CANNOT_CARRY_BIOLOGICAL_EFFECT" in x for x in mod().validate_stack([r]))

def test_duplicate_program_source_rejected():
    a=base(); b=base()
    assert any("DUPLICATE_PROGRAM_SOURCE" in x for x in mod().validate_stack([a,b]))

def test_population_unit_required():
    r=base(); r["population"]={}
    assert any("POPULATION_UNIT_REQUIRED" in x for x in mod().validate_stack([r]))
