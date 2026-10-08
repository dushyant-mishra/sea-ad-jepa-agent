#!/usr/bin/env python3
"""Finalize and hash-freeze the read-only PROD41K T1 recovery evidence."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/prod41k_t1_contextual_recovery_v1';T1=ROOT/'exports/prod41k_teacher_t1_20260823';RUN=T1/'t1_run'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
repro=pd.read_csv(OUT/'T1_RECOVERY_ORIGINAL_REPRODUCTION.csv');dec=pd.read_csv(OUT/'T1_RECOVERY_ADDRESS_OPERATOR_DECOMPOSITION.csv',low_memory=False);bio=pd.read_csv(OUT/'T1_RECOVERY_CONTEXTUAL_BIOLOGY.csv');query=pd.read_csv(OUT/'T1_RECOVERY_QUERY_SELF_PRIVILEGE.csv',low_memory=False);reader=pd.read_csv(OUT/'T1_RECOVERY_QUERY_SELF_MOLECULAR_READER.csv')
agg=dec[dec.scope.eq('aggregate')].to_dict('records');primary=bio[(bio['update']==205)&bio.evaluation_partition.eq('reader_oracle')&bio.evidence_mode.eq('rich_H')&bio.representation.eq('operator_residual')]
selfq=query[(query.get('assay_type','block_target_predictability').eq('block_target_predictability'))&(query['update']==205)&query.evaluation_partition.eq('reader_oracle')&query.target.eq('self_context_target')].iloc[0]
selfreader=reader[(reader['update']==205)&reader.evaluation_partition.eq('reader_oracle')&reader.representation.eq('forced_query_scalar_self_ablated_operator_residual_H')].iloc[0]
payload={'schema':'prod41k-t1-contextual-recovery-final-v1','classification':'T1_CONTEXTUAL_BIOLOGY_NOT_RECOVERED','decision_route':'C','recommendation':'FRESH_CONTEXTUAL_TEACHER_ARM_LIKELY_REQUIRED','training_authorized':False,
'scope':'read-only authenticated u0/u205 recovery; no corpus-discovery input used','original_reproduction':{'comparisons':len(repro),'maximum_numeric_difference':float(repro.max_abs_numeric_difference.max()),'all_exact':bool(repro.exact_parsed_match.all())},
'address_operator_decomposition_aggregate':agg,
'primary_operator_residual_oracle':primary[['endpoint','value','u205_minus_u0','donor_bootstrap_delta_lower','donor_bootstrap_delta_upper']].to_dict('records'),
'positive_dissenting_evidence':{'self_context_target_u205_coordinate_r2':float(selfq.coordinate_r2),'u205_minus_u0_negative_normalized_mse_CI':[float(selfq.u205_minus_u0_negative_normalized_mse_lower),float(selfq.u205_minus_u0_negative_normalized_mse_upper)],'interpretation':'self-masked contextual target geometry became modestly more predictable, but this is not a biological endpoint'},
'query_self_molecular_oracle':{'r2':float(selfreader.r2),'spearman':float(selfreader.spearman)},
'answers':{'A_more_contextual_biology_than_u0':'NO_COHERENT_DONOR_HELDOUT_GAIN','B_more_source_operator_structure':'RAW_OPERATOR_DECODABILITY_TINY_INCREASE; OPERATOR_RESIDUAL_AT_CHANCE','C_raw_geometry_masked_gain':'NO_BIOLOGICAL_RESCUE_AFTER_ADDRESS_OR_OPERATOR_DECOMPOSITION','D_source_vs_operator':'OPERATOR_CORRECTION_REMOVES_MORE_NUISANCE_BUT_DOES_NOT_REVEAL_BIOLOGICAL_GAIN','E_query_self_confound':'SCALAR_SELF_PRIVILEGE_IS_STRONG; ABLATED_MOLECULAR_READER_REMAINS_BELOW_ZERO_R2','F_preserve_full_molecular_H':'YES_EXACT_ALGEBRAIC_B_PLUS_O_PLUS_C_RECOVERY','G_continue_u205':'NOT_SUPPORTED; preserve optimization-incomplete caveat'},
'trajectory':'NOT_RUN_OPTIONAL: additional checkpoint streaming would materially delay the decisive u0/u205 result','optimization_caveat':'The authenticated u205 trajectory was optimization-incomplete, so this rejects qualification of the tested checkpoint, not every longer run of every contextual objective.','representation_optimizer_updates':0,'ema_updates':0,'dev_sealed_pathology_used':False}
(OUT/'T1_CONTEXTUAL_RECOVERY_FINAL.json').write_text(json.dumps(payload,indent=2,default=str)+'\n',encoding='utf-8')
md=f'''# PROD41K T1 contextual recovery — final

Classification: **T1_CONTEXTUAL_BIOLOGY_NOT_RECOVERED**  
Decision route: **C**  
Recommendation: **FRESH_CONTEXTUAL_TEACHER_ARM_LIKELY_REQUIRED**  
Training authorized by this phase: **No**

The authenticated u0/u205 evidence reproduced exactly (maximum difference 0). Address identity explains about 99% of raw H variance. Removing fit-only address and operator components eliminated source/operator shortcuts, but did not reveal a coherent donor-held-out u205 biological gain: every primary operator-residual biology interval crossed zero. Weak/local/sparse address-residual endpoints worsened, while innovation and rare changes were uncertain; rare1 remains descriptive.

One dissenting result is retained: lawful partial prediction of the self-masked contextual target improved modestly at u205, with a donor interval of [{selfq.u205_minus_u0_negative_normalized_mse_lower:.4g}, {selfq.u205_minus_u0_negative_normalized_mse_upper:.4g}]. This is target-geometry evidence, not frozen biological qualification. Forced self-ablated operator-residual molecular reading remained below zero R² ({selfreader.r2:.4f}).

The full Molecular Ledger remains accountable: `H = B + O + C` reconstructs H deterministically within the audited floating-point bound. Raw rich-H biology is a retention control only.

The tested u205 checkpoint is therefore not salvage-qualified. The earlier optimization-incomplete status remains a caveat, but does not justify continuing u205 without a new authorization. No training, T2, DEV/SEALED access, pathology, or corpus-discovery leakage occurred.
'''
(OUT/'T1_CONTEXTUAL_RECOVERY_FINAL.md').write_text(md,encoding='utf-8')
paths=[]
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name not in {'T1_CONTEXTUAL_RECOVERY_HASH_MANIFEST.csv'} and not p.name.endswith(('_stdout.log','_stderr.log')):paths.append(p)
for p in sorted((ROOT/'scripts/v4').glob('*t1_recovery*.py')):paths.append(p)
for p in [T1/'T1_BIOLOGY_EVALUATION_FREEZE.json',T1/'T1_FREEZE_HASH_MANIFEST.csv',RUN/'checkpoint_manifest.json',ROOT/'exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv',ROOT/'exports/contextual_biology_v6r5a_20260822/program_registry.csv',ROOT/'exports/contextual_biology_v6r5a_20260822/program_weights.npz']:
 paths.append(p)
for row in json.loads((RUN/'checkpoint_manifest.json').read_text())['checkpoints']:
 if int(row['update']) in (0,205):paths.append(ROOT/row['path'])
seen=set();rows=[]
for p in paths:
 p=p.resolve()
 if p in seen or not p.exists():continue
 seen.add(p);rows.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
pd.DataFrame(rows).sort_values('path').to_csv(OUT/'T1_CONTEXTUAL_RECOVERY_HASH_MANIFEST.csv',index=False,lineterminator='\n')
print(json.dumps({'classification':payload['classification'],'manifest_rows':len(rows),'final_sha256':sha(OUT/'T1_CONTEXTUAL_RECOVERY_FINAL.json')},indent=2))
