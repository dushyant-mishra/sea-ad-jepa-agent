"""Phase-IV addendum — cryptographically bind the Audit-B EXECUTION RULE.

Why this exists
---------------
The Phase-IV sample freeze (``AUDIT_B_FROZEN_TARGET_SAMPLE.json``, freeze digest
``c2c5e1b5…``) binds **what is sampled**: schema, salt, ladder, the seven bound
input hashes, and the N1/N2/N3 target lists.

It does **not** bind **how the result will be decided**. Verified by mutation:
changing the 0.05 escalation threshold, redefining the primary burden statistic,
flipping the terminal outcome to ``PROCEED_ANYWAY``, setting
``depends_only_on_precision`` to false, emptying the execution requirements, or
even setting ``training_authorized`` to true all leave ``freeze_digest``
unchanged.

That is the wrong half to have frozen. A decision rule that can be edited without
moving a digest is not frozen in any sense that matters, and it is precisely the
rule that must not be adjustable after seeing N1.

This addendum binds the rule **without modifying the original freeze**. The
sample remains valid and its digest unchanged; the addendum references it and
adds a second digest over the decision rule. The combined
``execution_contract_digest`` is what an execution run must cite.

Ratification
------------
One element of the rule is **not** a mechanical restatement of the frozen text
and therefore cannot be self-ratified: see ``RULE.interpretation_dispute``. The
addendum is emitted with ``ratified = false`` and an execution run must refuse
while it stays false. Binding the mechanism is a defect repair; ratifying a
scientific choice is not mine to make.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "V5_AUDIT_B_EXECUTION_RULE_ADDENDUM_V1"

FROZEN_SAMPLE = ("analysis/v5_full104_information_channel_redteam_20260920/evidence/"
                 "phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json")
EXPECTED_FREEZE_DIGEST = "c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac"

#: Modules that implement the rule. Bound so the rule cannot drift from the code.
RULE_SOURCES = {
    "estimator": "src/sea_ad_jepa/v5/audit_b_production_burden_v1.py",
    "evidence_contract": "src/sea_ad_jepa/v5/evidence_estimability_contract_v2.py",
    "rng_authority": "src/sea_ad_jepa/v5/masking_rng_replay_authority_v3.py",
}

RULE = {
    "primary_metric_id": "B2_HELDOUT_DETECTED_TOKEN_BURDEN",
    "secondary_metric_id": "B3_HELDOUT_RAW_UMI_BURDEN__DESCRIPTIVE_ONLY",
    "normalization_id": "ADDED_MINUS_DROPPED_OVER_UNIFORM_FULL_MASK_WITH_TARGET_V1",
    "primary_quantity": (
        "per target x fold x policy x rung: "
        "[B2(addresses ADDED by policy) - B2(addresses DROPPED)] / "
        "B2(UNIFORM_RANDOM full mask at the same target/fold/rung); "
        "the target address is included in the uniform denominator because it is "
        "masked in every arm, and never appears in ADDED or DROPPED"
    ),
    "aggregation": (
        "donors equal-weighted within source; sources equal-weighted within target; "
        "targets equal-weighted; every donor contributes only through its own "
        "held-out fold"
    ),
    "burden_rungs": ["1/20", "1/10", "3/20", "1/5", "3/10", "1/2"],
    "nonuniform_policies": ["TOP8_CORRELATION", "RIDGE8_CONDITIONAL", "PREFIX3_SELECTIVE"],
    "max_relative_standard_error": 0.05,
    "relative_standard_error_definition": "target-level SE / |target-level mean|",
    "zero_mean_rule": "UNDEFINED_ZERO_MEAN__FAIL_CLOSED (never a pass)",
    "escalation_ladder": [256, 1024, 4096],
    "escalation_is_prefix_extension": True,
    "terminal_outcome_if_unmet_at_N3": "INSUFFICIENT_PRECISION_AT_N3",
    "b3_may_drive_escalation": False,
    "execution_requirements": [
        "policy construction uses TRAINING-side information only",
        "burden measured on the HELD-OUT side only",
        "reported by source x donor x fold, never only pooled",
        "NO policy adaptation from observed burden",
        "no held-out realized zero/nonzero state may influence mask choice",
        "burden metric fixed in advance; never chosen after seeing which metric "
        "favours a policy",
        "a masked measured zero is legitimate evidence of non-detection, not missingness",
    ],
    "boundaries": {
        "terminal_masking_outcomes_inspected": False,
        "terminal_policy_selected": None,
        "p1_p2_p3_p4_selected": None,
        "p4_adopted": False,
        "g5_margin_selected": None,
        "terminal_target_panel_selected": None,
        "d_shared_opened": False,
        "pathology_opened": False,
        "training_authorized": False,
    },
    #: The element that cannot be self-ratified.
    "interpretation_dispute": {
        "id": "RSE_SCOPE__18_CELL_CONJUNCTION_VS_SINGLE_AGGREGATE",
        "frozen_text": (
            "escalate from Nk to Nk+1 iff relative standard error of the primary "
            "burden statistic > 0.05"
        ),
        "why_ambiguous": (
            "the frozen text says 'the primary burden statistic' in the singular "
            "while the frozen definition of that statistic is indexed by policy AND "
            "rung. It therefore does not determine whether the criterion is one "
            "aggregate RSE, a conjunction over cells, or something else."
        ),
        "implementation_reading": (
            "conjunction: all 3 non-uniform policies x 6 burden rungs = 18 cells "
            "must each satisfy RSE <= 0.05"
        ),
        "why_this_is_a_new_scientific_choice": [
            "a conjunction over 18 cells is materially stricter than one aggregate "
            "RSE, so it changes when escalation fires",
            "the zero-mean fail-closed rule appears NOWHERE in the frozen text and "
            "is wholly additional",
            "structurally, the numerator is (ADDED - DROPPED) while the denominator "
            "is the full uniform mask; if for some policy x rung those two burdens "
            "are close, the target-level mean approaches zero, RSE becomes undefined "
            "or very large, and escalation is forced by a near-zero denominator "
            "rather than by genuine imprecision on the cells that matter",
        ],
        "not_predicted_here": (
            "whether any cell actually has a near-zero mean is an OUTCOME and is "
            "deliberately not estimated. The earlier 512-address reduced-pool ratios "
            "are REDUCED_POOL_DIAGNOSTIC and must not be used to predict it."
        ),
        "status": "REQUIRES_EXPLICIT_RATIFICATION_BEFORE_N1",
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ratified", action="store_true",
                    help="only pass once the interpretation dispute has been ratified "
                         "by the owner; never set it to make an execution run proceed")
    args = ap.parse_args()
    repo = args.repo.resolve()

    sample_path = repo / FROZEN_SAMPLE
    if not sample_path.is_file():
        raise SystemExit(f"frozen sample missing: {FROZEN_SAMPLE}")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    if sample["freeze_digest"] != EXPECTED_FREEZE_DIGEST:
        raise SystemExit(
            f"frozen sample digest {sample['freeze_digest']} != expected "
            f"{EXPECTED_FREEZE_DIGEST}; the addendum must not be written against a "
            "different sample")

    rule_sources = {}
    for role, rel in RULE_SOURCES.items():
        path = repo / rel
        if not path.is_file():
            raise SystemExit(f"rule source missing: {rel}")
        rule_sources[role] = {"path": rel, "sha256": sha256_file(path)}

    rule_digest = hashlib.sha256(
        canonical({"schema": SCHEMA, "rule": RULE, "rule_sources": rule_sources})
    ).hexdigest()

    execution_contract_digest = hashlib.sha256(
        canonical({"schema": SCHEMA,
                   "sample_freeze_digest": EXPECTED_FREEZE_DIGEST,
                   "rule_digest": rule_digest})
    ).hexdigest()

    payload = {
        "schema": SCHEMA,
        "scope_class": "CURRENT_FULL104_RECONNAISSANCE",
        "supersedes_nothing": True,
        "original_sample_freeze_unmodified": True,
        "sample_freeze_digest": EXPECTED_FREEZE_DIGEST,
        "gap_this_addendum_closes": (
            "the sample freeze digest covers schema, salt, ladder, seven bound input "
            "hashes and the target lists, but NOT the escalation rule, the primary "
            "burden statistic definition, the execution requirements, or the boundary "
            "flags. Those could all be edited without moving freeze_digest, which was "
            "verified by mutation."
        ),
        "rule": RULE,
        "rule_sources": rule_sources,
        "rule_digest": rule_digest,
        "execution_contract_digest": execution_contract_digest,
        "ratified": bool(args.ratified),
        "execution_gate": (
            "an Audit-B execution run MUST cite execution_contract_digest and MUST "
            "refuse to run while ratified is false"
        ),
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "rule"}, indent=2))
    print()
    print("interpretation dispute status:",
          RULE["interpretation_dispute"]["status"])
    print("ratified:", payload["ratified"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
