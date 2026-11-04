"""Macha independent cumulative review of PR #541 at exact head 3b86b946 (tests only; code UNCHANGED).

Base: frozen Task 3 117dd51d. Scope: the Sol/GPT-authored Task 4 code and its whole-candidate
interactions. Macha-authored hunks (#428 handle identity, #459 X1 publish transaction, #465 short
I/O) are not independently reviewed here; Sol reviews them.

Only mechanisms that no retained test covers are added:

RED
  K01  C3 trusts isinstance(history_custody, RegistryHistoryCustody). A subclass whose
       validate_current does nothing earns C3_CURRENT_REGISTRY = PASS for any registry.
       It is latent: C5-C9 are hard-coded FAIL, so FINAL stays refused. The barrier's
       per-check report is still false, and C3 has no exact-type guard once C5-C9 are wired.
LIMIT (passes; a declared limitation recorded as evidence for HOLD)
  L01  The finite-exam lifecycle never touches PersistentCustodyStore. A second process
       re-creates the same DEVELOPMENT campaign identity with a fresh exposure budget.
       The exposure_ledger_v1 schema has no producer.
GUARD
  The real Task 3 history custody still validates. FINAL creation is still refused with
  a lawful harness. An in-process duplicate is still refused.

Synthetic fixtures only. No sealed exposure, training, GPU, real data or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.v5.td_unified import challenge_custody_v1 as c
from scripts.v5.td_unified import registry_v1 as registry
from scripts.v5.td_unified.task4_authority_barrier_v1 import Task4AuthorityHarness, evaluate_task4_preauthority_barrier

REPO = Path(__file__).resolve().parents[3]


def _deps():
    x = {
        "task2_manifest_sha": "1" * 64,
        "task3_registry_sha": "2" * 64,
        "registry_unit_identities": (("G8", "3" * 64),),
        "producer_actor_identity": "4" * 64,
        "executor_actor_identity": "5" * 64,
        "controller_actor_identity": "6" * 64,
        "adjudicator_actor_identity": "7" * 64,
        "challenge_generator_code_sha": "8" * 40,
        "challenge_generator_policy_sha": "9" * 64,
        "realization_schema_sha": "a" * 64,
        "rng_policy_sha": "b" * 64,
        "challenge_family_sha": "c" * 64,
        "adjudication_contract_sha": "d" * 64,
        "multiplicity_policy_sha": "e" * 64,
        "publication_policy_sha": "f" * 64,
        "genesis_ledger_identity": "0" * 64,
        "authority_scope": "UNIT:G8",
        "authority_restrictions": ("NO_TRAINING_AUTHORITY",),
        "qualification_budget": 2,
    }
    x.update(c.development_fixture_generator_identities())
    return x


class _NonValidatingHistoryCustody(registry.RegistryHistoryCustody):
    """Caller-supplied look-alike: never binds any registry state."""

    def __init__(self):  # skip the real constructor's anchors entirely
        pass

    def validate_current(self, registry_snapshot) -> None:
        return None


class _Store:
    def replay(self):
        raise RuntimeError("no persistent store in this probe")


def test_k01_red_c3_must_not_pass_for_a_non_validating_history_custody_subclass():
    status = evaluate_task4_preauthority_barrier(
        "G8",
        object(),  # not a registry at all
        custody_store=_Store(),
        expected_head="0" * 64,
        actor_context={"history_custody": _NonValidatingHistoryCustody()},
    )
    assert status.overall == "RED"  # C5-C9 still fail closed, so no FINAL bypass today
    assert status.checks["C3_CURRENT_REGISTRY"] == "FAIL", (
        "C3 reported PASS for a subclass that validated nothing against a non-registry object")


def test_guard_final_creation_is_still_refused_with_a_lawful_harness_type():
    harness = Task4AuthorityHarness(
        unit_id="G8", registry=object(), custody_store=_Store(), expected_head="0" * 64,
        actor_context={"history_custody": _NonValidatingHistoryCustody()},
    )
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("final-probe", _deps(), barrier_status=None, namespace="FINAL", authority_harness=harness)


def test_guard_in_process_duplicate_campaign_is_still_refused():
    c.create_campaign("dup-probe", _deps(), barrier_status=None, namespace="DEVELOPMENT")
    with pytest.raises(c.Task4ChallengeCustodyError):
        c.create_campaign("dup-probe", _deps(), barrier_status=None, namespace="DEVELOPMENT")


_CHILD = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from scripts.v5.td_unified import challenge_custody_v1 as c
deps = json.loads(sys.argv[2])
deps["registry_unit_identities"] = tuple(tuple(x) for x in deps["registry_unit_identities"])
deps["authority_restrictions"] = tuple(deps["authority_restrictions"])
camp = c.create_campaign("cross-process-remint", deps, barrier_status=None, namespace="DEVELOPMENT")
p = c._private_campaign(camp)
print(json.dumps({"identity": p.campaign_identity, "budget": p.dependencies["qualification_budget"],
                  "consumed": p.exposures_consumed}))
"""


def test_l01_limit_second_process_remints_the_same_development_campaign_with_a_fresh_budget():
    deps = _deps()
    first = c.create_campaign("cross-process-remint", deps, barrier_status=None, namespace="DEVELOPMENT")
    first_identity = c._private_campaign(first).campaign_identity
    child = subprocess.run([sys.executable, "-c", _CHILD, str(REPO), json.dumps(deps)],
                           capture_output=True, text=True, timeout=120, check=True)
    out = json.loads(child.stdout.strip().splitlines()[-1])
    # LIMIT, not RED: challenge_custody_v1 declares cross-process uniqueness out of scope.
    # This must flip to a refusal once durable exposure custody (exposure_ledger_v1) is wired.
    assert out["identity"] == first_identity
    assert out["consumed"] == 0
    assert out["budget"] == deps["qualification_budget"]


def test_l01_limit_challenge_lifecycle_has_no_persistent_custody_binding():
    source = (REPO / "scripts/v5/td_unified/challenge_custody_v1.py").read_text(encoding="utf-8")
    assert "task4_custody_store" not in source and "append_event" not in source
    producers = [p for p in (REPO / "scripts/v5/td_unified").glob("*.py")
                 if "exposure_ledger" in p.read_text(encoding="utf-8")]
    assert producers == []
