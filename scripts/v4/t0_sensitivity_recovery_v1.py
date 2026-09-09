#!/usr/bin/env python3
"""Recover the state sensitivity statistics the decision record omitted.

`T0_V20_ADJUDICATION_DECISION.json` carries `state_primary` in full but no
sensitivity statistics at all. The terminal
`BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL` can only be reached when the
composition sensitivity and every measurement sensitivity are positive at
`sensitivity_directional_alpha` = 0.05, so the reader knows they cleared but
cannot see by how much, and cannot check the adjudication rule against the
numbers it was applied to.

This is a reporting defect in the frozen code, not a design choice.
`adjudicate_donor_table_non_authoritative` defines `comp` -- the composition
sensitivity, the nuisance design plus IMMUNE_FRACTION -- and `measurements` --
Q_DEPTH+Q_DETECT, plus one reduced model per registered technical block -- and
passes both to `decide_state`, which produces the state terminal from them.

Of the eight returns in that function, one (line 62) precedes the definitions
and correctly cannot carry them, and two (lines 73 and 103) do carry them. Five
drop them: lines 76, 78, 86, 94 and 98. Every one of the five sits after the
terminal those statistics decided, and every one concerns the *tail* while
discarding the *state* sensitivities. That the two sibling paths include both
keys is what makes this an inconsistency rather than an intended omission. This
run took the QC path at line 78.

How the numbers are recovered. The frozen function is not edited. A repaired
copy is derived from its source by textual substitution -- the same technique
used for the corrective run_update variants and the R8 loaders -- adding
`state_composition` and `state_measurements` to the two deficient returns and
changing nothing else. The repaired function is injected into the adjudicator's
execution namespace exactly the way R8's repaired verifiers already are, so
nothing on the frozen module is rebound.

Why this is a replay and not a new result. The frozen procedure is unchanged:
same endpoint, same donor roles, same nuisance design, same thresholds, same
discovery object, same adjudication rule. The recovery is refused unless the
recomputed `state_primary` reproduces the committed decision **exactly**, field
by field, along with both terminals. If any of that differs, the run is not a
replay of the frozen procedure and its sensitivities would not be the ones that
decided the recorded terminal, so nothing is written.

This reads the confirmation numeric AT8 values, under the same Stage 3
authorization that opened them, to recompute statistics that were already
computed in that run.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import inspect
import io
import json
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_execution_input_authority_v2 as v2  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402
import t0_stage3_confirmation_v1 as stage3  # noqa: E402

STOP = "STOP_T0_SENSITIVITY_RECOVERY_REFUSED"

DECISION_FILE = "T0_V20_ADJUDICATION_DECISION.json"
RECOVERY_FILE = "T0_V20_RECOVERED_SENSITIVITY_STATISTICS.json"

ADDED_KEYS = ("'state_composition':comp,"
              "'state_measurements':dict(zip(measurement_names,measurements)),")

# A return is deficient when it can carry the sensitivities and does not. The
# rule is stated rather than the five call sites enumerated, so it cannot match
# the one return that precedes the definitions -- substituting there would raise
# NameError rather than recover anything.
RETURN_MARKER = "return {'state_terminal':"
INSERT_AFTER = "'state_primary':primary,"
DEFINITION_MARKER = "comp=_run("
EXPECTED_DEFICIENT = 5


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def repaired_state_adjudicator_source() -> tuple[str, str]:
    """The frozen function's source, and the repaired copy of it."""
    frozen_v1 = stage2a._frozen("t0_adjudicator_v1")
    original = inspect.getsource(
        frozen_v1.adjudicate_donor_table_non_authoritative)
    lines = original.splitlines(keepends=True)

    defined_at = [i for i, line in enumerate(lines)
                  if DEFINITION_MARKER in line]
    if len(defined_at) != 1:
        _fail("expected one definition of comp, found %d" % len(defined_at))
    defined = defined_at[0]

    repaired_lines = list(lines)
    changed = 0
    for index, line in enumerate(lines):
        if RETURN_MARKER not in line or index < defined:
            continue
        if "'state_composition'" in line:
            continue
        if line.count(INSERT_AFTER) != 1:
            _fail("deficient return on line %d has no single %r to anchor to"
                  % (index + 1, INSERT_AFTER))
        repaired_lines[index] = line.replace(
            INSERT_AFTER, INSERT_AFTER + ADDED_KEYS, 1)
        changed += 1
    if changed != EXPECTED_DEFICIENT:
        _fail("expected %d deficient returns, repaired %d"
              % (EXPECTED_DEFICIENT, changed))
    return original, "".join(repaired_lines)


def verify_repair(original: str, repaired: str) -> dict[str, Any]:
    """Five changed lines, each adding only the two omitted keys.

    Checked on the derived text. A substitution that landed anywhere else would
    still produce a runnable function, and its output would look like a faithful
    recovery.
    """
    diff = list(difflib.unified_diff(original.splitlines(),
                                     repaired.splitlines(),
                                     "frozen", "repaired", lineterm="", n=0))
    added = [line[1:] for line in diff
             if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in diff
               if line.startswith("-") and not line.startswith("---")]
    if len(added) != EXPECTED_DEFICIENT or len(removed) != EXPECTED_DEFICIENT:
        _fail("expected %d changed lines, got +%d/-%d"
              % (EXPECTED_DEFICIENT, len(added), len(removed)))
    for before, after in zip(removed, added):
        if after.replace(ADDED_KEYS, "") != before:
            _fail("a changed line differs by more than the two omitted keys")
    # An earlier version asserted here that the frozen source did not already
    # contain the added text. That is false by construction and the check was
    # wrong: the two sound returns at lines 73 and 103 carry exactly this text,
    # which is where its spelling comes from. What is worth checking instead is
    # that the repaired copy is still the same function and still parses.
    tree = ast.parse(textwrap.dedent(repaired))
    functions = [node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)]
    if len(functions) != 1:
        _fail("the repaired source defines %d functions, expected 1"
              % len(functions))
    if functions[0].name != "adjudicate_donor_table_non_authoritative":
        _fail("the repaired source defines %r" % functions[0].name)
    return {"changed_lines": EXPECTED_DEFICIENT,
            "repaired_function": functions[0].name,
            "added_keys": ["state_composition", "state_measurements"]}


def _repaired_router() -> Callable[..., Any]:
    """Stage 3's R8 router, with the repaired state adjudicator in scope.

    Derived from `stage3._adjudicator_through_r8` by one substitution, so the
    routing itself -- which is what carries the R8 repair -- is not retyped.
    """
    original, repaired = repaired_state_adjudicator_source()
    verify_repair(original, repaired)

    frozen_v1 = stage2a._frozen("t0_adjudicator_v1")
    v1_namespace = dict(frozen_v1.__dict__)
    exec(compile(repaired, "<recovery:adjudicate_donor_table>", "exec"),
         v1_namespace)
    repaired_function = v1_namespace["adjudicate_donor_table_non_authoritative"]

    anchor = "    namespace = dict(frozen.__dict__)"
    router_source = inspect.getsource(stage3._adjudicator_through_r8)
    if router_source.count(anchor) != 1:
        _fail("could not locate the namespace anchor in the R8 router")
    router_source = router_source.replace(
        anchor,
        anchor + "\n    namespace['adjudicate_donor_table_non_authoritative']"
                 " = _recovery_state_adjudicator", 1)
    router_namespace = dict(stage3.__dict__)
    router_namespace["_recovery_state_adjudicator"] = repaired_function
    exec(compile(router_source, "<recovery:_adjudicator_through_r8>", "exec"),
         router_namespace)
    return router_namespace["_adjudicator_through_r8"]


def _run_with_repair(**kwargs: Any) -> dict[str, Any]:
    """Stage 3's own `run`, resolving the repaired router. Nothing else changes."""
    namespace = dict(stage3.__dict__)
    namespace["_adjudicator_through_r8"] = _repaired_router()
    exec(compile(inspect.getsource(stage3.run), "<recovery:run>", "exec"),
         namespace)
    return namespace["run"](**kwargs)


def _identical(recomputed: Any, committed: Any) -> bool:
    """Compare as the decision file stores them: JSON-serialised, `default=str`."""
    return (json.loads(json.dumps(recomputed, default=str, sort_keys=True))
            == json.loads(json.dumps(committed, default=str, sort_keys=True)))


def recover(*, outdir: Path, committed_decision: Path,
            log=print, **stage3_kwargs: Any) -> dict[str, Any]:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%6.1fs] %s" % (time.time() - started, message))

    committed = json.loads(committed_decision.read_text(encoding="utf-8"))
    original, repaired = repaired_state_adjudicator_source()
    repair = verify_repair(original, repaired)
    stamp("repair verified: %d changed lines, adding %s"
          % (repair["changed_lines"], ", ".join(repair["added_keys"])))

    stamp("replaying the frozen Stage 3 adjudication with the repair")
    record = _run_with_repair(outdir=outdir, log=lambda m: None,
                              **stage3_kwargs)
    decision = record["decision"]
    stamp("replay returned terminal %s" % decision["state_terminal"])

    # The replay is only a replay if it reproduces what was committed.
    mismatches = []
    for field in ("state_terminal", "tail_terminal"):
        if decision.get(field) != committed.get(field):
            mismatches.append("%s: %r != %r"
                              % (field, decision.get(field), committed.get(field)))
    if not _identical(decision.get("state_primary"),
                      committed.get("state_primary")):
        mismatches.append("state_primary does not reproduce")
    if mismatches:
        _fail("the replay did not reproduce the committed decision; the "
              "recovered sensitivities would not be the ones that decided the "
              "recorded terminal. " + "; ".join(mismatches))
    stamp("state_primary and both terminals reproduce the committed decision")

    composition = decision.get("state_composition")
    measurements = decision.get("state_measurements")
    if composition is None or not measurements:
        _fail("the repair did not surface the sensitivities")

    payload = {
        "schema": "JEPA_T0_V20_RECOVERED_SENSITIVITY_STATISTICS_V1",
        "what": "The state composition and measurement sensitivity statistics "
                "that the frozen adjudicator computed and the decision record "
                "omitted.",
        "why_they_were_missing":
            "Five of the eight return paths in "
            "adjudicate_donor_table_non_authoritative drop state_composition "
            "and state_measurements: lines 76, 78, 86, 94 and 98. Every one "
            "sits after the state terminal those statistics decided, and every "
            "one concerns the tail while discarding the state sensitivities. "
            "This run took the QC path at line 78.",
        "recovered_by": "A repaired copy of the frozen function, derived by "
                        "textual substitution adding only the two omitted keys "
                        "to those five returns, injected into the "
                        "adjudicator's namespace. The frozen module is not "
                        "edited or rebound.",
        "replay_reproduces_committed_decision": True,
        "state_terminal": decision["state_terminal"],
        "tail_terminal": decision["tail_terminal"],
        "state_primary": decision["state_primary"],
        "state_composition": composition,
        "state_measurements": measurements,
        "sensitivity_directional_alpha": 0.05,
        "procedure_unchanged": {
            "endpoint_altered": False, "nuisance_design_altered": False,
            "donor_roles_altered": False, "discovery_refit": False,
            "ridge_grid_widened": False, "adjudication_rule_altered": False,
        },
    }
    out = Path(outdir) / RECOVERY_FILE
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    stamp("wrote %s" % out)
    return payload


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("outdir", "readiness-pkg", "stage2a-pkg", "discovery-pkg",
                 "role-pkg", "at8-pkg", "age-sex-pkg", "immune-pkg",
                 "family-pkg", "technical-pkg", "tc-pkg", "stage3-prep-pkg",
                 "population-pkg", "pathology-source", "store", "membership",
                 "feature-split", "committed-decision"):
        p.add_argument("--%s" % name, required=True, type=Path)
    a = p.parse_args(argv)
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
    print()
    print(json.dumps({"state_composition": payload["state_composition"],
                      "state_measurements": payload["state_measurements"]},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
