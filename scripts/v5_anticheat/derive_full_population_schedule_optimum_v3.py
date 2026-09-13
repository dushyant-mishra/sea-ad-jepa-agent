#!/usr/bin/env python3
"""Derive the lexicographically optimal V5 full-reader presentation schedule.

Authority comes only from the authenticated reader-fit metadata plus explicit
prospective constraints. No pathology, checkpoint outcome, or synthetic data is
read. The output contains donor-level multiplicity counts, not a training grant.
"""
from __future__ import annotations
import argparse, hashlib, heapq, json, math, sqlite3
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

from sea_ad_jepa.v5.full104_metadata_authority_v1 import (
    EXPECTED_METADATA_SQLITE_SHA256,
    validate_requested_metadata_authority,
)


def file_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()


def exact_product(counts, donor_n):
    D=len(donor_n); H=0; A=Fraction()
    for d,cnt in counts.items():
        n=donor_n[d]
        for m,c in cnt.items():
            if c: H+=m*c; A+=Fraction(c,D*D*n*n*m)
    return H,A,Fraction(H)*A


def main(argv=None, *, _expected_metadata_sha256_for_test: str | None = None):
    p=argparse.ArgumentParser()
    p.add_argument('--expected-metadata-sha256',required=True)
    p.add_argument('--partition',required=True)
    p.add_argument('--metadata-sqlite',type=Path,required=True)
    p.add_argument('--out-json',type=Path,required=True)
    p.add_argument('--expected-cells',type=int,required=True)
    p.add_argument('--expected-donors',type=int,required=True)
    p.add_argument('--expected-groups',type=int,required=True)
    p.add_argument('--group-floor',type=int,required=True)
    p.add_argument('--cell-cap',type=int,required=True)
    p.add_argument('--ess-floor-numerator',type=int,required=True)
    p.add_argument('--ess-floor-denominator',type=int,required=True)
    a=p.parse_args(argv)
    try:
        expected_metadata_sha256 = validate_requested_metadata_authority(
            a.expected_metadata_sha256,
            _expected_metadata_sha256_for_test=_expected_metadata_sha256_for_test,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    ints=(a.expected_cells,a.expected_donors,a.expected_groups,a.group_floor,a.cell_cap,a.ess_floor_numerator,a.ess_floor_denominator)
    if min(ints)<1: raise SystemExit('all integer authorities must be positive')
    ess_floor=Fraction(a.ess_floor_numerator,a.ess_floor_denominator)
    if ess_floor>1: raise SystemExit('ESS floor cannot exceed 1')
    observed=file_sha256(a.metadata_sqlite)
    if observed.lower()!=expected_metadata_sha256: raise SystemExit(f'metadata SHA mismatch: {observed}')

    con=sqlite3.connect(f'file:{a.metadata_sqlite}?mode=ro',uri=True); c=con.cursor()
    rows=c.execute('select donor_id,operator_index,source,count(*) from cells where partition=? group by donor_id,operator_index,source',(a.partition,)).fetchall()
    total=int(c.execute('select count(*) from cells where partition=?',(a.partition,)).fetchone()[0])
    unique=int(c.execute('select count(distinct stable_key) from cells where partition=?',(a.partition,)).fetchone()[0]); con.close()
    if total!=unique or total!=a.expected_cells: raise SystemExit('population/stable-key count mismatch')
    if len(rows)!=a.expected_groups: raise SystemExit('donor-operator group count mismatch')

    donor_n=Counter(); donor_sources=defaultdict(set); groups=defaultdict(list)
    for d,o,s,n in rows:
        d=str(d); s=str(s); n=int(n); donor_n[d]+=n; donor_sources[d].add(s); groups[d].append((int(o),s,n))
    if len(donor_n)!=a.expected_donors: raise SystemExit('donor count mismatch')
    if any(len(x)!=1 for x in donor_sources.values()): raise SystemExit('donor spans sources')

    nmin,nmax=min(donor_n.values()),max(donor_n.values())
    min_nm=nmin*a.cell_cap; max_nm=nmax; ratio=Fraction(max_nm,min_nm)
    bounds={}; counts={}; initial_group=[]; topup=0
    for d,n in sorted(donor_n.items()):
        L=max(1,math.ceil(min_nm/n)); U=min(a.cell_cap,max_nm//n)
        if L>U: raise SystemExit(f'ratio optimum infeasible for donor {d}')
        bounds[d]=(L,U); cnt=Counter()
        for op,source,g in groups[d]:
            extra=max(0,a.group_floor-g*L); q,r=divmod(extra,g); m0=L+q; m1=m0+1
            if m0>U or (r and m1>U): raise SystemExit(f'group floor incompatible with ratio optimum {d}/{op}')
            cnt[m0]+=g-r
            if r: cnt[m1]+=r
            initial_group.append((g-r)*m0+r*m1); topup+=extra
        if sum(cnt.values())!=n: raise RuntimeError('donor cell-count mismatch')
        counts[d]=cnt

    H0,A0,P0=exact_product(counts,donor_n); D=len(donor_n); heap=[]; live=set()
    def priority(d,m): return donor_n[d]*donor_n[d]*m*(m+1)
    def push(d,m):
        if m<bounds[d][1] and counts[d].get(m,0)>0 and (d,m) not in live:
            heapq.heappush(heap,(priority(d,m),d,m)); live.add((d,m))
    for d,cnt in counts.items():
        for m,cnt_m in cnt.items():
            if cnt_m: push(d,m)
    H=H0; Af=float(A0); target=float(Fraction(1,1)/ess_floor); steps=0; last=None
    while H*Af>target+1e-13:
        den,d,m=heapq.heappop(heap); live.discard((d,m))
        if counts[d].get(m,0)<=0 or m>=bounds[d][1]: continue
        counts[d][m]-=1; counts[d][m+1]+=1; H+=1; Af-=1.0/(D*D*den); steps+=1; last=(d,m); push(d,m); push(d,m+1)
    H,A,P=exact_product(counts,donor_n); threshold=Fraction(1,1)/ess_floor
    while P>threshold:
        den,d,m=heapq.heappop(heap); live.discard((d,m))
        if counts[d].get(m,0)<=0 or m>=bounds[d][1]: continue
        counts[d][m]-=1; counts[d][m+1]+=1; steps+=1; last=(d,m); push(d,m); push(d,m+1); H,A,P=exact_product(counts,donor_n)
    if last is None: raise RuntimeError('expected at least one ESS-balancing increment')
    d,m=last; counts[d][m+1]-=1; counts[d][m]+=1; Hp,Ap,Pp=exact_product(counts,donor_n); counts[d][m]-=1; counts[d][m+1]+=1; H,A,P=exact_product(counts,donor_n)
    if P>threshold or Pp<=threshold or H!=Hp+1: raise RuntimeError('minimum-H boundary proof failed')

    hist=Counter(); source_present=Counter(); lo=10**30; hi=0
    for d,cnt in counts.items():
        n=donor_n[d]; source=next(iter(donor_sources[d])); dt=0
        for m,cnt_m in cnt.items():
            if cnt_m: hist[m]+=cnt_m; dt+=m*cnt_m; lo=min(lo,n*m); hi=max(hi,n*m)
        source_present[source]+=dt
    if Fraction(hi,lo)!=ratio or min(initial_group)<a.group_floor: raise RuntimeError('final ratio/group invariant failed')
    st=a.metadata_sqlite.stat()
    out={
      'schema':'JEPA_V5_FULL_POPULATION_LEXICOGRAPHIC_OPTIMUM_V3','status':'REAL_READER_FIT_DATASET_GEOMETRY_OPTIMUM__NO_TRAINING_AUTHORITY',
      'metadata_sqlite_sha256':observed,'partition':a.partition,'metadata_file_receipt':{'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'inode':st.st_ino,'device':st.st_dev},
      'population_cells':total,'unique_stable_keys':unique,'donors':len(donor_n),'groups':len(rows),
      'constraints':{'full_unique_cell_coverage':True,'minimum_group_presentations':a.group_floor,'maximum_presentations_per_cell':a.cell_cap,'minimum_importance_ess_fraction':{'numerator':ess_floor.numerator,'denominator':ess_floor.denominator,'float':float(ess_floor)},'scientific_target':'DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1'},
      'lexicographic_objective':['MINIMIZE_IMPORTANCE_WEIGHT_MAX_TO_MIN_RATIO','THEN_MINIMIZE_TOTAL_PRESENTATIONS_SUBJECT_TO_ESS_GROUP_FLOOR_COVERAGE_AND_CAP'],
      'weight_ratio_optimum':{'smallest_donor_cells':nmin,'largest_donor_cells':nmax,'minimum_cell_product_n_times_m':min_nm,'maximum_cell_product_n_times_m':max_nm,'exact_numerator':ratio.numerator,'exact_denominator':ratio.denominator,'float':float(ratio)},
      'initial_minimum_presentation_ratio_optimal_schedule':{'presentations':H0,'extra_vs_population':H0-total,'group_topup_presentations':topup,'ess_fraction':float(Fraction(1,1)/P0)},
      'final_optimum':{'total_presentations':H,'extra_presentations':H-total,'population_equivalents':H/total,'importance_ess_fraction':float(Fraction(1,1)/P),'importance_weight_max_to_min_ratio':float(ratio),'max_cell_multiplicity':max(hist),'minimum_group_presentations':min(initial_group),'greedy_unit_increments_after_ratio_optimal_minimum':steps,'previous_total_presentations':Hp,'previous_schedule_importance_ess_fraction':float(Fraction(1,1)/Pp),'previous_schedule_passed_ess_floor':False,'source_presentations':dict(sorted(source_present.items())),'source_presentation_fraction':{s:source_present[s]/H for s in sorted(source_present)},'cell_multiplicity_histogram':{str(k):v for k,v in sorted(hist.items())},'donor_multiplicity_counts':{d:{str(k):v for k,v in sorted(counts[d].items()) if v} for d in sorted(counts)},'donor_ratio_bounds':{d:{'min_multiplicity':bounds[d][0],'max_multiplicity':bounds[d][1],'donor_cells':donor_n[d]} for d in sorted(donor_n)}},
      'pathology_used':False,'checkpoint_outcomes_used':False,'synthetic_data_used_for_authority':False,'training_authorized':False}
    a.out_json.parent.mkdir(parents=True,exist_ok=True); a.out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
