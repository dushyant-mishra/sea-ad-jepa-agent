"""Author-side self-check of the private-snapshot repair (not an independent review).

Run from the repair worktree root. Synthetic DEVELOPMENT only.
"""
import os
import sys
import types

repo = os.getcwd()
sys.path.insert(0, repo)
_m = types.ModuleType("tests")
_m.__path__ = [os.path.join(repo, "tests")]
sys.modules["tests"] = _m

from scripts.v5.td_unified import challenge_custody_v1 as c  # noqa: E402

RESULTS = []
M1 = "1" * 64
HIDDEN = b"hidden"


def t(name, fn, expect_refusal):
    try:
        out = fn()
        refused, detail = False, out
    except Exception as exc:  # noqa: BLE001
        refused, detail = True, f"{type(exc).__name__}: {str(exc)[:150]}"
    ok = refused == expect_refusal
    RESULTS.append(ok)
    print(f"{'OK  ' if ok else 'BAD '} {name} -> {'REFUSED' if refused else 'ACCEPTED'}: {ascii(str(detail))[:200]}")


def deps():
    d = dict(task2_manifest_sha="1" * 64, task3_registry_sha="2" * 64, registry_unit_identities=(("G8", "3" * 64),),
             producer_actor_identity="4" * 64, executor_actor_identity="5" * 64, controller_actor_identity="6" * 64,
             adjudicator_actor_identity="7" * 64, realization_schema_sha="a" * 64, challenge_family_sha="c" * 64,
             adjudication_contract_sha="d" * 64, multiplicity_policy_sha="e" * 64, publication_policy_sha="f" * 64,
             genesis_ledger_identity="0" * 64, authority_scope="UNIT:G8",
             authority_restrictions=("NO_TRAINING_AUTHORITY",), qualification_budget=2)
    d.update(c.development_fixture_generator_identities())
    return d


def sealed(cid):
    a = c.create_campaign(cid, deps(), barrier_status=None, namespace="DEVELOPMENT")
    a, d = c.seal_definition(a, family="fixture", hidden_spec=HIDDEN)
    rows = c.generate_development_fixture_rows(a, d, hidden_spec=HIDDEN)
    a, s = c.seal_realization_set(a, d, rows, budget=2)
    return a, d, s


def plain_value_mutation():
    a, d, s = sealed("mp-plain")
    a, e = c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)
    object.__setattr__(e, "realization_id", "r1")  # plain str, different value
    return c.freeze_method_output(a, e, output_sha256="a" * 64)[0].state.value


def token_swap():
    a, d, s = sealed("mp-token-a")
    b, _, _ = sealed("mp-token-b")
    object.__setattr__(a, "_lifecycle_token", object.__getattribute__(b, "_lifecycle_token"))
    return c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)


def namespace_flip_guard():
    a, d, s = sealed("mp-namespace")
    object.__setattr__(a, "namespace", "FINAL")
    return c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)


def private_never_returned():
    a, d, s = sealed("mp-private")
    a2, e = c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)
    tok = object.__getattribute__(a2, "_lifecycle_token")
    leaks = [
        c._LIFECYCLE_PRIVATE[tok] is a2,
        c._ISSUED_DEFINITIONS[tok][1] is d,
        c._ISSUED_REALIZATION_SETS[tok][1] is s,
        any(priv is e for _, priv in c._ISSUED_EXPOSURES[tok]),
        c._LIFECYCLE_PRIVATE[tok].dependencies is a2.dependencies,
    ]
    if any(leaks):
        raise AssertionError(f"private object returned to caller: {leaks}")
    return "no private object or private dependency dict was returned"


def stale_handle_after_advance():
    a, d, s = sealed("mp-stale")
    c.issue_exposure(a, s, realization_id="r0", method_scientific_identity=M1)
    return c.issue_exposure(a, s, realization_id="r1", method_scientific_identity=M1)


t("plain-value mutation of an issued exposure", plain_value_mutation, True)
t("swap another campaign's lifecycle token into a handle", token_swap, True)
t("flip namespace on an authentic handle", namespace_flip_guard, True)
t("private snapshots never returned to the caller", private_never_returned, False)
t("stale public handle after an advance", stale_handle_after_advance, True)
print(f"SUMMARY: {sum(RESULTS)}/{len(RESULTS)} expected; BAD={len(RESULTS) - sum(RESULTS)}")
