#!/usr/bin/env python3
"""Exact metadata anomalies and absent-combination tables for the fit-104 atlas."""
from pathlib import Path
import json,sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'exports/foundation_corpus_discovery_v1'; con=sqlite3.connect(OUT/'foundation_metadata_rows.sqlite')
def q(s): return pd.read_sql_query(s,con)
def main():
 dup_id=q("select source,cell_id,count(*) occurrences,count(distinct matrix_id) matrices from cells where partition='reader_fit' group by source,cell_id having count(*)>1")
 dup_key=q("select stable_key,count(*) occurrences from cells where partition='reader_fit' group by stable_key having count(*)>1")
 cross=q("select donor_id,count(distinct source) sources,group_concat(distinct source) source_list from cells where partition='reader_fit' group by donor_id having count(distinct source)>1")
 matrix=q("select matrix_id,count(distinct source) sources,group_concat(distinct source) source_list from cells where partition='reader_fit' group by matrix_id having count(distinct source)>1")
 donors=q("select distinct donor_id from cells where partition='reader_fit'"); ops=q("select distinct matrix_id from cells where partition='reader_fit'"); native=q("select distinct source,native_class from cells where partition='reader_fit' and native_class<>''")
 observed=set(map(tuple,q("select distinct donor_id,matrix_id from cells where partition='reader_fit'").to_numpy())); absent_do=pd.DataFrame([(d,o) for d in donors.donor_id for o in ops.matrix_id if (d,o) not in observed],columns=['donor_id','matrix_id'])
 obs_dn=set(map(tuple,q("select distinct donor_id,source,native_class from cells where partition='reader_fit' and native_class<>''").to_numpy())); absent_dn=pd.DataFrame([(d,s,n) for d in donors.donor_id for s,n in native.itertuples(index=False) if (d,s,n) not in obs_dn],columns=['donor_id','source','native_class'])
 frames={'FOUNDATION_DUPLICATED_CELL_IDS.csv':dup_id,'FOUNDATION_DUPLICATED_STABLE_KEYS.csv':dup_key,'FOUNDATION_DONORS_ACROSS_SOURCES.csv':cross,'FOUNDATION_SOURCE_MATRIX_INCONSISTENCIES.csv':matrix,'FOUNDATION_ABSENT_DONOR_OPERATOR_COMBINATIONS.csv':absent_do,'FOUNDATION_ABSENT_DONOR_NATIVE_CLASS_COMBINATIONS.csv':absent_dn}
 for name,f in frames.items(): f.to_csv(OUT/name,index=False,lineterminator='\n')
 old=int(q("select sum(in_original_t1) n from cells where partition='reader_fit'").n.iloc[0]); fit=int(q("select count(*) n from cells where partition='reader_fit'").n.iloc[0])
 if fit!=4_553_407 or old!=3_292: raise RuntimeError(f'exact inventory/cache mismatch fit={fit} old={old}')
 report={'fit104_cells':fit,'original_t1_exact_matches':old,'duplicated_source_scoped_cell_ids':len(dup_id),'duplicated_stable_keys':len(dup_key),'donors_unexpected_across_sources':len(cross),'source_matrix_inconsistencies':len(matrix),'absent_donor_operator_combinations':len(absent_do),'absent_donor_native_class_combinations':len(absent_dn)}
 (OUT/'FOUNDATION_METADATA_ANOMALY_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__':main()
