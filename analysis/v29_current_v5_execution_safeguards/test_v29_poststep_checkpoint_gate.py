"""Actual fixture checkpoint bytes + adversarial poststep states; no torch or real expression."""
from __future__ import annotations
import copy, hashlib
from pathlib import Path
import pytest
from analysis.v29_current_v5_execution_safeguards.v29_poststep_checkpoint_gate import (
    SCHEMA, REQUIRED_PARTS,validate_precommit, validate_parts,publish_toy_checkpoint)
def record():
    before={"a":[1.0,2.0],"b":[3.0,4.0]}
    after={"a":[.90,1.85],"b":[2.80,3.85]}
    teacher={"a":[1.0,2.0],"b":[3.0,4.0]}
    p,h=4,8
    m=2**(-p/h)
    end={k:[m*val+(1-m)*x for val,x in zip(teacher[k],after[k])] for k in before}
    return dict(schema=SCHEMA,training_authorized=False,execution_authorized=False,
      gradient=dict(missing=0,nonfinite=0,exact_zero=0,teacher_gradients=0,
        max_abs_gradient=.15,inline_before_step=True,
        per_parameter_observations={k:dict(finite=True,nonzero=True,max_abs=.15) for k in before}),
      online_before=before,online_after=after,
      optimizer_moments_after={k:dict(exp_avg=[.1,.2],exp_avg_sq=[.001,.002],step=1) for k in before},
      optimizer_step_before=0,optimizer_step_after=1,cursor_before=0,cursor_after=1,
      accepted_scientific_presentations=p,learning_rate=.01,weight_decay=.01,
      teacher_before=teacher,teacher_preema=copy.deepcopy(teacher),teacher_after_ema=end,
      ema_half_life_presentations=h)
def parts(tmp_path):
    m={}
    for k in REQUIRED_PARTS:
        b=("SYNTHETIC_ONLY:"+k).encode()
        (tmp_path/k).write_bytes(b)
        m[k]={"sha256":hashlib.sha256(b).hexdigest(),"size":len(b)}
    return m
def bad(edit):
    x=record();edit(x)
    with pytest.raises(ValueError,match="STOP_"):validate_precommit(x)
def test_positive_physical_synthetic_checkpoint_publishes_exclusively(tmp_path):
    m=parts(tmp_path)
    proof=publish_toy_checkpoint(tmp_path,record(),m)
    assert proof["part_count"]==8 and (tmp_path/"COMMIT.json").is_file()
    assert proof["training_authorized"] is False
def test_missing_gradient_report_cannot_pass():
    bad(lambda x:x.pop("gradient"))
def test_malformed_gradient_report_cannot_pass():
    bad(lambda x:x["gradient"].pop("per_parameter_observations"))
def test_hardcoded_zero_counters_without_per_parameter_measurements_cannot_pass():
    bad(lambda x:x["gradient"].update(per_parameter_observations={}))
def test_exact_zero_gradient_mutant_refused():
    bad(lambda x:x["gradient"]["per_parameter_observations"]["a"].update(nonzero=False))
def test_teacher_gradient_mutant_refused():
    bad(lambda x:x["gradient"].update(teacher_gradients=1))
def test_skipped_optimizer_step_refused():
    bad(lambda x:x.update(optimizer_step_after=0))
def test_repeated_optimizer_step_refused():
    bad(lambda x:x.update(optimizer_step_after=2))
def test_cursor_nonadvance_refused():
    bad(lambda x:x.update(cursor_after=0))
def test_empty_first_adam_moment_refused():
    bad(lambda x:x["optimizer_moments_after"]["a"].update(exp_avg=[0.,0.]))
def test_empty_second_adam_moment_refused():
    bad(lambda x:x["optimizer_moments_after"]["b"].update(exp_avg_sq=[0.,0.]))
def test_decay_only_no_beyond_decay_parameter_movement_refused():
    def mutate(x):
        x["online_after"]={k:[v*(1-x["learning_rate"]*x["weight_decay"]) for v in vec]
            for k,vec in x["online_before"].items()}
    bad(mutate)
def test_teacher_preema_mutation_refused():
    bad(lambda x:x["teacher_preema"]["a"].__setitem__(0,999.))
def test_wrong_ema_order_refused():
    bad(lambda x:x["teacher_after_ema"]["a"].__setitem__(0,999.))
def test_partial_checkpoint_missing_optimizer_blocks_publication(tmp_path):
    m=parts(tmp_path);(tmp_path/"optimizer.state").unlink()
    with pytest.raises(ValueError,match="STOP_MISSING_OR_UNSAFE_CHECKPOINT_PART"):
        publish_toy_checkpoint(tmp_path,record(),m)
    assert not(tmp_path/"COMMIT.json").exists()
def test_partial_checkpoint_mutated_after_digest_blocks_publication(tmp_path):
    m=parts(tmp_path);(tmp_path/"teacher.state").write_bytes(b"truncated")
    with pytest.raises(ValueError,match="STOP_PARTIAL_OR_TAMPERED_CHECKPOINT_PART"):
        publish_toy_checkpoint(tmp_path,record(),m)
    assert not(tmp_path/"COMMIT.json").exists()
def test_checkpoint_republication_without_overwrite_refused(tmp_path):
    m=parts(tmp_path);publish_toy_checkpoint(tmp_path,record(),m)
    before=(tmp_path/"COMMIT.json").read_bytes()
    with pytest.raises(ValueError,match="STOP_REFUSE_CHECKPOINT_OVERWRITE"):
        publish_toy_checkpoint(tmp_path,record(),m)
    assert (tmp_path/"COMMIT.json").read_bytes()==before
