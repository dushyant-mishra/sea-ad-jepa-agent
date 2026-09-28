"""V27 independent V4 freeze source-byte mutation control, no real training."""
import csv
import shutil
from pathlib import Path
from scripts.agent.audit_teacher_student_integration_freeze_v4 import (
    audit, SOURCE_MANIFEST, SOURCE_ROOT, FREEZE, TEST_SELECTION, ACTIVE_TEST_MANIFEST,
    SOURCE_AUTHORITY, OVERLAY_VALIDATOR, RUNTIME, RELATIONAL_TARGET, RELATIONAL_AUTHORITY,
    RELATIONAL_DESIGN, REVIEW_INSTRUCTIONS,
)
ROOT=Path(__file__).resolve().parents[1]

def test_current_v4_baseline_still_passes():
    result=audit(ROOT)
    assert result["terminal"]=="PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",result

def test_mutating_one_actual_frozen_source_byte_fails_before_acceptance(tmp_path):
    # Copy precisely referenced authority and frozen bytes; never modify originals.
    fixed=(SOURCE_MANIFEST,SOURCE_ROOT,FREEZE,TEST_SELECTION,ACTIVE_TEST_MANIFEST,
           SOURCE_AUTHORITY,OVERLAY_VALIDATOR,RUNTIME,RELATIONAL_TARGET,
           RELATIONAL_AUTHORITY,RELATIONAL_DESIGN,REVIEW_INSTRUCTIONS)
    with (ROOT/SOURCE_MANIFEST).open(newline="",encoding="utf-8") as f:
        sources=[Path(r["path"]) for r in csv.DictReader(f)]
    with (ROOT/ACTIVE_TEST_MANIFEST).open(newline="",encoding="utf-8") as f:
        tests=[Path(r["path"]) for r in csv.DictReader(f)]
    for rel in set(fixed)|set(sources)|set(tests):
        dst=tmp_path/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/rel,dst)
    pristine=audit(tmp_path)
    assert pristine["terminal"]=="PASS_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4",pristine
    tampered=tmp_path/RUNTIME
    with tampered.open("ab") as f:
        f.write(b"\n# planted V27 source-byte mutation; not a real project edit\n")
    result=audit(tmp_path)
    assert result["terminal"]=="STOP_TEACHER_STUDENT_INTEGRATION_FREEZE_AUDIT_V4"
    assert any(s.startswith("source SHA mismatch: "+RUNTIME.as_posix()) for s in result["failures"]),result
