"""Stage 3 preparation — the three pathology-blind authorities the adjudicator needs.

Built before confirmation AT8 opens, and none of them reads any pathology value.

1. The rare-5 decision-capability status file. A declaration that the historical
   rare-5 endpoint family is not decision-capable because its authority is
   missing. `t0_target_family_authority_v3._load_status` accepts only that
   status, with `decision_capable` False, and refuses anything else with "new
   reviewed family contract required". So this file records a fact about what is
   absent; it does not weaken the primary hypothesis.

2. The target family authority v3 package. `family_mode: PRIMARY_ONLY`,
   `primary_hypothesis: BROAD_IMMUNE_EXPRESSION_TARGET`. The alphas come from
   `t0_decision_v1` and the tail engine and allowed n from `t0_tail_hc3_t_v1`,
   so every decision constant is taken from the frozen modules rather than
   retyped here.

   Worth stating because it is easy to misread: the rare-5 family being
   not-decision-capable is exactly why the family is PRIMARY_ONLY. The primary
   T0 decision is capable and carries real alphas.

3. The technical sensitivity registry, with **zero additional blocks**. That is
   the faithful configuration rather than a convenience:

     * `mandatory_direct_observation_block` is fixed at `['Q_DEPTH','Q_DETECT']`
       and additional blocks are forbidden from repeating it;
     * `additional_block_semantics` is `CUMULATIVE_ON_TOP_OF_Q_DEPTH_Q_DETECT`;
     * the V18 frozen constants set `qc_metric_count: 2`, which is those two;
     * `t0_adjudicator_v1` builds `measurement_names=['Q_DEPTH+Q_DETECT']` as
       the base sensitivity and adds one per registry block.

   So zero additional blocks yields exactly one measurement sensitivity, which
   is what the frozen design specifies. Declaring extra blocks here would add
   sensitivity models the contract does not call for.

Q_DEPTH and Q_DETECT reach the confirmation adjudication through the confirmation
state donor table, not through `confirmation_metadata`, so the registry's
additional blocks are genuinely additional.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_execution_input_readiness_authority_v1 as readiness  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402

SUMMARY = "T0_STAGE3_PREP_SUMMARY.json"
RARE5_STATUS_FILE = "T0_RARE5_DECISION_CAPABILITY_STATUS.json"

RARE5_STATUS = "NOT_DECISION_CAPABLE_AUTHORITY_MISSING"
RARE5_SCHEMA = "JEPA_T0_RARE5_DECISION_CAPABILITY_STATUS_V1"
RARE5_REASON = (
    "The historical rare-5 endpoint family has no materialized decision "
    "authority in the recovered V20 package, so it is declared not "
    "decision-capable. This records what is absent and does not weaken the "
    "primary broad-IMMUNE hypothesis, which is why the target family is "
    "PRIMARY_ONLY.")

FAMILY_NOTE = (
    "Primary-only family for the staged real T0 run. Alphas, tail engine and "
    "tail allowed n are taken from the frozen t0_decision_v1 and "
    "t0_tail_hc3_t_v1 modules rather than retyped. The rare-5 family is not "
    "decision-capable and is excluded, which is the reason for PRIMARY_ONLY.")

TECHNICAL_AUDIT_NOTE = (
    "Zero additional technical blocks. The mandatory direct observation block "
    "is Q_DEPTH and Q_DETECT, additional blocks are cumulative on top of those "
    "and may not repeat them, and the V18 frozen constants set qc_metric_count "
    "to 2. The adjudicator builds Q_DEPTH+Q_DETECT as the base measurement "
    "sensitivity and adds one per registry block, so zero blocks yields exactly "
    "the one measurement sensitivity the frozen design specifies. Declaring "
    "extra blocks would add models the contract does not call for.")

STOP_STATUS = "STOP_T0_STAGE3_RARE5_STATUS_DECLARATION_INVALID"
STOP_FAMILY = "STOP_T0_STAGE3_FAMILY_AUTHORITY_CONSTANTS_NOT_FROM_FROZEN_MODULES"
STOP_TECHNICAL = "STOP_T0_STAGE3_TECHNICAL_REGISTRY_DECLARES_EXTRA_BLOCKS"


def code_sha256(filename: str) -> str:
    """SHA-256 over LF-normalized content. Not a Git blob digest."""
    path = Path(__file__).resolve().parent / filename
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def write_rare5_status(path: Path, *, log=print) -> dict[str, Any]:
    """Declare the rare-5 family not decision-capable, in the frozen schema."""
    obj = {
        "schema": RARE5_SCHEMA,
        "historical_rare5_status": RARE5_STATUS,
        "decision_capable": False,
        "reason": RARE5_REASON,
    }
    blob = (json.dumps(obj, sort_keys=True, separators=(",", ":"))
            + "\n").encode("utf-8")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "wb") as handle:
        handle.write(blob)
    digest = hashlib.sha256(blob).hexdigest()

    # Verified through the frozen loader, which refuses a decision-capable or
    # altered declaration.
    family_mod = stage2a._frozen("t0_target_family_authority_v3")
    status, status_sha = family_mod._load_status(path)
    if status_sha != digest:
        raise AssertionError("%s: digest %s, loader saw %s"
                             % (STOP_STATUS, digest, status_sha))
    if status["decision_capable"] is not False:
        raise AssertionError("%s: declaration is decision-capable"
                             % STOP_STATUS)
    log("    rare-5 status %s" % RARE5_STATUS)
    log("    status file digest %s" % digest)
    return {"path": str(path), "sha256": digest, "status": status}


def build_family_authority(outdir: Path, *, status_file: Path,
                           log=print) -> dict[str, Any]:
    """Build the primary-only family authority from the frozen constants."""
    family_mod = stage2a._frozen("t0_target_family_authority_v3")
    decision = stage2a._frozen("t0_decision_v1")
    tail = stage2a._frozen("t0_tail_hc3_t_v1")

    built = family_mod.build_primary_only_family_v3(
        str(outdir), str(status_file), FAMILY_NOTE)
    authority = built["authority"]

    # Every decision constant must be the frozen module's value.
    expected = {
        "primary_positive_alpha": decision.STATE_POS_ALPHA,
        "primary_negative_alpha": decision.NEG_ALPHA,
        "tail_positive_alpha": decision.TAIL_POS_ALPHA,
        "tail_negative_alpha": decision.NEG_ALPHA,
        "sensitivity_directional_alpha": decision.SENS_ALPHA,
        "tail_allowed_n": sorted(tail.TAIL_ALLOWED_N),
        "tail_engine": "HC3_T_RESIDUAL_DF",
    }
    for field, value in expected.items():
        if authority.get(field) != value:
            raise AssertionError("%s: %s is %r, frozen module says %r"
                                 % (STOP_FAMILY, field, authority.get(field),
                                    value))
    reloaded = family_mod.load_primary_only_family_v3(str(outdir))
    if reloaded["package_root_sha256"] != built["package_root_sha256"]:
        raise AssertionError("%s: family package does not replay" % STOP_FAMILY)

    log("    family mode %s, primary hypothesis %s"
        % (authority["family_mode"], authority["primary_hypothesis"]))
    log("    primary alpha %s, negative %s, tail positive %s, sensitivity %s"
        % (authority["primary_positive_alpha"],
           authority["primary_negative_alpha"],
           authority["tail_positive_alpha"],
           authority["sensitivity_directional_alpha"]))
    log("    tail engine %s, allowed n %s"
        % (authority["tail_engine"], authority["tail_allowed_n"]))
    log("    family package root %s" % built["package_root_sha256"])
    return {"package_root_sha256": built["package_root_sha256"],
            "authority": authority}


def build_technical_registry(outdir: Path, *, source_authority_hashes,
                             log=print) -> dict[str, Any]:
    """Build the technical sensitivity registry with zero additional blocks."""
    registry_mod = stage2a._frozen("t0_technical_registry_v3")
    built = registry_mod.build_technical_registry_v3(
        str(outdir), [], dict(source_authority_hashes), TECHNICAL_AUDIT_NOTE)
    reloaded = registry_mod.load_technical_registry_v3(str(outdir))
    if reloaded["blocks"]:
        raise AssertionError("%s: %r" % (STOP_TECHNICAL, reloaded["blocks"]))
    if reloaded["registry"]["mandatory_direct_observation_block"] != [
            "Q_DEPTH", "Q_DETECT"]:
        raise AssertionError("%s: the mandatory block is not the frozen two"
                             % STOP_TECHNICAL)
    log("    mandatory block %s"
        % reloaded["registry"]["mandatory_direct_observation_block"])
    log("    additional blocks %d (zero is the frozen configuration)"
        % len(reloaded["blocks"]))
    log("    technical registry root %s" % built["package_root_sha256"])
    return {"package_root_sha256": built["package_root_sha256"],
            "blocks": reloaded["blocks"],
            "registry": reloaded["registry"]}


def run(*, outdir: Path, readiness_pkg: Path, family_outdir: Path,
        technical_outdir: Path, log=print) -> dict[str, Any]:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%5.1fs] %s" % (time.time() - started, message))

    stamp("re-verifying the R7 gate before building Stage 3 authorities")
    gate = stage2a.verify_r7_gate(readiness_pkg, log=lambda m: None)
    stamp("  R7 gate verified: readiness root %s"
          % gate["readiness_root_sha256"])
    bindings = gate["authority"]["bindings"]

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    stamp("1/3 declaring the rare-5 decision capability status")
    status = write_rare5_status(out / RARE5_STATUS_FILE, log=log)

    stamp("2/3 building the primary-only target family authority")
    family = build_family_authority(family_outdir,
                                    status_file=out / RARE5_STATUS_FILE,
                                    log=log)

    stamp("3/3 building the technical sensitivity registry")
    technical = build_technical_registry(
        technical_outdir,
        source_authority_hashes={
            "technical_completeness_root_sha256":
                bindings["technical_completeness_root_sha256"],
            "population_raw_source_root_sha256":
                bindings["b2_population_raw_source_root_sha256"],
            "eligible_donor_root_sha256":
                bindings["eligible_donor_root_sha256"],
        },
        log=log)

    record = {
        "schema": "JEPA_T0_STAGE3_PREP_SUMMARY_V1",
        "terminal": "STAGE3_PATHOLOGY_BLIND_AUTHORITIES_BUILT",
        "rare5_status_file_sha256": status["sha256"],
        "rare5_status": RARE5_STATUS,
        "rare5_decision_capable": False,
        "target_family_package_root_sha256": family["package_root_sha256"],
        "family_mode": family["authority"]["family_mode"],
        "primary_hypothesis": family["authority"]["primary_hypothesis"],
        "primary_positive_alpha": family["authority"]["primary_positive_alpha"],
        "primary_negative_alpha": family["authority"]["primary_negative_alpha"],
        "tail_positive_alpha": family["authority"]["tail_positive_alpha"],
        "sensitivity_directional_alpha":
            family["authority"]["sensitivity_directional_alpha"],
        "tail_engine": family["authority"]["tail_engine"],
        "tail_allowed_n": family["authority"]["tail_allowed_n"],
        "technical_registry_package_root_sha256":
            technical["package_root_sha256"],
        "technical_additional_blocks": len(technical["blocks"]),
        "technical_mandatory_block":
            technical["registry"]["mandatory_direct_observation_block"],
        "r7_readiness_root_sha256": gate["readiness_root_sha256"],
        "confirmation_numeric_at8_accessed": False,
        "numeric_at8_value_read": False,
        "dev_opened": False,
        "sealed_opened": False,
        "scientific_design_unchanged": True,
        "runner_code_sha256": code_sha256("t0_stage3_prep_authorities_v1.py"),
        "code_byte_semantics": readiness.ACCURATE_CODE_BYTE_SEMANTICS,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    with io.open(out / SUMMARY, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    stamp("wrote %s" % (out / SUMMARY))
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--readiness-pkg", required=True, type=Path)
    parser.add_argument("--family-outdir", required=True, type=Path)
    parser.add_argument("--technical-outdir", required=True, type=Path)
    args = parser.parse_args(argv)

    record = run(outdir=args.outdir, readiness_pkg=args.readiness_pkg,
                 family_outdir=args.family_outdir,
                 technical_outdir=args.technical_outdir)
    print()
    print(json.dumps(record, indent=2, sort_keys=True))
    print()
    print("STAGE 3 PATHOLOGY-BLIND AUTHORITIES BUILT. "
          "Confirmation numeric AT8 not accessed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
