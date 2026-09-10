#!/usr/bin/env python3
"""Reporting-only T0 V20 sensitivity recovery using explicit replay equivalence.

This successor does not edit or weaken the frozen V20 bit-exact verifier. It
routes a separately versioned target replay-equivalence verifier only inside a
derived Stage-3 execution namespace, while preserving the existing R8 execution
input authority routing. The state adjudicator repair remains the V1 reporting-
only repair: it surfaces sensitivity values the frozen adjudicator already
computed but omitted from five return paths.
"""
from __future__ import annotations

import argparse
import inspect
import io
import json
import sys
import time
import types
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_numeric_environment_v1 as numeric_environment
import t0_replay_equivalence_v1 as replay

# Frozen policy identities, selected by name. Not a tolerance knob: neither
# module exposes a configurable budget, and V2 refuses to load unless it is the
# single authorized change from V1.
POLICY_VERSIONS = ("v1", "v2")
DEFAULT_POLICY_VERSION = "v1"
_ACTIVE_POLICY: Any = replay

STOP = "STOP_T0_SENSITIVITY_RECOVERY_V2_REFUSED"
DECISION_FILE = "T0_V20_ADJUDICATION_DECISION.json"
RECOVERY_FILE = "T0_V20_RECOVERED_SENSITIVITY_STATISTICS_V2.json"
EQUIVALENCE_REPORT_FILE = "T0_V20_REPLAY_EQUIVALENCE_REPORT.json"
ROUTER_ANCHOR = "    namespace = dict(frozen.__dict__)"
# Stage 3 resolves the tail-freeze module inside `run`; the derived chain has to
# be substituted in there or step 4 reaches the frozen bit-exact verifier first.
FREEZE_ANCHOR = '    freeze_mod = stage2a._frozen("t0_canonical_freeze_v1")'
FREEZE_REPLACEMENT = "    freeze_mod = _recovery_freeze_module"
# The frozen path reaches the target verifier twice: once at the tail freeze
# (step 4) and once in the adjudicator (step 9). Counted from the frozen call
# sites, not from what a run happened to produce.
TAIL_CHAIN_FUNCTIONS = ("compute_tail_threshold", "freeze_tail_authority")
EXPECTED_TARGET_REPLAYS = 2
ROUTED_SOURCE_MARKER = 'source = inspect.getsource(frozen._adjudicate_from_raw_v2)'
R8_PRETARGET_MARKER = 'namespace["verify_pretarget_execution_authority"]'
R8_PREADJUDICATION_MARKER = 'namespace["verify_preadjudication_execution_authority"]'


class ReplayStopped(RuntimeError):
    """The frozen equivalence policy refused. Carries the evidence to publish."""

    def __init__(self, reason: str, full_reports: list[dict[str, Any]],
                 repair_report: dict[str, Any] | None):
        super().__init__(reason)
        self.reason = reason
        self.full_reports = full_reports
        self.repair_report = repair_report


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def build_stop_report(reason: str, full_reports: list[dict[str, Any]],
                      repair_report: dict[str, Any] | None) -> dict[str, Any]:
    """The complete equivalence report for a run the policy refused.

    Published rather than discarded. The budgets are not revisited here: a
    refused replay is a finding about this numeric stack, and re-choosing the
    tolerance that would have admitted it is a different act from reporting it.
    """
    stopped: list[str] = []
    for entry in full_reports:
        stopped.extend(entry.get("full_report", {}).get("stopped_fields", []))
    return {
        "schema": "JEPA_T0_V20_REPLAY_EQUIVALENCE_STOP_REPORT_V1",
        "replay_equivalence_policy": policy_identity(),
        "terminal": "STOP_T0_V20_REPLAY_NOT_EQUIVALENT_UNDER_FROZEN_POLICY",
        "reason": reason,
        "stopped_fields": sorted(set(stopped)),
        "sensitivity_statistics_recovered": False,
        "why_not_recovered":
            "The frozen equivalence policy refused the target replay at Stage 3 "
            "step 4, which precedes the adjudicator, so the omitted sensitivity "
            "surfaces were never reached.",
        "tolerances_revisited_after_seeing_the_discrepancy": False,
        "historical_bit_exact_verifier_modified": False,
        "frozen_v20_files_modified": 0,
        "training_authorized": False,
        "t0_conclusion_changed": False,
        "numeric_environment": numeric_environment.numeric_environment(),
        "reporting_repair": repair_report,
        "target_replay_reports": full_reports,
    }


def _deps():
    """Load project modules lazily so pure governance helpers are testable."""
    import t0_sensitivity_recovery_v1 as v1
    import t0_stage2a_pre_at8_gate_v1 as stage2a
    import t0_stage3_confirmation_v1 as stage3
    return v1, stage2a, stage3


def select_policy(version: str) -> Any:
    """Bind the frozen policy this run applies. V1 unless asked otherwise."""
    global _ACTIVE_POLICY
    if version not in POLICY_VERSIONS:
        _fail("unknown policy version %r; expected one of %r"
              % (version, list(POLICY_VERSIONS)))
    if version == "v1":
        _ACTIVE_POLICY = replay
    else:
        import t0_replay_equivalence_v2 as replay_v2
        # Raises unless V2 is exactly the authorized single change from V1.
        replay_v2.verify_single_policy_change()
        _ACTIVE_POLICY = replay_v2
    return _ACTIVE_POLICY


def active_policy() -> Any:
    return _ACTIVE_POLICY


def policy_identity() -> dict[str, Any]:
    """What a reviewer needs to check the tolerances this run actually used."""
    policy = _ACTIVE_POLICY
    identity: dict[str, Any] = {
        "module": policy.__name__,
        "identity": getattr(policy, "POLICY_IDENTITY",
                            "JEPA_T0_V20_TARGET_REPLAY_EQUIVALENCE_V1"),
        "float_policy": policy.FLOAT_POLICY,
        "ulp_policy": policy.ULP_POLICY,
        "exact_array_fields": list(policy.EXACT_ARRAY_FIELDS),
        "exact_scalar_fields": list(policy.EXACT_SCALAR_FIELDS),
        "required_float_dtype": str(policy.REQUIRED_FLOAT_DTYPE),
        "state_primary_float_rtol": policy.STATE_PRIMARY_FLOAT_RTOL,
        "state_primary_float_fields": list(policy.STATE_PRIMARY_FLOAT_FIELDS),
        "state_primary_exact_fields": list(policy.STATE_PRIMARY_EXACT_FIELDS),
    }
    if hasattr(policy, "policy_digest"):
        identity["policy_sha256"] = policy.policy_digest()
        identity["policy_document"] = policy.POLICY_DOCUMENT
        identity["single_authorized_change"] = policy.verify_single_policy_change()
    return identity


def derive_r8_router_source(router_source: str) -> str:
    """Inject exactly two recovery hooks; preserve the R8 authority bindings.

    The two hooks are (1) the V1 reporting-only state-adjudicator repair and
    (2) the separately versioned replay-equivalence target verifier. No R8
    execution-input authority assignment is replaced or removed.
    """
    required = {
        "namespace anchor": ROUTER_ANCHOR,
        "routed adjudicator source": ROUTED_SOURCE_MARKER,
        "R8 pretarget authority binding": R8_PRETARGET_MARKER,
        "R8 preadjudication authority binding": R8_PREADJUDICATION_MARKER,
    }
    for label, marker in required.items():
        if router_source.count(marker) != 1:
            _fail(f"expected exactly one {label}")
    if not (router_source.index(ROUTED_SOURCE_MARKER)
            < router_source.index(ROUTER_ANCHOR)
            < router_source.index(R8_PRETARGET_MARKER)
            < router_source.index(R8_PREADJUDICATION_MARKER)):
        _fail("Stage-3 R8 router ordering changed")
    injected = (
        ROUTER_ANCHOR
        + "\n    namespace['adjudicate_donor_table_non_authoritative'] = _recovery_state_adjudicator"
        + "\n    namespace['verify_target_v2_against_raw'] = _recovery_target_verifier"
    )
    return router_source.replace(ROUTER_ANCHOR, injected, 1)


def derive_stage3_run_source(run_source: str) -> str:
    """Point Stage 3's tail freeze at the derived chain. One declared change."""
    if run_source.count(FREEZE_ANCHOR) != 1:
        _fail("expected exactly one Stage-3 tail-freeze module resolution, "
              "found %d" % run_source.count(FREEZE_ANCHOR))
    return run_source.replace(FREEZE_ANCHOR, FREEZE_REPLACEMENT, 1)


def derive_freeze_module(target_verifier: Callable[..., Any]) -> types.SimpleNamespace:
    """The frozen tail-freeze chain, resolving the equivalence verifier.

    Each function is exec'd verbatim from its own source into a namespace where
    only `verify_target_v2_against_raw` differs, so no frozen module is edited
    and no call site is rewritten. The chain wires itself because each function
    calls the next through module globals.
    """
    _, stage2a, _ = _deps()
    tail_mod = stage2a._frozen("t0_tail_authority_v1")
    freeze_mod = stage2a._frozen("t0_canonical_freeze_v1")

    tail_namespace = dict(tail_mod.__dict__)
    tail_namespace["verify_target_v2_against_raw"] = target_verifier
    for name in TAIL_CHAIN_FUNCTIONS:
        source = inspect.getsource(getattr(tail_mod, name))
        exec(compile(source, "<recovery-v2:%s>" % name, "exec"), tail_namespace)

    freeze_namespace = dict(freeze_mod.__dict__)
    freeze_namespace["freeze_tail_authority"] = tail_namespace[
        "freeze_tail_authority"]
    entry = "freeze_tail_after_discovery_authority"
    exec(compile(inspect.getsource(getattr(freeze_mod, entry)),
                 "<recovery-v2:%s>" % entry, "exec"), freeze_namespace)

    # `run` uses this module for exactly one call, so the shim carries exactly
    # that one function rather than impersonating the module.
    return types.SimpleNamespace(**{entry: freeze_namespace[entry]})


def verify_replay_decision(committed: dict[str, Any],
                           recomputed: dict[str, Any]) -> dict[str, Any]:
    """Exact terminals/discrete statistics; tight tolerance only for 3 floats.

    Inherited unchanged by V2, so this is identical under either policy; routed
    through the active one so the report cannot claim an identity it did not use.
    """
    return active_policy().compare_decision_equivalence(committed, recomputed)


def build_payload(decision: dict[str, Any], target_report: dict[str, Any],
                  decision_report: dict[str, Any],
                  repair_report: dict[str, Any]) -> dict[str, Any]:
    composition = decision.get("state_composition")
    measurements = decision.get("state_measurements")
    if composition is None or not measurements:
        _fail("the reporting repair did not surface both sensitivity families")
    if target_report.get("verified") is not True:
        _fail("target replay-equivalence was not verified")
    if decision_report.get("equivalent") is not True:
        _fail("decision replay-equivalence was not verified")
    return {
        "schema": "JEPA_T0_V20_RECOVERED_SENSITIVITY_STATISTICS_V2",
        "replay_equivalence_policy": policy_identity(),
        # The committed null_t is a truncated serialized representation, not the
        # full 9,999-value array, so no full-null equality is claimed here.
        "null_representation_scope": (
            "Only the stored truncated representation of state_primary.null_t "
            "is checked. The permutation count and every decision-relevant "
            "p-value are compared exactly."),
        # Recorded because the whole reason a tolerant replay was needed is
        # that no earlier T0 summary said which arithmetic produced the frozen
        # bytes. A replay report without its own stack would repeat the hole.
        "numeric_environment": numeric_environment.numeric_environment(),
        "what": (
            "Reporting-only recovery of state composition and measurement "
            "sensitivity statistics omitted from the committed V20 decision."
        ),
        "training_authorized": False,
        "historical_bit_exact_verifier_modified": False,
        "model_changed": False,
        "decision_procedure_changed": False,
        "reporting_surface_changed": True,
        "endpoint_altered": False,
        "nuisance_design_altered": False,
        "donor_roles_altered": False,
        "discovery_fit_recomputed_for_replay": True,
        "discovery_target_changed": False,
        "ridge_grid_widened": False,
        "adjudication_rule_altered": False,
        "reporting_repair": repair_report,
        "target_replay_equivalence": target_report,
        "decision_replay_equivalence": decision_report,
        "replay_reproduces_committed_decision_under_frozen_equivalence_policy": True,
        "state_terminal": decision["state_terminal"],
        "tail_terminal": decision["tail_terminal"],
        "state_primary": decision["state_primary"],
        "state_composition": composition,
        "state_measurements": measurements,
        "sensitivity_directional_alpha": 0.05,
    }


def _repaired_router_with_replay() -> tuple[Callable[..., Any], list[dict[str, Any]], dict[str, Any]]:
    """Build Stage-3's R8 router with two scoped recovery namespace bindings."""
    v1, stage2a, stage3 = _deps()

    original, repaired_source = v1.repaired_state_adjudicator_source()
    repair_report = v1.verify_repair(original, repaired_source)
    frozen_v1 = stage2a._frozen("t0_adjudicator_v1")
    v1_namespace = dict(frozen_v1.__dict__)
    exec(compile(repaired_source, "<recovery-v2:adjudicate_donor_table>", "exec"),
         v1_namespace)
    repaired_function = v1_namespace["adjudicate_donor_table_non_authoritative"]

    target_reports: list[dict[str, Any]] = []
    # Filled before the gates are applied, so it survives a STOP.
    full_reports: list[dict[str, Any]] = []

    def target_verifier(target_dir, **kwargs: Any):
        report = active_policy().verify_target_v2_replay_equivalent(
            target_dir, report_sink=full_reports, **kwargs)
        target_reports.append(report)
        return report

    freeze_module = derive_freeze_module(target_verifier)

    original_router = inspect.getsource(stage3._adjudicator_through_r8)
    routed_source = derive_r8_router_source(original_router)
    router_namespace = dict(stage3.__dict__)
    router_namespace["_recovery_state_adjudicator"] = repaired_function
    router_namespace["_recovery_target_verifier"] = target_verifier
    exec(compile(routed_source, "<recovery-v2:_adjudicator_through_r8>", "exec"),
         router_namespace)
    return (router_namespace["_adjudicator_through_r8"], target_reports,
            repair_report, freeze_module, full_reports)


def _run_with_repair(**kwargs: Any) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Run Stage-3 source with the scoped recovery routing.

    Both target-verifier call sites must have gone through the equivalence
    verifier. If either had fallen through to the frozen bit-exact verifier the
    run would have stopped there, so the count is what proves the routing held.
    """
    _, _, stage3 = _deps()
    router, target_reports, repair_report, freeze_module, full_reports = (
        _repaired_router_with_replay())
    namespace = dict(stage3.__dict__)
    namespace["_adjudicator_through_r8"] = router
    namespace["_recovery_freeze_module"] = freeze_module
    routed_run = derive_stage3_run_source(inspect.getsource(stage3.run))
    exec(compile(routed_run, "<recovery-v2:run>", "exec"), namespace)
    try:
        record = namespace["run"](**kwargs)
    except replay.ReplayEquivalenceError as error:
        # A STOP is a publishable outcome, so the evidence gathered before the
        # gate refused is carried out rather than lost with the traceback.
        raise ReplayStopped(str(error), full_reports, repair_report) from error
    if len(target_reports) != EXPECTED_TARGET_REPLAYS:
        _fail("expected %d target replay-equivalence verifications, observed %d"
              % (EXPECTED_TARGET_REPLAYS, len(target_reports)))
    unverified = [i for i, r in enumerate(target_reports)
                  if r.get("verified") is not True]
    if unverified:
        _fail("target replay-equivalence not verified at call sites %r"
              % unverified)
    return record, target_reports, repair_report


def recover(*, outdir: Path, committed_decision: Path,
            log=print, **stage3_kwargs: Any) -> dict[str, Any]:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%6.1fs] %s" % (time.time() - started, message))

    committed = json.loads(Path(committed_decision).read_text(encoding="utf-8"))
    stamp("replaying Stage 3 with scoped reporting repair + replay-equivalence target verifier")
    try:
        record, target_reports, repair_report = _run_with_repair(
            outdir=Path(outdir), log=lambda m: None, **stage3_kwargs)
    except ReplayStopped as stopped:
        report = build_stop_report(stopped.reason, stopped.full_reports,
                                   stopped.repair_report)
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / EQUIVALENCE_REPORT_FILE
        with io.open(path, "w", encoding="utf-8", newline=chr(10)) as handle:
            handle.write(json.dumps(report, indent=2, sort_keys=True,
                                    default=str) + chr(10))
        stamp("STOP: %s" % stopped.reason)
        stamp("published the complete equivalence report to %s" % path)
        raise
    target_report = {
        "verified": all(r.get("verified") is True for r in target_reports),
        "call_sites": len(target_reports),
        "expected_call_sites": EXPECTED_TARGET_REPLAYS,
        "reports": target_reports,
        "equivalence_schema": target_reports[0]["equivalence_schema"],
    }
    decision = record["decision"]

    decision_report = verify_replay_decision(committed, decision)
    stamp("target and decision replay-equivalence verified")
    payload = build_payload(decision, target_report, decision_report, repair_report)

    out = Path(outdir) / RECOVERY_FILE
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    stamp("wrote %s" % out)
    return payload


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--policy-version", choices=POLICY_VERSIONS,
                   default=DEFAULT_POLICY_VERSION,
                   help="frozen replay-equivalence policy identity to apply")
    for name in ("outdir", "readiness-pkg", "stage2a-pkg", "discovery-pkg",
                 "role-pkg", "at8-pkg", "age-sex-pkg", "immune-pkg",
                 "family-pkg", "technical-pkg", "tc-pkg", "stage3-prep-pkg",
                 "population-pkg", "pathology-source", "store", "membership",
                 "feature-split", "committed-decision"):
        p.add_argument("--%s" % name, required=True, type=Path)
    a = p.parse_args(argv)
    select_policy(a.policy_version)
    payload = recover(
        outdir=a.outdir, committed_decision=a.committed_decision,
        readiness_pkg=a.readiness_pkg, stage2a_pkg=a.stage2a_pkg,
        discovery_pkg=a.discovery_pkg, role_pkg=a.role_pkg, at8_pkg=a.at8_pkg,
        age_sex_pkg=a.age_sex_pkg, immune_pkg=a.immune_pkg,
        family_pkg=a.family_pkg, technical_pkg=a.technical_pkg,
        tc_pkg=a.tc_pkg, stage3_prep_pkg=a.stage3_prep_pkg,
        population_pkg=a.population_pkg, pathology_source=a.pathology_source,
        store=a.store, membership=a.membership,
        feature_split=a.feature_split)
    print(json.dumps({
        "state_composition": payload["state_composition"],
        "state_measurements": payload["state_measurements"],
    }, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
