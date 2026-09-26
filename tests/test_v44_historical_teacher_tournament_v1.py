"""V44 negative controls: the published historical proxy must not be promoted."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
AREA=ROOT/"analysis/v44_tiny_teacher_team_tournament_20260926"
spec=importlib.util.spec_from_file_location("v44_verify",AREA/"verify_tournament_v1.py")
v44=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v44)
CSV=(AREA/"tournament_scores_v1.csv").read_text()
STATE=json.loads((AREA/"tournament_machine_state_v1.json").read_text())

class V44TournamentAudit(unittest.TestCase):
    def fail(self,change,why,*,csv=False):
        doc=copy.deepcopy(STATE)
        text=CSV
        if csv:text=change(text)
        else:change(doc)
        with self.assertRaisesRegex(ValueError,why):v44.validate(text,doc)

    def test_01_original_exact_15_rows_and_authority_still_off(self):
        v44.validate(CSV,copy.deepcopy(STATE))

    def test_02_original_score_bytes_mutated(self):
        self.fail(lambda x:x.replace("0.41838347911834717","0.99999999999999999"),"score bytes",csv=True)

    def test_03_original_row_deleted(self):
        self.fail(lambda x:"\n".join(x.splitlines()[:-1])+"\n","score bytes",csv=True)

    def test_04_invented_actual_current_v5_run(self):
        self.fail(lambda x:x["authority"].update(actual_current_v5_ipb_executed=True),"unsafe authority")

    def test_05_fake_ema_training(self):
        self.fail(lambda x:x["authority"].update(ema_teacher_trained=True),"unsafe authority")

    def test_06_training_authorized_without_33_roots(self):
        self.fail(lambda x:x["authority"].update(training_authorized=True),"unsafe authority")

    def test_07_invented_q_specificity(self):
        self.fail(lambda x:x["population"].update(query_specificity_tested=True),"unexecuted query")

    def test_08_promote_repeated_60_donor_appearances_as_unique(self):
        self.fail(lambda x:x["population"].update(distinct_test_donors_across_splits=60),"repeated donor")

    def test_09_hide_richer_teacher_C_evidence(self):
        self.fail(lambda x:x["means"][0].__setitem__(4,"T_ONLY_EQUAL"),"extra C input")

    def test_10_false_GitHub_large_original_upload(self):
        self.fail(lambda x:x["originals"].update(uploaded_large_original_to_github=True),"large original")

    def test_11_false_portable_GitHub_upload(self):
        self.fail(lambda x:x["local_exact_artifacts"].update(portable_on_github=True),"public portable")

    def test_12_alter_source_score_hash_receipt(self):
        self.fail(lambda x:x["local_exact_artifacts"].update(score_csv_sha256="0"*64),"receipt mismatch")

    def test_13_omit_unverified_teacher_architecture(self):
        self.fail(lambda x:x["authority"].pop("actual_current_v5_ipb_executed"),"unsafe authority")

    def test_14_mutate_C_T_Y_disjoint_claim(self):
        self.fail(lambda x:x["population"].update(all_three_views_disjoint=False),"panel overlap")

    def test_15_treat_scope_as_real_full104(self):
        self.fail(lambda x:x.update(scope="FULL104_AUTHORIZED_NEURAL_TRAINING"),"surrogate falsely promoted")
if __name__=="__main__":
    unittest.main()
