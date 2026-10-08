#!/usr/bin/env python3
"""Fail-closed promotion gate for the empirically calibrated V73/V74/V75 stress twin.

This gate may authorize only the first 100K stress execution. It cannot authorize 500K,
full 4,553,407-cell execution, training, Stage-4 real correspondence, or protected TEST.
V75 additionally requires source-feasible realised operator occupancy and an independent
fragment-byte linkage receipt; status strings alone are not deciding evidence.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

SOURCE_AMEND=Path('results/v64/V73_SYNTHETIC_STRESS_TWIN_CONTRACT_AMENDMENT_1_SOURCE_COMPOSITION.json')
CAL_CONTRACT=Path('results/v64/V73_FULL104_EMPIRICAL_CALIBRATION_CONTRACT_V1.json')
QC_AMEND=Path('results/v64/V73_FULL104_EMPIRICAL_CALIBRATION_CONTRACT_AMENDMENT_1_SAMPLED_QC.json')
POP_AUTH=Path('results/v64/V73_FULL104_POPULATION_GEOMETRY_AUTHORITY_V1.json')
QC_AUTH=Path('results/v64/V74_FULL104_RNA_QC_CALIBRATION_AUTHORITY_50K_V2.json')
EXPECTED_SOURCES={'SEA_AD':4118213,'NPH52':236476,'HVS':198718}

def sha256_file(path:Path,chunk:int=1<<20):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for b in iter(lambda:fh.read(chunk),b''):h.update(b)
    return h.hexdigest()

def _realised_operator_support_complete(tm:dict,pa:dict)->bool:
    summary=tm.get('empirical_calibration',{}).get('synthetic_population_summary',{})
    counts=summary.get('operator_counts')
    source_counts=tm.get('source_counts',{})
    op_sources=pa.get('operator_sources',[])
    if not isinstance(counts,list) or len(counts)!=pa.get('n_operators') or len(op_sources)!=len(counts):
        return False
    for source in EXPECTED_SOURCES:
        indices=[i for i,s in enumerate(op_sources) if s==source]
        if not indices:
            return False
        quota=int(source_counts.get(source,-1))
        if quota<0:
            return False
        if quota>=len(indices) and any(int(counts[i])<=0 for i in indices):
            return False
    return True

def validate(root:Path,resource_receipt:Path|None=None,calibration_authority:Path|None=None,fragment_receipt:Path|None=None)->dict:
    truth=root/'hidden_truth/TRUTH_MANIFEST.json'; full=root/'observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json'
    multi=root/'observable_raw/PAIRED_MULTIOME_like_sharded/PAIRED_MULTIOME_SHARDED_MANIFEST.json'; frag=root/'observable_raw/PAIRED_MULTIOME_fragments/SYNTHETIC_FRAGMENT_MANIFEST.json'
    required=[SOURCE_AMEND,CAL_CONTRACT,QC_AMEND,POP_AUTH,QC_AUTH,truth,full,multi,frag]
    missing=[str(p) for p in required if not p.exists()]
    if missing:return {'schema':'V75_SYNTHETIC_STRESS_PROMOTION_READINESS_V5','status':'BLOCKED','authorized_scale':'CI_ONLY','blockers':['MISSING_REQUIRED_ARTIFACTS'],'missing_required_artifacts':missing}
    sa=json.loads(SOURCE_AMEND.read_text()); cc=json.loads(CAL_CONTRACT.read_text()); qa=json.loads(QC_AMEND.read_text()); pa=json.loads(POP_AUTH.read_text()); qca=json.loads(QC_AUTH.read_text())
    tm=json.loads(truth.read_text()); fm=json.loads(full.read_text()); mm=json.loads(multi.read_text()); gm=json.loads(frag.read_text())
    checks={}; blockers=[]
    def check(name,holds,blocker):
        checks[name]=bool(holds)
        if not holds and blocker not in blockers:blockers.append(blocker)
    check('source_amendment_prospective',sa.get('status')=='PROSPECTIVE__BEFORE_100K_PROMOTION','SOURCE_COMPOSITION_AMENDMENT_INVALID')
    check('calibration_contract_frozen',cc.get('status')=='FROZEN_REQUIREMENTS__AUTHORITY_EXPORT_PENDING','CALIBRATION_CONTRACT_INVALID')
    check('sampled_qc_amendment_frozen',qa.get('status')=='FROZEN_CLARIFICATION__BEFORE_100K_PROMOTION','SAMPLED_QC_AMENDMENT_INVALID')
    check('population_authority_qualified',pa.get('status')=='QUALIFIED_AGGREGATE_POPULATION_AUTHORITY' and pa.get('n_cells')==4553407 and pa.get('n_groups')==1400 and pa.get('n_donors')==104 and pa.get('n_operators')==42 and pa.get('source_counts')==EXPECTED_SOURCES and pa.get('cell_level_data_exported') is False and pa.get('real_correspondence_opened') is False,'POPULATION_AUTHORITY_INVALID')
    check('sampled_qc_authority_qualified',qca.get('status')=='QUALIFIED_SAMPLED_QC_AUTHORITY' and qca.get('sample_total_cells')==50000 and qca.get('population_total_cells')==4553407 and qca.get('qc_quantiles_are_full_population_exact') is False and qca.get('biological_thresholds_may_be_chosen_from_these_quantiles') is False and qca.get('real_correspondence_opened') is False,'SAMPLED_QC_AUTHORITY_INVALID')
    check('truth_binds_population_authority',tm.get('empirical_calibration',{}).get('authority_sha256')==sha256_file(POP_AUTH),'TRUTH_NOT_BOUND_TO_POPULATION_AUTHORITY')
    check('rna_binds_qc_authority',fm.get('empirical_qc_calibration',{}).get('authority_sha256')==sha256_file(QC_AUTH),'RNA_NOT_BOUND_TO_QC_AUTHORITY')
    expected=tm.get('source_counts'); check('source_counts_match_observers',expected is not None and fm.get('source_counts')==expected and mm.get('source_counts')==expected,'SOURCE_COUNTS_DISAGREE_ACROSS_OBSERVERS')
    donor=str(tm.get('donor_assignment_status','')); operator=str(tm.get('operator_assignment_status',''))
    check('donor_structure_qualified',donor.startswith('QUALIFIED_EMPIRICAL_'),'DONOR_STRUCTURE_NOT_QUALIFIED')
    check('operator_structure_qualified',operator.startswith('QUALIFIED_EMPIRICAL_'),'SOURCE_OPERATOR_STRUCTURE_NOT_QUALIFIED')
    check('realised_operator_support_complete',_realised_operator_support_complete(tm,pa),'REALIZED_OPERATOR_SUPPORT_INCOMPLETE')
    check('paired_multiome_same_cell',mm.get('paired_same_cell_identity') is True,'PAIRED_MULTIOME_IDENTITY_FAILED')
    check('paired_multiome_truth_firewall',mm.get('model_facing_output_contains_hidden_truth') is False,'PAIRED_MULTIOME_TRUTH_FIREWALL_FAILED')
    check('fragment_truth_firewall',gm.get('hidden_truth_read') is False,'FRAGMENT_TRUTH_FIREWALL_FAILED')
    if fragment_receipt and fragment_receipt.exists():
        fr=json.loads(fragment_receipt.read_text())
        check('fragment_byte_linkage_qualified',fr.get('status')=='PASS' and fr.get('qualified') is True and fr.get('compressed_sha256_recomputed_from_bytes') is True and fr.get('barcode_multiplicity_reconciled_to_multiome') is True,'FRAGMENT_BYTE_LINKAGE_NOT_QUALIFIED')
    else:check('fragment_byte_linkage_qualified',False,'FRAGMENT_BYTE_LINKAGE_NOT_QUALIFIED')
    if resource_receipt and resource_receipt.exists():
        r=json.loads(resource_receipt.read_text()); measured=r.get('measured',{}); proj=r.get('calibrated_projection',{})
        check('fragment_resource_calibrated',measured.get('fragment_bytes_per_cell',0)>0 and proj.get('calibration_is_ci_scale_only') is True and proj.get('requires_100k_measurement_before_500k_promotion') is True,'FRAGMENT_RESOURCE_CALIBRATION_INCOMPLETE')
    else:check('fragment_resource_calibrated',False,'RESOURCE_RECEIPT_NOT_SUPPLIED')
    status='READY_FOR_100K_STRESS_ONLY' if not blockers else 'BLOCKED'
    return {'schema':'V75_SYNTHETIC_STRESS_PROMOTION_READINESS_V5','status':status,'authorized_scale':'100K_STRESS_ONLY' if not blockers else 'CI_ONLY',
      'explicitly_not_authorized':['500K_STRESS','FULL_4553407','TRAINING','STAGE4_REAL_CORRESPONDENCE','RECOVERABILITY_TEST'],
      'checks':checks,'blockers':blockers,'source_counts':expected,'current_assignment_status':{'donor':donor,'operator':operator},
      'bindings':{'population_authority':{'path':str(POP_AUTH),'sha256':sha256_file(POP_AUTH)},'sampled_qc_authority':{'path':str(QC_AUTH),'sha256':sha256_file(QC_AUTH)},
        'truth_manifest':{'path':str(truth),'sha256':sha256_file(truth)},'full104_manifest':{'path':str(full),'sha256':sha256_file(full)},
        'paired_multiome_manifest':{'path':str(multi),'sha256':sha256_file(multi)},'fragment_manifest':{'path':str(frag),'sha256':sha256_file(frag)},
        'fragment_linkage_receipt':({'path':str(fragment_receipt),'sha256':sha256_file(fragment_receipt)} if fragment_receipt and fragment_receipt.exists() else None),
        'resource_receipt':({'path':str(resource_receipt),'sha256':sha256_file(resource_receipt)} if resource_receipt and resource_receipt.exists() else None)},
      'real_correspondence_opened':False,'recoverability_TEST_opened':False,'training_authorized':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--resource-receipt',default=None);ap.add_argument('--fragment-receipt',default=None);ap.add_argument('--calibration-authority',default=None);ap.add_argument('--out',default=None);a=ap.parse_args()
    out=validate(Path(a.root),Path(a.resource_receipt) if a.resource_receipt else None,Path(a.calibration_authority) if a.calibration_authority else None,Path(a.fragment_receipt) if a.fragment_receipt else None); text=json.dumps(out,indent=2)+'\n'
    if a.out:Path(a.out).write_text(text)
    print(text,end='');return 0 if out['status'].startswith('READY') else 2
if __name__=='__main__':raise SystemExit(main())
