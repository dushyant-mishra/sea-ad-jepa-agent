#!/usr/bin/env python3
"""Profile reader-fit operator semantics and relational weighting distortion.

Reader-fit metadata only. This script never opens validation/oracle/pathology
outcomes. It exists to test whether `operator` is a semantically common axis
before allowing it to determine scientific objective mass.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

METADATA_SHA256='a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913'
BUNDLE_MEMBER='metadata/foundation_metadata_rows.sqlite'


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''): h.update(chunk)
    return h.hexdigest()


def qdict(values)->dict[str,float]:
    a=np.asarray(values,dtype=float)
    return {str(q):float(np.quantile(a,q)) for q in (0,.01,.05,.10,.25,.50,.75,.90,.95,.99,1)}


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--metadata-sqlite',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    observed=sha256(a.metadata_sqlite)
    if observed != METADATA_SHA256:
        raise SystemExit(f'metadata SHA mismatch {observed} != {METADATA_SHA256}')
    con=sqlite3.connect(a.metadata_sqlite)
    try:
        groups=pd.read_sql_query("""
          select source,donor_id,operator_index,matrix_id,count(*) cells
          from cells where partition='reader_fit'
          group by source,donor_id,operator_index,matrix_id
        """,con)
        ops=pd.read_sql_query("""
          select source,operator_index,matrix_id,count(*) cells,count(distinct donor_id) donors,
                 count(distinct native_class) native_classes,count(distinct broad_class) broad_classes
          from cells where partition='reader_fit'
          group by source,operator_index,matrix_id order by operator_index
        """,con)
        native=pd.read_sql_query("""
          select source,operator_index,native_class,count(*) cells
          from cells where partition='reader_fit'
          group by source,operator_index,native_class
        """,con)
    finally:
        con.close()
    totals=native.groupby('operator_index').cells.transform('sum')
    native['share']=native.cells/totals
    dominant=native.groupby('operator_index').share.max().rename('dominant_native_class_share')
    ops=ops.merge(dominant,on='operator_index',validate='one_to_one')

    groups['donor_cells']=groups.groupby('donor_id').cells.transform('sum')
    groups['operators_per_donor']=groups.groupby('donor_id').operator_index.transform('nunique')
    groups['share_within_donor']=groups.cells/groups.donor_cells
    donor=groups.groupby(['source','donor_id']).agg(
        cells=('cells','sum'),operators=('operator_index','nunique'),
        max_operator_share=('share_within_donor','max'),
        hhi=('share_within_donor',lambda x:float((x*x).sum())),
    ).reset_index()
    donor['effective_operators']=1.0/donor.hhi

    eligible=groups[groups.cells>=3].copy()
    eligible['eligible_cells_donor']=eligible.groupby('donor_id').cells.transform('sum')
    eligible['eligible_groups_donor']=eligible.groupby('donor_id').operator_index.transform('count')
    eligible['anchor_cell_group_mass']=eligible.cells/eligible.eligible_cells_donor
    eligible['equal_group_mass']=1.0/eligible.eligible_groups_donor
    eligible['equal_group_over_anchor_mass']=eligible.equal_group_mass/eligible.anchor_cell_group_mass

    donor_total=groups.groupby(['source','donor_id']).cells.sum().rename('total').reset_index()
    donor_elig=eligible.groupby(['source','donor_id']).cells.sum().rename('eligible').reset_index()
    de=donor_total.merge(donor_elig,on=['source','donor_id'],how='left').fillna({'eligible':0})
    de['eligible_fraction']=de.eligible/de.total

    source_profiles={}
    for src,og in ops.groupby('source',sort=True):
        dg=donor[donor.source==src]
        eg=eligible[eligible.source==src]
        de_src=de[de.source==src]
        source_profiles[src]={
            'operators':int(len(og)),
            'operator_matrix_ids':og.matrix_id.tolist(),
            'operator_native_class_counts':qdict(og.native_classes),
            'operator_dominant_native_class_share':qdict(og.dominant_native_class_share),
            'donor_operator_count':qdict(dg.operators),
            'donor_max_operator_cell_share':qdict(dg.max_operator_share),
            'donor_effective_operator_count':qdict(dg.effective_operators),
            'eligible_relational_groups':int(len(eg)),
            'eligible_anchor_cell_fraction_per_donor':qdict(de_src.eligible_fraction),
            'equal_group_over_anchor_mass_ratio':qdict(eg.equal_group_over_anchor_mass),
        }

    payload={
        'schema':'READER_FIT_OPERATOR_SEMANTICS_PROFILE_V1',
        'population':'reader_fit',
        'authority_input':{'bundle_member':BUNDLE_MEMBER,'sha256':observed},
        'cells':int(groups.cells.sum()),
        'donors':int(groups.donor_id.nunique()),
        'operators':int(groups.operator_index.nunique()),
        'donor_operator_groups':int(len(groups)),
        'eligible_groups_n_ge_3':int(len(eligible)),
        'eligible_cells_n_ge_3':int(eligible.cells.sum()),
        'eligible_cell_fraction':float(eligible.cells.sum()/groups.cells.sum()),
        'per_donor_eligible_cell_fraction':qdict(de.eligible_fraction),
        'source_profiles':source_profiles,
        'cross_source_operator_semantics':{
            'HVS':'operators are each native-class-pure in reader_fit, but matrix_id labels are opaque identifiers',
            'NPH52':'operators are each native-class-pure and matrix_id names explicitly encode Astro/Endo/ExN/InN/MG/OPC/Oligo partitions',
            'SEA_AD':'operators are multi-native-class matrices; each contains 17-26 native classes in reader_fit',
            'common_scientific_axis_established':False,
        },
        'relational_weighting_diagnostic':{
            'old_equal_operator_group_target':'1 / eligible_operator_groups_within_donor',
            'data_first_anchor_cell_target':'group cells / eligible cells within donor; then uniform anchored relation inside group',
            'equal_group_over_anchor_mass_ratio':qdict(eligible.equal_group_over_anchor_mass),
            'max_equal_group_upweight_vs_anchor':float(eligible.equal_group_over_anchor_mass.max()),
            'interpretation':'Equal operator-group mass can upweight a tiny operator group by >100x relative to its eligible-cell prevalence, and operator meaning is not common across sources. Operator is therefore safe as a same-support/comparison boundary, not as an automatically equal scientific-mass axis.',
        },
        'decision_implications':[
            'Keep base JEPA donor-uniform and cell-uniform within donor; operator is not a cross-source scientific averaging axis.',
            'For production relational target, use operator only as an admissibility boundary: select eligible anchor cells uniformly within donor and comparator pairs within the anchor operator.',
            'Keep TD57B/TD59/TD60 qualification semantics byte-for-byte/exactly frozen; this profile changes no historical gate.',
            'Operator/group balancing may be used in a proposal for coverage only when exact target/proposal correction preserves the scientific target.',
        ],
        'training_authorized':False,
        'execution_authorized':False,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(a.out),'sha256':sha256(a.out),'terminal':'PASS_READER_FIT_OPERATOR_SEMANTICS_PROFILE_V1'},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
