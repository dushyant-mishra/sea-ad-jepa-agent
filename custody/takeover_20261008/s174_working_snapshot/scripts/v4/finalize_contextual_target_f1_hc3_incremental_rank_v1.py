#!/usr/bin/env python3
"""Finalize the fail-closed Command-15A3 reproduction gate."""
from __future__ import annotations
import argparse,csv,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--staging',type=Path,required=True);a=ap.parse_args();o=a.staging.resolve()
 review="""# F1 HC3 incremental-rank diagnostic — governance review

Historian verdict: **CONTRADICTS_CLOSED_DECISION**.

Both hash-verified prior packages record the mandatory base at rank 7: one intercept, two independent source contrasts, and four continuous nuisance dimensions. Independent reconstruction gives the same seven constructed columns, rank 7, df 97, and HC3 estimability. Command 15A3 instead requires exact reproduction of mandatory-base rank 8 and explicitly mandates a reproduction STOP on mismatch.

Following the JEPA preflight's Historian-first rule, the five downstream specialist reviews were not launched after this verdict. No incremental rank authority, SVD prefix, frontier, or design was evaluated or selected.

The likely provenance correction is prospective: mandatory base rank 7; the historical 8->8 refers to mandatory base plus NPH52 component 1, followed by attempted component 2. That correction was not silently made here.
""";(o/'F1_HC3_INCREMENTAL_MULTIAGENT.md').write_text(review,encoding='utf-8')
 handoff="""# F1 HC3 Command 15A3 — external-review handoff

Terminal: `STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH`.

All hashes and the old rank-18/df-86 HC3 failure reproduce. However, the mandatory base is rank 7 in both prior authoritative packages and in two current implementations. Command 15A3 requires reproducing rank 8, so its own Section-1 mismatch gate stops execution before augmented-rank analysis.

The discrepancy is semantic/provenance, not an engineering failure: rank 7 is intercept + two independent source contrasts + four continuous nuisances. The earlier 8->8 trace is the design after adding NPH52 component 1, then testing component 2.

No frontier, candidate authority, rank triple, integration change, expression, model, checkpoint, outcome, training, or EMA work was performed. A corrected prospective command must explicitly require mandatory-base rank 7 before this diagnostic can resume.
""";(o/'F1_HC3_INCREMENTAL_EXTERNAL_REVIEW_HANDOFF.md').write_text(handoff,encoding='utf-8')
 snap=o/'source_snapshot';snap.mkdir(exist_ok=True);names=['audit_contextual_target_f1_hc3_incremental_rank_v1.py','validate_contextual_target_f1_hc3_incremental_rank_v1.py','finalize_contextual_target_f1_hc3_incremental_rank_v1.py'];sr=[]
 for n in names:
  p=ROOT/'scripts/v4'/n;q=snap/n;shutil.copy2(p,q);sr.append({'source_path':str(p.relative_to(ROOT)).replace('\\','/'),'snapshot_path':str(q.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(p),'snapshot_sha256':sha(q),'byte_identical':sha(p)==sha(q)})
 with (o/'F1_HC3_INCREMENTAL_SOURCE_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(sr[0]));w.writeheader();w.writerows(sr)
 rows=[]
 for p in sorted(x for x in o.rglob('*') if x.is_file() and x.name!='F1_HC3_INCREMENTAL_MANIFEST.csv'):rows.append({'relative_path':str(p.relative_to(o)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)})
 with (o/'F1_HC3_INCREMENTAL_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['relative_path','bytes','sha256']);w.writeheader();w.writerows(rows)
 print({'terminal':'STOP_F1_HC3_INCREMENTAL_RANK_REPRODUCTION_MISMATCH','manifest_sha256':sha(o/'F1_HC3_INCREMENTAL_MANIFEST.csv'),'manifested_files':len(rows)})
if __name__=='__main__':main()
