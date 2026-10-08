#!/usr/bin/env python3
"""Finalize the Command-15A diagnostic as a fail-closed review package."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--staging",type=Path,required=True);a=ap.parse_args();o=a.staging.resolve()
 md="""# F1 HC3 Command-15A targeted review

Terminal synthesis: **DO_NOT_RUN_INVALID**. Four lenses passed the outcome-blind root-cause diagnosis, but Numerical Linear Algebra and Scientific Red-Team independently issued STOP. Dissent is preserved below.

## 1. Historian / Statistical Authority — PASS

- Command 15A is novel and authorized strictly as a diagnostic; all frozen inputs and the no-selection boundary are bound.
- The rank-18/df-86 failure and two unit-leverage donors reproduce exactly.
- Falsification: using this package to select or freeze a repair would violate authority.

## 2. HC3 / Regression Geometry — PASS

- The old failure is geometric unit leverage and the first lexicographic boundary crossing occurs at `operator_mix_001`.
- Mandatory source plus continuous base is estimable; raw operator families are not.
- Falsification: exact estimability alone cannot qualify any diagnostic prefix.

## 3. Operator / Observation Semantics — PASS

- The 42x41,238 uint8 state authority and nine exact row-equivalence classes reproduce.
- Source operator blocks and the two multicolumn donor-isolation patterns reproduce.
- Exact physical-state equality is diagnostic only and does not imply scientific interchangeability.

## 4. Survey Sampling / Donor Geometry — PASS

- All 104 donors and the 41/17/46 source split are preserved; no donor deletion occurs.
- Operator isolation is multivariate, not a donor-unique raw operator.
- k/n, leverage, 2k/n and 3k/n remain descriptive, not selection rules.

## 5. Numerical Linear Algebra — STOP

- NPH52 residual rank 2 is projection-roundoff: `rank([W,O])-rank(W)=1`, whereas re-ranking the tiny residual under its rescaled tolerance yields 2.
- Every `r_NPH52=2` candidate has more constructed columns than numerical rank; normal-equation hat values and condition summaries are therefore not reliable for those rows.
- The independent validator repeats the vulnerable residual-rank and normal-equation arithmetic instead of independently falsifying it.

## 6. Scientific Red-Team — STOP

- The frontier omits the frozen engine's `rank == X.shape[1]` gate, so 35/105 nominal rows can be labeled estimable when the engine would reject them.
- Actual ill-conditioned same-span Gram-inverse reparameterization changes leverage enough to alter boundary classification; the well-conditioned synthetic basis test cannot certify the actual arithmetic.
- Falsification succeeded: the current frontier is not safe for repair selection.

## Synthesis

`DO_NOT_RUN_INVALID`. Preserve the valid old-failure/root-cause evidence, but do not use the source-prefix frontier to choose or freeze a design. A later prospective command must define numerically stable residual-rank and hat/estimability arithmetic before a repaired diagnostic is attempted.
"""
 (o/"F1_HC3_MULTIAGENT.md").write_text(md,encoding="utf-8")
 terminal={"terminal_status":"STOP_F1_HC3_SVD_NUMERICAL_NONREPRODUCIBLE","synthesis":"DO_NOT_RUN_INVALID","old_failure_reproduced":True,"valid_root_cause_label":"ROOT_CAUSE_RAW_OPERATOR_MIXTURE_DONOR_ISOLATION","frontier_promotable":False,"design_frozen":False,"production_integration_patched":False,"expression_or_candidate_outcomes_accessed":False,"model_or_checkpoint_accessed":False,"training_or_ema":False,"blocking_findings":{"nph52_augmented_space_residual_rank":1,"reported_residual_rank":2,"affected_frontier_rows":35,"frozen_engine_full_column_rank_gate_omitted_from_frontier":True,"actual_ill_conditioned_basis_arithmetic_not_certified":True}}
 (o/"F1_HC3_TERMINAL_STATUS.json").write_text(json.dumps(terminal,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 handoff="""# F1 HC3 geometry diagnostic — external-review handoff

Terminal: `STOP_F1_HC3_SVD_NUMERICAL_NONREPRODUCIBLE`.

The historical rank-18/df-86 HC3 failure, the two unit-leverage donors, the mandatory-base estimability, the raw-column order dependence, and the donor-isolating operator-mixture root cause were reproduced outcome-blind.

The diagnostic frontier is **not promotable**. Review found that NPH52's nominal second residual component is projection roundoff: augmented-space rank increment is one, while residual rescaling reports two. This makes 35 of 105 frontier rows constructed-rank-deficient, contrary to the frozen engine's full-column-rank gate. The validator reproduced rather than falsified that defect. Actual ill-conditioned Gram-inverse leverage is also not basis-stable enough for the claimed certification.

No design/rank/operator subset/estimator is selected or frozen. No expression, model, checkpoint, candidate outcome, training, or EMA was accessed. Do not resume F1 evaluation from this package. A separate prospective instruction is required to define stable residual-rank and leverage arithmetic.
"""
 (o/"F1_HC3_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff,encoding="utf-8")
 snap=o/"source_snapshot";snap.mkdir(exist_ok=True)
 source_names=["derive_contextual_target_f1_hc3_geometry_diagnostic_v1.py","validate_contextual_target_f1_hc3_geometry_diagnostic_v1.py","finalize_contextual_target_f1_hc3_geometry_diagnostic_v1.py"]
 source_rows=[]
 for n in source_names:
  src=ROOT/"scripts/v4"/n;dst=snap/n;shutil.copy2(src,dst);source_rows.append({"source_path":str(src.relative_to(ROOT)).replace('\\','/'),"snapshot_path":str(dst.relative_to(ROOT)).replace('\\','/'),"source_sha256":sha(src),"snapshot_sha256":sha(dst),"byte_identical":sha(src)==sha(dst)})
 with (o/"F1_HC3_SOURCE_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(source_rows[0]));w.writeheader();w.writerows(source_rows)
 # Manifest is generated last from actual bytes and intentionally excludes itself.
 rows=[]
 for p in sorted(x for x in o.rglob("*") if x.is_file() and x.name!="F1_HC3_MANIFEST.csv"):
  rows.append({"relative_path":str(p.relative_to(o)).replace('\\','/'),"bytes":p.stat().st_size,"sha256":sha(p)})
 with (o/"F1_HC3_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=["relative_path","bytes","sha256"]);w.writeheader();w.writerows(rows)
 print(json.dumps({"terminal_status":terminal["terminal_status"],"manifest_sha256":sha(o/"F1_HC3_MANIFEST.csv"),"files_manifested":len(rows)}))

if __name__=="__main__":main()
