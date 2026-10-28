"""Static, source-limited custody check for independent PR480 reviewer RED.

Does not re-run original human calibration, authenticate a source issuer,
or turn expected failing adversarial cases into a qualified Task3 PASS.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path("results/production_synthetic/JEPA_TASK3_CHATGPT_INDEPENDENT_REVIEW_20261028.json")
PROBE = Path("docs/agent/review_probes/chatgpt_20261028/ps_task3_437_expected_red_probe.py.txt")
REPORT = Path("docs/agent/JEPA_PS_TASK3_MACHA437_INDEPENDENT_REVIEW_20261028.md")
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
PROBE_BLOB = "9f2ea674b41730faacd9801a82a20745e592d9ad"
REPORT_BLOB = "3ea78eed8965cd46478bf980ab2d7105a2c689f6"

def must(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("PS_TASK3_INDEPENDENT_REVIEW_NONPROMOTION_REFUSAL: " + message)

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def verify(d: dict, probe_blob: str, report_blob: str) -> None:
    must(type(d) is dict and d.get("schema") ==
         "JEPA_PS_TASK3_CHATGPT_INDEPENDENT_437_REVIEW_DELTA_V1", "schema")
    must(d.get("kind") ==
         "APPEND_ONLY_HOSTILE_REVIEW__SOURCE_UNMODIFIED__NOT_CALIBRATION_ACCEPTANCE", "scope")
    must(d.get("source_pr")==437 and
         d.get("source_head")=="fd3242ada6f77ba09ff2d8a1c7716eb9725ced11" and
         d.get("source_git_blob")=="bafd0a24536a30ca927c9808e2feddda4cb29428" and
         d.get("source_unchanged") is True, "original Macha source")
    must(d.get("review_pr")==480 and
         d.get("review_initial_ci_head")=="3635eae7ee0df5a4e311f04c16e9ab0e6d574fff" and
         d.get("tests_source_git_blob")==PROBE_BLOB and
         probe_blob==PROBE_BLOB and report_blob==REPORT_BLOB, "original reviewer artifact identity")
    must(d.get("verdict")=="REPAIR_REQUIRED__R1_NUMERIC_ALIAS__R2_OBS_PARAMETER_SPOOF","verdict")
    cases=d.get("findings",[])
    must(type(cases) is list and
         {v.get("id") for v in cases if type(v) is dict}=={"R1","R2A","R2B"} and
         all(v.get("real_data_executed") is False for v in cases),
         "the three synthetic adversarial results")
    ci=d.get("ci",{})
    must(ci.get("review_expected_red_run")==40733195290 and
         ci.get("review_expected_red_conclusion")=="SUCCESS_EXPECTED_RED_ASSERTION" and
         ci.get("review_hostile_failed")==3 and ci.get("review_nonpromotion_control_passed")==1,
         "expected RED cannot be painted green")
    must(ci.get("original_macha_unchanged_tests_passed")==33 and
         ci.get("full_task3_run")==40733195258 and
         ci.get("full_task3_conclusion")=="FAILURE_INCLUDES_NEW_REVIEW_TESTS" and
         ci.get("full_task3_failed")==3 and ci.get("full_task3_passed")==391 and
         ci.get("full_task3_xfailed")==1, "original source/broad CI scope")
    must(ci.get("unified_synthetic_run")==40733195217 and
         ci.get("unified_synthetic_conclusion")=="SUCCESS", "unchanged unified scope")
    must(d.get("authority")==AUTH and len(d.get("external_blockers",[]))>=4,
         "external gates and training authorization")
    must(any("registry is empty" in x for x in d.get("preserve_positive",[])),
         "empty real calibration registry")

def validate_root(root=ROOT) -> None:
    d=json.loads((root/DATA).read_text(encoding="utf-8"))
    verify(d, git_blob((root/PROBE).read_bytes()), git_blob((root/REPORT).read_bytes()))

if __name__=="__main__":
    validate_root()
    print("PS_TASK3_MACHA437_R1_R2_HOSTILE_REVIEW_PRESERVED__3_RED_33_ORIGINAL_PASS__NO_REAL_CALIBRATION")
