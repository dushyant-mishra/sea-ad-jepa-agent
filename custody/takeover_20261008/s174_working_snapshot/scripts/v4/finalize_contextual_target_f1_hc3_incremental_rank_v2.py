#!/usr/bin/env python3
"""Finalize corrected Command-15A3 as a fail-closed reviewed package."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--staging',type=Path,required=True);a=ap.parse_args();o=a.staging.resolve()
 amendment="""# Command 15A3 authority correction

Classification: `COMMAND_15A3_AUTHORITY_TYPO / PREFIX-STATE-CONFLATION`.

Prospectively corrected sequence authorized by the user before this rerun:

- mandatory base B: rank 7, df 97;
- B + NPH52 C1: rank 7 -> 8, df 96;
- B + NPH52 C1 + C2: rank 8 -> 8, df 96.

The original hard-coded “mandatory base rank 8” moved the post-C1 rank backward onto B. Only that wording is corrected. The incremental-rank mathematics, frozen HC3 engine, inputs, nuisance primitives, donors, and no-selection boundary are unchanged. The prior STOP package remains historical provenance.
""";(o/'F1_HC3_INCREMENTAL_AUTHORITY_AMENDMENT.md').write_text(amendment,encoding='utf-8')
 review="""# F1 HC3 corrected incremental-rank diagnostic — targeted review

Synthesis: **DO_NOT_RUN_INVALID** for inferential promotion. The corrected diagnostic arithmetic is accepted; the candidate frontier hits a structural HC3 STOP.

1. **Historian / Statistical Authority — REVISIT_JUSTIFIED; STOP.** The explicit amendment resolves the typo. Base rank 7 and the 7->8->8 NPH sequence reproduce. The first NPH prefix is HC3-nonestimable.
2. **Numerical Linear Algebra — PASS diagnostic; STOP downstream.** Raw/full-design increments are HVS/NPH52/SEA-AD 6/1/4, joint 11, unchanged by equilibration. Score-versus-unit scaling agrees. NPH component 2 is locally nonzero but full-design redundant.
3. **HC3 / Regression Geometry — STOP.** Candidate `(0,1,0)` is full rank 8/8 with df 96, but `NPH52::human_NPH_906` has unit leverage and LOO rank loss one; HC3 is undefined for every outcome.
4. **Operator / Dataset Semantics — PASS diagnostic; STOP downstream.** All 104 donors and complete 24/7/11 source operator blocks remain present; no donor/operator deletion or forbidden access occurred.
5. **Decision-Engine Compatibility — PASS for the STOP.** The frozen rank and leverage gates are unchanged and independently reproduce the same first-invalid prefix.
6. **Scientific Red-Team — CONCERN.** Arithmetic/STOP withstand attack. It requested stronger authority/input/firewall binding, supplied in the final validator, source snapshot, amendment artifact, and manifest. No complete frontier or arbitrary-basis claim is made after the first frozen gate failure.

Coordinator note: synthesis phrased unit leverage as “no residual degrees of freedom.” Precisely, global df is 96; the offending donor has zero residual leverage (`1-h=0` geometrically), making HC3 undefined.

No rank triple or repaired nuisance design is selected or frozen.
""";(o/'F1_HC3_INCREMENTAL_MULTIAGENT.md').write_text(review,encoding='utf-8')
 handoff="""# Corrected F1 HC3 Command 15A3 — external-review handoff

Terminal: `STOP_F1_HC3_INCREMENTAL_FRONTIER_HC3_NONESTIMABLE`.

The authority typo is resolved and hash-bound: mandatory base rank 7/df 97; NPH C1 changes 7->8; C2 leaves 8->8. Incremental operator ranks are HVS 6, NPH52 1, SEA-AD 4, joint 11. Equilibration gives the same ranks. NPH component 2 is correctly classified `LOCAL_NUMERICAL_DIRECTION__REDUNDANT_IN_ACTUAL_HC3_DESIGN`.

The first NPH-bearing frontier point `(0,1,0)` is full rank 8/8 with df 96 but recreates unit leverage at `NPH52::human_NPH_906`; donor deletion lowers rank by one. It therefore fails the unchanged frozen HC3 boundary. The frontier stops after six fixed-order rows and is not complete or selectable.

No design/rank triple/estimator is selected or frozen. No expression, model, checkpoint, outcome, training, or EMA was accessed. A later prospective authority must repair the donor-isolating HC3 geometry before F1 execution.
""";(o/'F1_HC3_INCREMENTAL_EXTERNAL_REVIEW_HANDOFF.md').write_text(handoff,encoding='utf-8')
 snap=o/'source_snapshot';snap.mkdir(exist_ok=True);names=['derive_contextual_target_f1_hc3_incremental_rank_v2.py','validate_contextual_target_f1_hc3_incremental_rank_v2.py','finalize_contextual_target_f1_hc3_incremental_rank_v2.py'];sr=[]
 for n in names:
  p=ROOT/'scripts/v4'/n;q=snap/n;shutil.copy2(p,q);sr.append({'source_path':str(p.relative_to(ROOT)).replace('\\','/'),'snapshot_path':str(q.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(p),'snapshot_sha256':sha(q),'byte_identical':sha(p)==sha(q)})
 with (o/'F1_HC3_INCREMENTAL_SOURCE_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(sr[0]));w.writeheader();w.writerows(sr)
 rows=[]
 for p in sorted(x for x in o.rglob('*') if x.is_file() and x.name!='F1_HC3_INCREMENTAL_MANIFEST.csv'):rows.append({'relative_path':str(p.relative_to(o)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)})
 with (o/'F1_HC3_INCREMENTAL_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['relative_path','bytes','sha256']);w.writeheader();w.writerows(rows)
 print(json.dumps({'terminal':'STOP_F1_HC3_INCREMENTAL_FRONTIER_HC3_NONESTIMABLE','manifest_sha256':sha(o/'F1_HC3_INCREMENTAL_MANIFEST.csv'),'manifested_files':len(rows)}))
if __name__=='__main__':main()
