"""V41 prospective-only Phase-IV G3 source candidate adversaries.

Runs only on the committed pre-outcome frozen sample and source code.
The tests NEVER call Audit-B N1 burden, masking outcome, or training.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.agent.build_phaseiv_g3_source_successor_candidate_v41 import (
    ROOT, ORIGINAL, OLD_FREEZE_DIGEST, OLD_PLANNER_SHA,
    G3_PLANNER_SHA, G3_PARITY_TEST, EXPECTED_ROLES,
    build_candidate, canonical, digest, verify_candidate,
)


@pytest.fixture
def copied_repo(tmp_path):
    root = tmp_path / "repo"
    original = json.loads((ROOT / ORIGINAL).read_bytes())
    paths = [ORIGINAL, G3_PARITY_TEST]
    paths.extend(Path(rec["path"]) for rec in original["bound_inputs"].values())
    for rel in paths:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    return root


def test_draft_rebinds_exactly_one_changed_parent_without_authorizing(copied_repo):
    proposal = build_candidate(copied_repo)
    verify_candidate(proposal, copied_repo)
    assert proposal["parent_original_freeze_canonical_sha256"] == OLD_FREEZE_DIGEST
    assert proposal["changed_original_bound_roles"] == {
        "planner_source": {"old_sha256": OLD_PLANNER_SHA, "new_sha256": G3_PLANNER_SHA},
    }
    assert tuple(proposal["all_seven_current_candidate_inputs"]) == EXPECTED_ROLES
    assert list(proposal["sample_ladder"]) == [256, 1024, 4096]
    assert all(proposal[k] is False for k in (
        "prospective_scientist_signoff_present",
        "new_frozen_sample_issued",
        "audit_b_n1_execution_authorized",
        "terminal_masking_outcomes_inspected",
        "training_authorized",
    ))
    print("V41_DRAFT_ONLY_SOURCE_REBINDING_VALIDATED__ORIGINAL_FREEZE_UNCHANGED")


def test_proposal_is_byte_deterministic_and_recomputable(copied_repo):
    a = build_candidate(copied_repo)
    b = build_candidate(copied_repo)
    assert canonical(a) == canonical(b)
    assert digest(canonical({k: v for k, v in a.items() if k != "proposal_digest"})) == a["proposal_digest"]
    assert len(set(a["original_target_set_digests_by_rung"].values())) == 3


def test_changed_original_freeze_bytes_rejected_before_build(copied_repo):
    path = copied_repo / ORIGINAL
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="original Phase-IV frozen sample physical Git blob differs"):
        build_candidate(copied_repo)


def test_planner_byte_mutation_after_g3_pin_rejected(copied_repo):
    old = json.loads((copied_repo / ORIGINAL).read_bytes())
    path = copied_repo / old["bound_inputs"]["planner_source"]["path"]
    path.write_bytes(path.read_bytes() + b"\n# malicious post-freeze code\n")
    with pytest.raises(ValueError, match="unexpected current Phase-IV source change"):
        build_candidate(copied_repo)


def test_unchanged_other_parent_mutation_rejected(copied_repo):
    old = json.loads((copied_repo / ORIGINAL).read_bytes())
    path = copied_repo / old["bound_inputs"]["qualification_runner"]["path"]
    path.write_bytes(path.read_bytes() + b"\n# illegitimate replacement\n")
    with pytest.raises(ValueError, match="unexpected current Phase-IV source change"):
        build_candidate(copied_repo)


def test_replaced_parity_test_with_same_filename_rejected(copied_repo):
    path = copied_repo / G3_PARITY_TEST
    path.write_bytes(path.read_bytes() + b"\n# modified after successful hosted run\n")
    with pytest.raises(ValueError, match="V40 independently hosted test bytes differ"):
        build_candidate(copied_repo)


def test_caller_fake_approval_or_rehashed_unverified_receipt_rejected(copied_repo):
    proposal = build_candidate(copied_repo)
    altered = copy.deepcopy(proposal)
    altered["prospective_scientist_signoff_present"] = True
    altered["audit_b_n1_execution_authorized"] = True
    altered["proposal_digest"] = digest(canonical({
        k: v for k, v in altered.items() if k != "proposal_digest"
    }))
    with pytest.raises(ValueError, match="differs from independently rederived"):
        verify_candidate(altered, copied_repo)


def test_caller_replaced_parent_digest_rejected_even_with_recomputed_self_hash(copied_repo):
    proposal = build_candidate(copied_repo)
    altered = copy.deepcopy(proposal)
    altered["all_seven_current_candidate_inputs"]["planner_source"]["sha256"] = hashlib.sha256(b"fabricated").hexdigest()
    altered["proposal_digest"] = digest(canonical({
        k: v for k, v in altered.items() if k != "proposal_digest"
    }))
    with pytest.raises(ValueError, match="differs from independently rederived"):
        verify_candidate(altered, copied_repo)


def test_producer_cli_export_and_independent_cli_verify_without_freeze_write(tmp_path):
    candidate = tmp_path / "V41_DRAFT_ONLY.json"
    script = ROOT / "scripts/agent/build_phaseiv_g3_source_successor_candidate_v41.py"
    made = subprocess.run(
        [sys.executable, str(script), "--output", str(candidate)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "V41_DRAFT_G3_SOURCE_SUCCESSOR_PROPOSAL_ONLY__NO_N1_NO_TRAINING" in made.stdout
    checked = subprocess.run(
        [sys.executable, str(script), "--verify", str(candidate)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "V41_INDEPENDENT_DRAFT_CANDIDATE_REDERIVATION_PASS__NOT_FROZEN" in checked.stdout
    assert json.loads(candidate.read_text())["audit_b_n1_execution_authorized"] is False


def test_producer_cli_refuses_frozen_directory_overwrite():
    script = ROOT / "scripts/agent/build_phaseiv_g3_source_successor_candidate_v41.py"
    forbidden = ROOT / ORIGINAL.parent / "_V41_SHOULD_NOT_EXIST.json"
    assert not forbidden.exists()
    result = subprocess.run(
        [sys.executable, str(script), "--output", str(forbidden)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "cannot write inside the original Phase-IV freeze directory" in result.stderr
    assert not forbidden.exists()
