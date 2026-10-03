#!/usr/bin/env python3
"""Fail-closed promotion gate for the empirically calibrated V73 stress twin.

This gate may authorize only the first 100K stress execution. It cannot authorize 500K,
full 4,553,407-cell execution, training, Stage-4 real correspondence, or protected TEST.
Fragment integrity is independently revalidated here; producer assertions alone cannot open
the promotion gate.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_v73_fragment_byte_linkage as FRAGV

SOURCE_AMEND=Path('results/v64/V73_SYNTHETIC_STRESS_TWIN_CONTRACT_AMENDMENT_1_SOURCE_COMPOSITION.json')
FRAG_AMEND=Path('results/v64/V73_SYNTHETIC_STRESS_TWIN_CONTRACT_AMENDMENT_2_FRAGMENT_INTEGRITY.json')
CAL_CONTRACT=Path('results/v64/V73_FULL104_EMPIRICAL_CALIBRATION_CONTRACT_V1.json')
QC_AMEND=Path('results/v64/V73_FULL104_EMPIRICAL_CALIBRATION_CONTRACT_AMENDMENT_1_SAMPLED_QC.json')
POP_AUTH=Path('results/v64/V73_FULL104_POPULATION_GEOMETRY_AUTHORITY_V1.json')
QC_AUTH=Path('results/v64/V73_FULL104_RNA_QC_CALIBRATION_AUTHORITY_50K_V1.json')
EXPECTED_SOURCES={'SEA_AD':4118213,'NPH52':236476,'HVS':198718}


def sha256_file(path:Path,chunk:int=1<<20):
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for b in iter(lambda:fh.read(chunk),b''): h.update(b)
    return h.hexdigest()


def validate(root:Path,resource_receipt:Path|None=None,calibration_authority:Path|None=None)->dict:
    truth=root/'hidden_truth/TRUTH_MANIFEST.json'
    full=root/'observable_raw/FULL104_like_sharded/FULL104_SHARDED_MANIFEST.json'
    multi=root/'observable_raw/PAIRED_MULTIOME_like_sharded/PAIRED_MULTIOME_SHARDED_MANIFEST.json'
    frag=root/'observable_raw/PAIRED_MULTIOME_fragments/SYNTHETIC_FRAGMENT_MANIFEST.json'
    required=[SOURCE_AMEND,FRAG_AMEND,CAL_CONTRACT,QC_AMEND,POP_AUTH,QC_AUTH,truth,full,multi,frag]
    missing=[str(p) for p in required if not p.exists()]
    if missing:
        return {'schema':'V73_SYNTHETIC_STRESS_PROMOTION_READINESS_V4','status':'BLOCKED','authorized_scale':'CI_ONLY','blockers':['MISSING_REQUIRED_ARTIFACTS'],'missing_required_artifacts':missing}

    sa=json.loads(SOURCE_AMEND.read_text()); fa=json.loads(FRAG_AMEND.read_text())
    cc=json.loads(CAL_CONTRACT.read_text()); qa=json.loads(QC_AMEND.read_text())
    pa=json.loads(POP_AUTH.read_text()); qca=json.loads(QC_AUTH.read_text())
    tm=json.loads(truth.read_text()); fm=json.loads(full.read_text()); mm=json.loads(multi.read_text()); gm=json.loads(frag.read_text())
    checks={}; blockers=[]
    def check(name,holds,blocker):
        checks[name]=bool(holds)
        if not holds: blockers.append(blocker)

    check('source_amendment_prospective',sa.get('status')=='PROSPECTIVE__BEFORE_100K_PROMOTION','SOURCE_COMPOSITION_AMENDMENT_INVALID')
    check('fragment_integrity_amendment_frozen',fa.get('status')=='FROZEN_BEFORE_NEXT_STRESS_PROMOTION','FRAGMENT_INTEGRITY_AMENDMENT_INVALID')
    check('calibration_contract_frozen',cc.get('status')=='FROZEN_REQUIREMENTS__AUTHORITY_EXPORT_PENDING','CALIBRATION_CONTRACT_INVALID')
    check('sampled_qc_amendment_frozen',qa.get('status')=='FROZEN_CLARIFICATION__BEFORE_100K_PROMOTION','SAMPLED_QC_AMENDMENT_INVALID')
    check('population_authority_qualified',pa.get('status')=='QUALIFIED_AGGREGATE_POPULATION_AUTHORITY' and pa.get('n_cells')==4553407 and pa.get('n_groups')==1400 and pa.get('n_donors')==104 and pa.get('n_operators')==42 and pa.get('source_counts')==EXPECTED_SOURCES and pa.get('cell_level_data_exported') is False and pa.get('real_correspondence_opened') is False,'POPULATION_AUTHORITY_INVALID')
    check('sampled_qc_authority_qualified',qca.get('status')=='QUALIFIED_SAMPLED_QC_AUTHORITY' and qca.get('sample_total_cells')==50000 and qca.get('population_total_cells')==4553407 and qca.get('qc_quantiles_are_full_population_exact') is False and qca.get('real_correspondence_opened') is False,'SAMPLED_QC_AUTHORITY_INVALID')
    check('truth_binds_population_authority',tm.get('empirical_calibration',{}).get('authority_sha256')==sha256_file(POP_AUTH),'TRUTH_NOT_BOUND_TO_POPULATION_AUTHORITY')
    check('rna_binds_qc_authority',fm.get('empirical_qc_calibration',{}).get('authority_sha256')==sha256_file(QC_AUTH),'RNA_NOT_BOUND_TO_QC_AUTHORITY')
    expected=tm.get('source_counts')
    check('source_counts_match_observers',expected is not None and fm.get('source_counts')==expected and mm.get('source_counts')==expected,'SOURCE_COUNTS_DISAGREE_ACROSS_OBSERVERS')
    donor=str(tm.get('donor_assignment_status','')); operator=str(tm.get('operator_assignment_status',''))
    check('donor_structure_qualified',donor.startswith('QUALIFIED_EMPIRICAL_'),'DONOR_STRUCTURE_NOT_QUALIFIED')
    check('operator_structure_qualified',operator.startswith('QUALIFIED_EMPIRICAL_'),'SOURCE_OPERATOR_STRUCTURE_NOT_QUALIFIED')
    check('paired_multiome_same_cell',mm.get('paired_same_cell_identity') is True,'PAIRED_MULTIOME_IDENTITY_FAILED')
    check('paired_multiome_truth_firewall',mm.get('model_facing_output_contains_hidden_truth') is False,'PAIRED_MULTIOME_TRUTH_FIREWALL_FAILED')
    check('fragment_truth_firewall',gm.get('hidden_truth_read') is False,'FRAGMENT_TRUTH_FIREWALL_FAILED')

    fragment_integrity=FRAGV.validate(root)
    check(
        'fragment_byte_linkage_qualified',
        fragment_integrity.get('qualified') is True
        and fragment_integrity.get('compressed_sha256_recomputed_from_bytes') is True
        and fragment_integrity.get('barcode_multiplicity_reconciled_to_multiome') is True,
        'FRAGMENT_BYTE_LINKAGE_NOT_QUALIFIED'
    )

    if resource_receipt and resource_receipt.exists():
        r=json.loads(resource_receipt.read_text()); measured=r.get('measured',{}); proj=r.get('calibrated_projection',{})
        check('fragment_resource_calibrated',measured.get('fragment_bytes_per_cell',0)>0 and proj.get('calibration_is_ci_scale_only') is True and proj.get('requires_100k_measurement_before_500k_promotion') is True,'FRAGMENT_RESOURCE_CALIBRATION_INCOMPLETE')
    else:
        check('fragment_resource_calibrated',False,'RESOURCE_RECEIPT_NOT_SUPPLIED')

    status='READY_FOR_100K_STRESS_ONLY' if not blockers else 'BLOCKED'
    return {
      'schema':'V73_SYNTHETIC_STRESS_PROMOTION_READINESS_V4','status':status,
      'authorized_scale':'100K_STRESS_ONLY' if not blockers else 'CI_ONLY',
      'explicitly_not_authorized':['500K_STRESS','FULL_4553407','TRAINING','STAGE4_REAL_CORRESPONDENCE','RECOVERABILITY_TEST','CONSENSUS_PEAKS_WITHOUT_FROZEN_BLACKLIST'],
      'checks':checks,'blockers':blockers,'source_counts':expected,
      'current_assignment_status':{'donor':donor,'operator':operator},
      'fragment_integrity':fragment_integrity,
      'bindings':{
        'population_authority':{'path':str(POP_AUTH),'sha256':sha256_file(POP_AUTH)},
        'sampled_qc_authority':{'path':str(QC_AUTH),'sha256':sha256_file(QC_AUTH)},
        'fragment_integrity_amendment':{'path':str(FRAG_AMEND),'sha256':sha256_file(FRAG_AMEND)},
        'truth_manifest':{'path':str(truth),'sha256':sha256_file(truth)},
        'full104_manifest':{'path':str(full),'sha256':sha256_file(full)},
        'paired_multiome_manifest':{'path':str(multi),'sha256':sha256_file(multi)},
        'fragment_manifest':{'path':str(frag),'sha256':sha256_file(frag)},
        'resource_receipt':({'path':str(resource_receipt),'sha256':sha256_file(resource_receipt)} if resource_receipt and resource_receipt.exists() else None)
      },
      'real_correspondence_opened':False,'recoverability_TEST_opened':False,'training_authorized':False
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--resource-receipt',default=None); ap.add_argument('--calibration-authority',default=None); ap.add_argument('--out',default=None); a=ap.parse_args()
    out=validate(Path(a.root),Path(a.resource_receipt) if a.resource_receipt else None,Path(a.calibration_authority) if a.calibration_authority else None)
    text=json.dumps(out,indent=2)+'\n'
    if a.out: Path(a.out).write_text(text)
    print(text,end='')
    return 0 if out['status'].startswith('READY') else 2


if __name__=='__main__': raise SystemExit(main())
