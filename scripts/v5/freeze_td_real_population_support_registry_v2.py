"""Freeze the outcome-blind real TD population/support registry V2.

Inputs are metadata-only custody assets. No expression values or candidate outcomes
are read. The frozen population is separated from candidate-evidence readiness:
foundation candidate support stays blocked until exact evidence-rights/address/query
support contracts are frozen, while C5 is structurally unsupported in this RNA-only
population pending a separate regulatory/chromatin evidence registry.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path

CANDIDATES=(
    'C1_SHARED_EMERGENT','C2_RELATIONAL_SHARED','C3_QUERY_MEASURED',
    'C6_SHARED_QUERY_COMPOSITE','C4_STRUCTURED_COMPOSITE','C5_REGULATORY_SPECIALIST'
)
FOUNDATION=CANDIDATES[:-1]
SPECIALIST='C5_REGULATORY_SPECIALIST'
PARTITIONS={'reader_fit','reader_validation','reader_oracle'}
PRODUCTION_DB_SHA256='a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913'
PRODUCTION_SPLIT_SHA256='efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511'
PRODUCTION_EXPECTED={
    'rows':6351753,'donors':149,'operators':42,'sources':3,'donor_operator_pairs':2028,
    'partition_donors':{'reader_fit':104,'reader_validation':22,'reader_oracle':23},
}

class RegistryFreezeError(ValueError):
    pass

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def _read_split(path: Path) -> dict[str,str]:
    out={}
    with Path(path).open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f)
        if r.fieldnames != ['donor_id','reader_partition']:
            raise RegistryFreezeError('split schema mismatch')
        for row in r:
            d,p=row['donor_id'],row['reader_partition']
            if not d or p not in PARTITIONS:
                raise RegistryFreezeError('invalid donor/partition in split')
            if d in out:
                raise RegistryFreezeError(f'duplicate donor in split: {d}')
            out[d]=p
    if not out: raise RegistryFreezeError('empty split')
    return out

def _pair_rows(db_path: Path):
    con=sqlite3.connect(str(db_path))
    try:
        return con.execute('''
          select source,matrix_id,donor_id,partition,count(*) as cell_count
          from cells
          group by source,matrix_id,donor_id,partition
          order by source,matrix_id,donor_id,partition
        ''').fetchall()
    finally:
        con.close()

def build_registry(db_path: Path, split_path: Path) -> dict:
    split=_read_split(split_path)
    pairs=_pair_rows(db_path)
    db_donors={r[2] for r in pairs}
    if db_donors != set(split):
        raise RegistryFreezeError('donor roster mismatch between metadata database and split')
    donor_parts={}
    strata=[]
    support={c:'BLOCKED_EVIDENCE_CONTRACT' for c in FOUNDATION}; support[SPECIALIST]='UNSUPPORTED_STRUCTURAL'
    for source,matrix,donor,partition,cell_count in pairs:
        if partition not in PARTITIONS:
            raise RegistryFreezeError(f'invalid database partition: {partition}')
        if split[donor] != partition:
            raise RegistryFreezeError(f'partition mismatch for donor {donor}: db={partition} split={split[donor]}')
        prior=donor_parts.setdefault(donor,partition)
        if prior != partition:
            raise RegistryFreezeError(f'donor appears in multiple database partitions: {donor}')
        identity={'donor_id':donor,'source':source,'operator_matrix':matrix,'reader_partition':partition}
        sid='STRATUM::'+hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        strata.append({
            'stratum_id':sid,'donor_id':donor,'source':source,'operator_matrix':matrix,
            'study_family':source,'technology':'snRNA-seq','reader_partition':partition,
            'candidate_support_state':dict(support),
        })
    claims={c:['DONOR','SOURCE','OPERATOR_MATRIX','STUDY_FAMILY','TECHNOLOGY'] for c in CANDIDATES}
    return {
      'schema':'JEPA_TD_REAL_STATIC_POPULATION_SUPPORT_REGISTRY_V2',
      'frozen':True,
      'candidate_transfer_claims':claims,
      'strata':strata,
    }

def production_audit(db_path: Path, split_path: Path, registry: dict) -> dict:
    db_sha, split_sha=sha256_file(db_path),sha256_file(split_path)
    if db_sha != PRODUCTION_DB_SHA256: raise RegistryFreezeError('production metadata database SHA mismatch')
    if split_sha != PRODUCTION_SPLIT_SHA256: raise RegistryFreezeError('production split SHA mismatch')
    con=sqlite3.connect(str(db_path))
    try:
        rows,donors,operators,sources=con.execute('select count(*),count(distinct donor_id),count(distinct matrix_id),count(distinct source) from cells').fetchone()
        pairs=con.execute('select count(*) from (select distinct donor_id,matrix_id from cells)').fetchone()[0]
        part=dict(con.execute('select partition,count(distinct donor_id) from cells group by partition').fetchall())
    finally: con.close()
    observed={'rows':rows,'donors':donors,'operators':operators,'sources':sources,'donor_operator_pairs':pairs,'partition_donors':part}
    if observed != PRODUCTION_EXPECTED: raise RegistryFreezeError(f'production population counts mismatch: {observed}')
    if len(registry['strata']) != PRODUCTION_EXPECTED['donor_operator_pairs']:
        raise RegistryFreezeError('registry stratum count mismatch')
    payload=json.dumps(registry,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return {
      'schema':'JEPA_TD_REAL_POPULATION_SUPPORT_REGISTRY_FREEZE_RECEIPT_V2',
      'status':'OUTCOME_BLIND_POPULATION_SUPPORT_REGISTRY_FROZEN__NO_BIOLOGICAL_AUTHORITY',
      'metadata_database_sha256':db_sha,'reader_split_sha256':split_sha,
      'observed_population':observed,'canonical_registry_payload_sha256':hashlib.sha256(payload).hexdigest(),
      'foundation_support_rule':'POPULATION_STRATA_FROZEN__FOUNDATION_CANDIDATE_SUPPORT_BLOCKED_UNTIL_EXACT_EVIDENCE_RIGHTS_AND_ADDRESS_QUERY_SUPPORT_ARE_FROZEN',
      'specialist_support_rule':'C5_UNSUPPORTED_STRUCTURAL_IN_FOUNDATION_RNA_REGISTRY_PENDING_SEPARATE_FROZEN_REGULATORY_CHROMATIN_EVIDENCE_REGISTRY',
      'technology_rule':'ALL_CURRENT_FOUNDATION_STRATA_SN_RNA_SEQ__TECHNOLOGY_TRANSFER_BLOCKED_DEPENDENCY',
      'authority':{'value_read_authorized':False,'real_tournament_authorized':False,'target_selection_authorized':False,'representation_selection_authorized':False,'td60_authorized':False,'stage4_authorized':False,'training_authorized':False},
    }
