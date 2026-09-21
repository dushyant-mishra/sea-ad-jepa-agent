"""Phase IV — freeze the Audit B target sample BEFORE any burden is computed.

This script exists so the sample cannot be chosen, extended or re-rolled after
seeing a burden result. It emits a frozen specification bound to every input that
could change what the sample means, together with a predeclared escalation ladder
and a precision criterion that depends on **precision only** — never on the value
or sign of any result, and never on which masking arm looks better.

What the sample is bound to
---------------------------
Changing any of these changes the meaning of the sample, so each is recorded and
re-verified at execution time:

* the authenticated 17,053-target universe (eligibility receipt digest);
* the authenticated donor/source/fold split receipt digest;
* the planner source — the module whose partner-selection functions define which
  addresses a policy would swap in;
* the masking parameters and evidence-budget authorities, which fix the
  targeted-partner cap and the burden rungs;
* the read-only mask-plan generator used to realize plans;
* a fixed salt, so the draw is reproducible and depends on nothing else.

Selection rule
--------------
Targets are ordered by ``SHA-256(salt | target_address)`` and the first N taken.
This is a **prefix ordering**, so escalating from N1 to N2 to N3 *extends* the
sample rather than re-rolling it — the earlier sample is always a prefix of the
later one, and no target can be dropped by escalating.

Escalation ladder, declared here and not adjustable later
---------------------------------------------------------
``N1 = 256`` → ``N2 = 1024`` → ``N3 = 4096`` targets.

Escalate from Nk to Nk+1 **iff** the relative standard error of the primary
burden statistic exceeds ``MAX_RELATIVE_STANDARD_ERROR`` at Nk.

The criterion is deliberately a function of **precision alone**. It does not
reference the observed ratio, its sign, its distance from 1, or which policy
looks better — so escalation cannot be steered by the result. If the criterion is
still unmet at N3, the outcome is ``INSUFFICIENT_PRECISION_AT_N3``; the ladder
does not continue and the sample is not enlarged opportunistically.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SCHEMA = "V5_AUDIT_B_FROZEN_TARGET_SAMPLE_V1"

#: Fixed before any burden was computed. Changing it would re-roll the draw, so
#: it is part of the frozen specification rather than a runtime option.
SALT = "V5_AUDIT_B_PRODUCTION_BURDEN_TARGET_SAMPLE_20260921"

LADDER = (256, 1024, 4096)

#: Escalate while the relative standard error of the primary burden statistic
#: exceeds this. A precision criterion only: it cannot reference the observed
#: value, its sign, or which arm looks better.
MAX_RELATIVE_STANDARD_ERROR = 0.05

PRIMARY_BURDEN_STATISTIC = (
    "mean over sampled targets of (detected-token burden of addresses ADDED by the "
    "policy) minus (detected-token burden of addresses DROPPED), per target x fold x "
    "policy, expressed relative to the uniform-arm burden at the same rung"
)

#: Inputs whose change invalidates the frozen sample.
BOUND_INPUTS = {
    "target_universe": "analysis/v5_full104_pass1_rebuild_20260920/evidence/"
                       "full104_target_eligibility_v1.json",
    "split_receipt": "analysis/v5_full104_pass1_rebuild_20260920/evidence/"
                     "full104_split_receipt_v1.json",
    "planner_source": "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
    "qualification_runner": "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py",
    "masking_parameters_authority": "src/sea_ad_jepa/v5/"
                                    "masking_qualification_parameters_authority_v3.py",
    "evidence_budget_authority": "src/sea_ad_jepa/v5/target_evidence_budget_authority_v2.py",
    "mask_plan_generator": "analysis/v5_full104_information_channel_redteam_20260920/"
                           "scripts/audit_b_mask_plan_generator_20260920.py",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ordered_targets(addresses: list[int], salt: str = SALT) -> list[int]:
    """Prefix ordering by SHA-256(salt|address).

    Because it is an ordering rather than a per-N draw, N1 is always a prefix of
    N2 and N2 of N3. Escalation therefore extends the sample and can never drop a
    target that has already been measured.
    """
    return sorted(addresses,
                  key=lambda a: hashlib.sha256(f"{salt}|{int(a)}".encode()).digest())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()

    bound = {}
    for role, rel in BOUND_INPUTS.items():
        path = repo / rel
        if not path.is_file():
            raise SystemExit(f"bound input missing: {rel}")
        bound[role] = {"path": rel, "sha256": sha256_file(path)}

    eligibility = json.loads((repo / BOUND_INPUTS["target_universe"]).read_text(encoding="utf-8"))
    addresses = [int(a) for a in eligibility["eligible_target_cols_all_folds"]]
    if len(addresses) != 17053:
        raise SystemExit(f"expected the 17,053-target universe, found {len(addresses)}")

    split = json.loads((repo / BOUND_INPUTS["split_receipt"]).read_text(encoding="utf-8"))

    order = ordered_targets(addresses)
    samples = {f"N{i+1}": {"n": n, "targets": sorted(order[:n])}
               for i, n in enumerate(LADDER)}
    # Prefix property is a promise of the ladder, so it is asserted here rather
    # than assumed by the consumer.
    for i in range(len(LADDER) - 1):
        a = set(samples[f"N{i+1}"]["targets"])
        b = set(samples[f"N{i+2}"]["targets"])
        if not a.issubset(b):
            raise SystemExit("ladder is not a prefix ordering; escalation could drop targets")

    digest_material = json.dumps(
        {"schema": SCHEMA, "salt": SALT, "ladder": list(LADDER),
         "bound": bound, "samples": {k: v["targets"] for k, v in samples.items()}},
        sort_keys=True, separators=(",", ":")).encode("utf-8")
    freeze_digest = hashlib.sha256(digest_material).hexdigest()

    payload = {
        "schema": SCHEMA,
        "scope_class": "CURRENT_FULL104_RECONNAISSANCE",
        "frozen_before_any_burden_was_computed": True,
        "salt": SALT,
        "selection_rule": "targets ordered by SHA-256(salt | target_address); first N taken",
        "prefix_ordering": True,
        "prefix_ordering_note": "N1 is a prefix of N2 and N2 of N3, so escalation EXTENDS "
                                "the sample and can never drop an already-measured target",
        "ladder": list(LADDER),
        "escalation_criterion": {
            "statistic": PRIMARY_BURDEN_STATISTIC,
            "rule": "escalate from Nk to Nk+1 iff relative standard error > "
                    f"{MAX_RELATIVE_STANDARD_ERROR}",
            "max_relative_standard_error": MAX_RELATIVE_STANDARD_ERROR,
            "depends_only_on_precision": True,
            "explicitly_not_a_function_of": [
                "the observed burden ratio", "its sign", "its distance from 1",
                "which masking policy looks better", "any terminal masking outcome",
            ],
            "terminal_outcome_if_unmet_at_N3": "INSUFFICIENT_PRECISION_AT_N3",
            "ladder_does_not_continue_past_N3": True,
        },
        "universe": {
            "targets": len(addresses),
            "eligibility_receipt_sha256": bound["target_universe"]["sha256"],
            "split_receipt_canonical_sha256": split.get("receipt_sha256"),
            "folds": int(split.get("n_folds", 0)),
        },
        "bound_inputs": bound,
        "samples": samples,
        "freeze_digest": freeze_digest,
        "execution_requirements": [
            "policy construction uses TRAINING-side information only",
            "burden measured on the held-out side",
            "reported by source x donor x fold, never only pooled",
            "NO policy adaptation from observed burden",
            "no held-out realized zero/nonzero state may influence mask choice",
            "burden metric fixed in advance; never chosen after seeing which "
            "metric favours a policy",
        ],
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    summary = {k: v for k, v in payload.items() if k != "samples"}
    summary["sample_sizes"] = {k: v["n"] for k, v in samples.items()}
    summary["sample_heads"] = {k: v["targets"][:5] for k, v in samples.items()}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
