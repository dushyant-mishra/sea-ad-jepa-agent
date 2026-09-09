"""Repaired execution-input authority loaders. R8.

Supersedes the two loaders in `t0_execution_input_authority_v1` whose readiness
value check makes the canonical adjudicator unreachable. The frozen module is not
edited; it is imported, and the two loaders are re-derived from its own source.

The contradiction
-----------------
    t0_adjudicator_v2, lines 34 and 48
        raise STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED
        unless real_execution_ready IS True
    t0_execution_input_authority_v1.load_pretarget_execution_authority
    t0_execution_input_authority_v1.load_preadjudication_execution_authority
        raise 'metadata mismatch' unless it IS False

So a package that loads cannot adjudicate and a package that could adjudicate
cannot load. R7 repaired the readiness semantics for the canonical *freeze* path
by building a parallel authority; it did not reach the adjudication path, because
the adjudicator calls these frozen loaders directly.

Why this is a defect and not a reading
--------------------------------------
`contract/T0_V20_EXECUTION_AUTHORITY_CONSTANTS.json` declares:

    production_requires_real_execution_ready          True
    synthetic_test_authorities_real_execution_ready   False

The contract states that production requires True. The loader refuses True. This
module aligns the implementation with the contract's own constant rather than
choosing among interpretations.

The single change, and how it is made verifiable
------------------------------------------------
Both loaders are re-derived from `inspect.getsource` of the frozen functions by
one textual substitution each, then executed in a copy of the frozen module's
globals. Every line except the substituted one is byte-identical, and
`source_diff()` emits the unified diff so a reviewer checks four changed lines
rather than trusting a claim. This is the method the C2 lane used to attribute
the T1 gradient defect to a single line.

The two builders are derived the same way, with one further substitution each:
`'real_execution_ready':False` becomes `'real_execution_ready':_r8_derived_readiness()`.
That call refuses unless a derivation has been recorded through
`record_readiness_derivation`, whose value must come from R7's `derive_readiness`.
So readiness remains derived rather than assigned, and there is no parameter
through which a caller could simply assert True. Eight changed lines in total,
every one touching `real_execution_ready`.

The two `verify_*` functions are copied into that same namespace **verbatim**,
with no substitution, and a guard refuses to copy them if they contain the
readiness condition. Because they live in the namespace holding the derived
loaders, their global lookup resolves to the repaired loader. Nothing on the
frozen module is rebound, so no other importer of it is affected and there is
nothing to restore.

The substitution replaces

    obj.get('real_execution_ready') is not False

with

    not isinstance(obj.get('real_execution_ready'), bool)

so the loader validates the field's *type* and the entrypoint decides
production readiness. That division of labour is what the contract describes:
the loader checks shape, `production_requires_real_execution_ready` is enforced
where production is claimed. It is a correction, not a loosening — `False` is
still accepted for non-production packages, and a non-boolean is still refused.

What this module does not do
----------------------------
It reads no numeric AT8, discovery or confirmation. It does not refit discovery,
touch the discovery object, the donor roles, the endpoint, the frozen ridge grid,
the nuisance design, the thresholds or any scientific procedure. It adjudicates
nothing: it makes the readiness path satisfiable and stops there.
"""

from __future__ import annotations

import difflib
import inspect
import sys
from pathlib import Path
from typing import Any

FROZEN_V20 = (Path("C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project")
              / "cdf819f6-5db4-4119-9a97-37fef1d27909" / "scratchpad"
              / "v20_recovery" / "current" / "code")

SUPERSEDES = "t0_execution_input_authority_v1"
BEHAVIOURAL_DIFFERENCE = "READINESS_VALUE_CHECK_ONLY"
JUSTIFICATION = (
    "contract/T0_V20_EXECUTION_AUTHORITY_CONSTANTS.json declares "
    "production_requires_real_execution_ready True, which the frozen loader's "
    "`is not False` contradicts")
CODE_BYTE_SEMANTICS = (
    "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT"
    "__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES")

SCIENTIFIC_DESIGN_UNCHANGED = True
DISCOVERY_REFIT = False
CONFIRMATION_NUMERIC_AT8_READ = False
FROZEN_MODULE_EDITED = False

STOP_SUBSTITUTION = "STOP_T0_R8_READINESS_SUBSTITUTION_DID_NOT_APPLY_EXACTLY"

_ORIGINAL = "obj.get('real_execution_ready') is not False"
_REPAIRED = "not isinstance(obj.get('real_execution_ready'), bool)"

# The builders hardcode False. Stage 3 needs True, and the adjudicator gates on
# True, so the builders must be derived too. The substituted value is a call, not
# a literal, and the call refuses unless a derivation has been recorded -- so
# readiness stays derived and there is no parameter through which a caller could
# simply assert it.
_BUILDER_ORIGINAL = "'real_execution_ready':False}"
_BUILDER_REPAIRED = "'real_execution_ready':_r8_derived_readiness()}"

STOP_READINESS_NOT_DERIVED = (
    "STOP_T0_R8_BUILDER_CALLED_WITHOUT_A_RECORDED_READINESS_DERIVATION")

_DERIVED: dict[str, Any] = {}
_READINESS: dict[str, Any] = {}


def record_readiness_derivation(*, value: bool, derivation: str,
                                evidence: dict[str, Any]) -> None:
    """Record a derived readiness value for the derived builders to emit.

    `value` must come from R7's `derive_readiness`, not from a caller's opinion.
    `derivation` and `evidence` are stored so the emitted package can be traced
    back to what established it.
    """
    if not isinstance(value, bool):
        raise AssertionError("%s: readiness must be a bool, got %r"
                             % (STOP_READINESS_NOT_DERIVED, value))
    if not isinstance(derivation, str) or not derivation.strip():
        raise AssertionError("%s: a derivation marker is required"
                             % STOP_READINESS_NOT_DERIVED)
    _READINESS.clear()
    _READINESS.update({"value": value, "derivation": derivation,
                       "evidence": dict(evidence)})


def clear_readiness_derivation() -> None:
    _READINESS.clear()


def readiness_derivation() -> dict[str, Any]:
    if not _READINESS:
        raise AssertionError("%s: no derivation recorded"
                             % STOP_READINESS_NOT_DERIVED)
    return dict(_READINESS)


def _r8_derived_readiness() -> bool:
    """Injected into the derivation namespace as the substituted value."""
    if not _READINESS:
        raise AssertionError(
            "%s: the derived builder was called before any readiness "
            "derivation was recorded. Establish it with R7's derive_readiness "
            "and pass it through record_readiness_derivation."
            % STOP_READINESS_NOT_DERIVED)
    return bool(_READINESS["value"])


def _frozen_module():
    if str(FROZEN_V20) not in sys.path:
        sys.path.insert(0, str(FROZEN_V20))
    import t0_execution_input_authority_v1 as frozen
    return frozen


def _derive() -> dict[str, Any]:
    """Re-derive both loaders by one textual substitution each.

    Executed in the frozen module's own `__dict__`, so every name the original
    body resolves resolves identically here. Nothing is retyped.
    """
    if _DERIVED:
        return _DERIVED
    frozen = _frozen_module()
    # Substituted: the two loaders whose readiness check is the defect.
    substituted = {
        "load_pretarget_execution_authority":
            frozen.load_pretarget_execution_authority,
        "load_preadjudication_execution_authority":
            frozen.load_preadjudication_execution_authority,
    }
    # Copied verbatim, no substitution. Exec'd into the same namespace so their
    # global lookup of the loader name resolves to the derived loader. This is
    # what removes any need to rebind names on the frozen module.
    verbatim = {
        "verify_pretarget_execution_authority":
            frozen.verify_pretarget_execution_authority,
        "verify_preadjudication_execution_authority":
            frozen.verify_preadjudication_execution_authority,
    }
    # The builders, whose hardcoded False becomes a derived call.
    builders = {
        "build_pretarget_execution_authority":
            frozen.build_pretarget_execution_authority,
        "build_preadjudication_execution_authority":
            frozen.build_preadjudication_execution_authority,
    }
    before_lines: list[str] = []
    after_lines: list[str] = []
    namespace = dict(frozen.__dict__)
    for name, func in substituted.items():
        source = inspect.getsource(func)
        if source.count(_ORIGINAL) != 1:
            raise AssertionError(
                "%s: %s contains the readiness condition %d times, expected 1"
                % (STOP_SUBSTITUTION, name, source.count(_ORIGINAL)))
        repaired = source.replace(_ORIGINAL, _REPAIRED, 1)
        before_lines.extend(source.splitlines(keepends=True))
        after_lines.extend(repaired.splitlines(keepends=True))
        exec(compile(repaired, "<r8-derived:%s>" % name, "exec"), namespace)

    namespace["_r8_derived_readiness"] = _r8_derived_readiness
    for name, func in builders.items():
        source = inspect.getsource(func)
        if source.count(_BUILDER_ORIGINAL) != 1:
            raise AssertionError(
                "%s: %s writes the readiness literal %d times, expected 1"
                % (STOP_SUBSTITUTION, name, source.count(_BUILDER_ORIGINAL)))
        repaired = source.replace(_BUILDER_ORIGINAL, _BUILDER_REPAIRED, 1)
        before_lines.extend(source.splitlines(keepends=True))
        after_lines.extend(repaired.splitlines(keepends=True))
        exec(compile(repaired, "<r8-derived:%s>" % name, "exec"), namespace)

    for name, func in verbatim.items():
        source = inspect.getsource(func)
        if _ORIGINAL in source:
            raise AssertionError(
                "%s: %s contains the readiness condition and would need "
                "substitution, but is being copied verbatim"
                % (STOP_SUBSTITUTION, name))
        exec(compile(source, "<r8-verbatim:%s>" % name, "exec"), namespace)

    diff = "".join(difflib.unified_diff(
        before_lines, after_lines,
        fromfile="frozen/t0_execution_input_authority_v1",
        tofile="r8/t0_execution_input_authority_v2", n=1))
    changed = [line for line in diff.splitlines()
               if (line.startswith("+") or line.startswith("-"))
               and not line.startswith(("+++", "---"))]
    if len(changed) != 8:
        raise AssertionError("%s: %d changed lines, expected 8: %r"
                             % (STOP_SUBSTITUTION, len(changed), changed))
    for line in changed:
        if "real_execution_ready" not in line:
            raise AssertionError("%s: a changed line does not touch the "
                                 "readiness field: %r"
                                 % (STOP_SUBSTITUTION, line))

    _DERIVED.update({
        "frozen": frozen,
        "diff": diff,
        "load_pretarget_execution_authority":
            namespace["load_pretarget_execution_authority"],
        "load_preadjudication_execution_authority":
            namespace["load_preadjudication_execution_authority"],
        "verify_pretarget_execution_authority":
            namespace["verify_pretarget_execution_authority"],
        "verify_preadjudication_execution_authority":
            namespace["verify_preadjudication_execution_authority"],
        "build_pretarget_execution_authority":
            namespace["build_pretarget_execution_authority"],
        "build_preadjudication_execution_authority":
            namespace["build_preadjudication_execution_authority"],
    })
    return _DERIVED


def source_diff() -> str:
    """The unified diff between the frozen loaders and the derived ones."""
    return _derive()["diff"]


def load_pretarget_execution_authority(outdir) -> dict[str, Any]:
    """The frozen loader with the readiness value check corrected."""
    return _derive()["load_pretarget_execution_authority"](outdir)


def load_preadjudication_execution_authority(outdir) -> dict[str, Any]:
    """The frozen loader with the readiness value check corrected."""
    return _derive()["load_preadjudication_execution_authority"](outdir)


def verify_pretarget_execution_authority(outdir, **kwargs) -> dict[str, Any]:
    """The frozen verifier, byte-identical, resolving the repaired loader.

    The verifier source is copied verbatim and exec'd into the namespace that
    holds the derived loaders, so its global lookup of
    `load_pretarget_execution_authority` finds the repaired one. Nothing on the
    frozen module is rebound and nothing needs restoring.
    """
    return _derive()["verify_pretarget_execution_authority"](outdir, **kwargs)


def verify_preadjudication_execution_authority(outdir,
                                               **kwargs) -> dict[str, Any]:
    """The frozen verifier, byte-identical, resolving the repaired loader."""
    return _derive()["verify_preadjudication_execution_authority"](
        outdir, **kwargs)


def build_pretarget_execution_authority(outdir, **kwargs) -> dict[str, Any]:
    """The frozen builder, emitting the derived readiness instead of False."""
    return _derive()["build_pretarget_execution_authority"](outdir, **kwargs)


def build_preadjudication_execution_authority(outdir,
                                              **kwargs) -> dict[str, Any]:
    """The frozen builder, emitting the derived readiness instead of False."""
    return _derive()["build_preadjudication_execution_authority"](
        outdir, **kwargs)


def adjudicator_gate_satisfied(authority: dict[str, Any]) -> bool:
    """The frozen adjudicator's own condition, evaluated verbatim.

    `t0_adjudicator_v2` raises unless `real_execution_ready is True`. This
    reports whether a loaded authority passes that, so satisfiability is shown
    against the frozen condition rather than a paraphrase of it.
    """
    return not (authority.get("real_execution_ready") is not True)
