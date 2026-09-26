"""Fail-closed verification of committed V44 descriptive scores/limits only.

No historical raw RNA, full current V5 learner or biological fidelity is run in CI.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CSV=ROOT/"tournament_scores_v1.csv"
STATE=ROOT/"tournament_machine_state_v1.json"
ARMS=("R_SINGLE_RICH_V5_LINEAR_PROXY","A_SINGLE_COMPLEMENTARY","B_SHARED_TRUNK_THREE_HEADS","C_INDEPENDENT_CORE_FINE_RARE","D_INDEPENDENT_WITH_TAIL_SPECIALIST")
METRICS=("independent_Y_donor_equal_R2","independent_Y_rare_subgroup_R2","student_teacher_latent_R2")
EXPECTED_MEAN={"R_SINGLE_RICH_V5_LINEAR_PROXY":(0.4158819,0.443839,0.7125625),"A_SINGLE_COMPLEMENTARY":(0.4026731,0.4315778,0.2415312),"B_SHARED_TRUNK_THREE_HEADS":(0.4078233,0.4326608,0.7676336),"C_INDEPENDENT_CORE_FINE_RARE":(0.4018643,0.4220601,0.648729),"D_INDEPENDENT_WITH_TAIL_SPECIALIST":(0.4004149,0.4160421,0.5958158)}
CSV_SHA="43edc51516ad63bebbba48eb5f98d8c5271f993e7ed4fa6a2a6c716fb518ae26"

def validate(raw:str,state:dict)->None:
    def demand(ok,why):
        if not ok:raise ValueError(why)
    demand(hashlib.sha256(raw.encode()).hexdigest()==CSV_SHA,"committed original score bytes have changed")
    rows=list(csv.DictReader(raw.splitlines()))
    demand(len(rows)==15,"must have fifteen actually recorded rows")
    demand(set((int(r["seed"]),r["arm"]) for r in rows)=={(seed,arm) for seed in (7,11,17) for arm in ARMS},"missing/duplicate/wrong original arm or split")
    demand(all(int(r["holdout_donors"])==20 for r in rows),"not original heldout donor split")
    for seed,tr,te in ((7,2257,343),(11,2125,475),(17,2029,571)):
        demand(all(int(r["train_cells"])==tr and int(r["test_cells"])==te for r in rows if int(r["seed"])==seed),"train/test cell mismatch")
    for arm,expect in EXPECTED_MEAN.items():
        arm_rows=[r for r in rows if r["arm"]==arm]
        for col,mean in zip(METRICS,expect):
            observed=sum(float(r[col]) for r in arm_rows)/3
            demand(abs(observed-mean)<6e-7,"original arm mean changed "+arm+":"+col)
    demand(state.get("scope")=="HISTORICAL_2600_CELL_PCA_RIDGE_CPU_SURROGATES_NOT_ACTUAL_V5_IPB_OR_EMA","surrogate falsely promoted")
    auth=state.get("authority",{})
    for flag in ("training_authorized","actual_current_v5_ipb_executed","ema_teacher_trained","protected_outcomes_opened","audit_b_n1_opened","architecture_selected"):
        demand(auth.get(flag) is False,"unsafe authority promotion:"+flag)
    pop=state.get("population",{})
    demand(pop.get("query_ids_excluded")==[6186,12469] and pop.get("query_specificity_tested") is False,"unexecuted query specificity promoted")
    demand(pop.get("distinct_test_donors_across_splits")==48,"repeated donor splits presented as 60 independent")
    demand(pop.get("all_three_views_disjoint") is True,"C/T/Y panel overlap not acknowledged")
    means=state.get("means",[])
    demand(len(means)==5 and {m[0] for m in means}==set(ARMS),"incorrect arm records")
    rich=next(m for m in means if m[0]=="R_SINGLE_RICH_V5_LINEAR_PROXY")
    demand("UNFAIR" in rich[-1],"rich teacher extra C input hidden")
    demand(state.get("originals",{}).get("uploaded_large_original_to_github") is False,"unreviewed large original falsely committed")
    demand(state.get("bootstrap_warning","").startswith("48 distinct test donor IDs"),"donor-unit warning erased")
    demand(state.get("local_exact_artifacts",{}).get("score_csv_sha256")==CSV_SHA,"original score SHA receipt mismatch")
    demand(state.get("local_exact_artifacts",{}).get("portable_on_github") is False,"invented public portable transfer")

def main():
    validate(CSV.read_text(),json.loads(STATE.read_text()))
    print("V44_15_EXACT_ORIGINAL_ROWS_FIVE_ARMS_THREE_HELDOUT_SPLITS")
    print("V44_48_UNIQUE_REPEATED_DONOR_CAVEAT_AND_RICH_EVIDENCE_BIAS")
    print("V44_NO_REAL_IPB_NO_Q_SPECIFICITY_NO_TRAINING_AUTHORITY")

if __name__=="__main__":
    main()
