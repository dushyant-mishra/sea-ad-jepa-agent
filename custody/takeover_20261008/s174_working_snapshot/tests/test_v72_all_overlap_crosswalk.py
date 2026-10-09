import csv
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/v72_all_overlap_crosswalk.py"

def load():
    s=importlib.util.spec_from_file_location("v72_overlap",SCRIPT)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def write(path,rows):
    with open(path,"w",newline="") as fh:
        w=csv.writer(fh); w.writerow(["chrom","start","end","id"]); w.writerows(rows)

def test_all_overlaps_keeps_more_than_first_hit(tmp_path):
    q=tmp_path/"q.csv"; t=tmp_path/"t.csv"; out=tmp_path/"x.csv"
    write(q,[["chr1",100,200,"Q1"]])
    write(t,[["chr1",90,150,"T1"],["chr1",140,210,"T2"],["chr1",300,400,"T3"]])
    r=load().write_crosswalk(q,t,out)
    rows=list(csv.DictReader(open(out)))
    assert {(x["query_id"],x["target_id"]) for x in rows}=={("Q1","T1"),("Q1","T2")}
    assert r["queries_with_multiple_targets"]==1
    assert r["max_targets_per_query"]==2

def test_touching_boundaries_are_not_overlap(tmp_path):
    q=tmp_path/"q.csv"; t=tmp_path/"t.csv"; out=tmp_path/"x.csv"
    write(q,[["chr1",100,200,"Q1"]])
    write(t,[["chr1",200,250,"T1"]])
    r=load().write_crosswalk(q,t,out)
    assert r["overlap_pairs"]==0

def test_overlap_fractions_are_explicit(tmp_path):
    q=tmp_path/"q.csv"; t=tmp_path/"t.csv"; out=tmp_path/"x.csv"
    write(q,[["chr1",100,200,"Q1"]])
    write(t,[["chr1",150,250,"T1"]])
    load().write_crosswalk(q,t,out)
    row=list(csv.DictReader(open(out)))[0]
    assert float(row["overlap_bp"])==50
    assert float(row["query_fraction"])==0.5
    assert float(row["target_fraction"])==0.5
