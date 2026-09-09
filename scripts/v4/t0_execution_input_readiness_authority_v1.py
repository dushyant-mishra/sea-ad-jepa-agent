"""Repaired execution-input readiness authority for the real T0 run.

R7. The frozen V20 package cannot execute production T0, and the reason is a
contradiction rather than a missing input:

    t0_execution_input_authority_v1.build_pretarget_execution_authority
        writes real_execution_ready = False, always, and nothing in the frozen
        package ever writes True
    t0_execution_input_authority_v1.load_pretarget_execution_authority
        raises 'pretarget authority metadata mismatch' unless it IS False
    t0_canonical_freeze_v2._verified and t0_adjudicator_v2 (twice)
        raise STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED
        unless it IS True

A package that loads cannot run; a package that could run cannot load. All three
canonical conclusion entrypoints are gated on the unsatisfiable side.

This module re-freezes the readiness semantics. It does not edit the frozen
package, which stays read-only, and the R7 red suite keeps the frozen
contradiction demonstrable.

The repaired semantics
----------------------
`real_execution_ready = True` may exist only on a production execution-input
authority derived from verified Stage 1 parents plus explicit staged owner
authorization. `False` stays lawful for pre-run, test, fixture, candidate and
non-execution packages, and is refused for production canonical input.

Readiness is *derived*, never assigned:

    real_execution_ready = all_required_stage1_bindings_verified
                           AND staged_authorization_present
                           AND no_forbidden_gate_opened

Every conjunct is computed here from bindings checked against expectations
supplied from outside the package. A caller cannot assert readiness, and a
package cannot attest to its own identity: `assert_production_authority_lawful`
refuses expectations that are the package's own bindings object.

What this module does not do
----------------------------
It binds the AT8 endpoint identity and the pathology source digest. It never
parses a magnitude from that source, and `numeric_at8_value_read` is False in
every artifact it writes. It opens no DEV path, no SEALED path, no protected
population, and it changes no scientific design constant: the donor set, the role
split, the endpoint, the nuisance design, the Stage A rank criteria, the
technical-completeness semantics, the tail floor, the thresholds and the feature
set are all untouched.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "JEPA_T0_EXECUTION_INPUT_READINESS_AUTHORITY_V1"
NAMESPACE = "T0-EXECUTION-INPUT-READINESS-V1"
DOMAIN_TAG = "T0-EXECUTION-INPUT-READINESS-V1-TYPED-LENGTH-PREFIXED"

MEMBER = "T0_EXECUTION_INPUT_READINESS_AUTHORITY.json"
MANIFEST = "T0_EXECUTION_INPUT_READINESS_MANIFEST.csv"
ROOT_FILE = "T0_EXECUTION_INPUT_READINESS_PACKAGE_ROOT_SHA256.txt"
MEMBERS = (MEMBER, MANIFEST)

# --- the design, unchanged by this repair ----------------------------------
SCIENTIFIC_DESIGN_UNCHANGED = True
CONFIRMATION_DONORS = 18
DISCOVERY_DONORS = 28
INELIGIBLE_DONORS = 0
POPULATION_ROWS = 20_804
CANDIDATE_DONORS = 46

READINESS_DERIVATION = "VERIFIED_FROM_STAGE1_PARENT_CHAIN_AND_AUTHORIZATION"
READINESS_DERIVATION_NON_PRODUCTION = "NOT_DERIVED__NON_PRODUCTION_PACKAGE"
READINESS_DERIVATION_STATEMENT = (
    "real_execution_ready = all_required_stage1_bindings_verified "
    "AND staged_authorization_present AND no_forbidden_gate_opened")

PACKAGE_KIND_PRODUCTION = "PRODUCTION_EXECUTION_INPUT"
NON_PRODUCTION_KINDS = ("PRE_RUN", "TEST", "FIXTURE", "CANDIDATE",
                        "NON_EXECUTION")

ACCURATE_CODE_BYTE_SEMANTICS = (
    "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT"
    "__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES")
WAIVED_FALSE_CODE_BYTE_SEMANTICS = "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES"

STAGED_AUTHORIZATION_TOKEN = (
    "AUTHORIZE_ROLLING_REAL_T0_EXECUTION_WITH_FAIL_CLOSED_STAGE_GATES")
STAGED_AUTHORIZATION_SCOPE = (
    "REAL_T0_STAGED_EXECUTION_AUTHORIZED__DISCOVERY_FIRST"
    "__CONFIRMATION_AFTER_DISCOVERY_REPLAY")

# Gates that must be shut. A package claiming any of these was opened is
# refused, so readiness cannot coexist with a widened scope.
FORBIDDEN_GATES = ("dev_opened", "sealed_opened", "protected_populations_opened",
                   "teacher_student_training_begun",
                   "successor_u0_materialized", "td60_run",
                   "biological_sweeps_run")

# --- the nineteen bindings a production authority must carry ---------------
REQUIRED_BINDINGS = (
    "b2_population_raw_source_root_sha256",
    "b2_authority_package_root_sha256",
    "technical_completeness_root_sha256",
    "technical_completeness_package_root_sha256",
    "at8_availability_root_sha256",
    "at8_availability_package_root_sha256",
    "age_sex_root_sha256",
    "age_sex_package_root_sha256",
    "eligible_donor_root_sha256",
    "donor_role_root_sha256",
    "eligible_donor_package_root_sha256",
    "stage_a_preflight_root_sha256",
    "input_dependency_contract_root_sha256",
    "authorization_record_root_sha256",
    "at8_endpoint_identity",
    "pathology_source_sha256",
    "discovery_donor_set_sha256",
    "confirmation_donor_set_sha256",
    "code_byte_semantics_audit",
)

# The accepted Stage 1 values, frozen here so a production authority is checked
# against expectations that live in committed code rather than in the package
# being checked. This is the same anti-circularity rule R6 applied to the AT8 and
# age/sex parents.
ACCEPTED_BINDINGS: dict[str, Any] = {
    "b2_population_raw_source_root_sha256":
        "0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b",
    "b2_authority_package_root_sha256":
        "98eac4a68df7960e79739d236cf0febacdec52a33de76144b146dc29a5a64436",
    "technical_completeness_root_sha256":
        "360381dc7625386a58c1aa0b262de3e55e9835bc32808f86b663d944ec453470",
    "technical_completeness_package_root_sha256":
        "0164bccc76ad7ed9385de01fd0ab885dd80770afad0b94ee189e9084ee3cfe99",
    "at8_availability_root_sha256":
        "e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b",
    "at8_availability_package_root_sha256":
        "3f74fa833bc1838a50d92bf3f6bdb55e6eafdb10b489fbfff142a4240466fc5a",
    "age_sex_root_sha256":
        "95ed8f75a42368f3308cf794dbab3c651a4467756147a49a937c5a881e1cffff",
    "age_sex_package_root_sha256":
        "8212191a03f09d669a383be6a541b5ce3493b32c13608a76f197a88fa18ddf9b",
    "eligible_donor_root_sha256":
        "a5470b9f5389e0fa72b3ca51832c67d7419ed6447a85d6d979884b9fe1444f85",
    "donor_role_root_sha256":
        "799261f54de158f4c24c33a51a674611fe4e5e68509fcbbca681216470fe10bd",
    "eligible_donor_package_root_sha256":
        "7d372603cb4833a2cba02a047f6f3f3e4ef680ab0c730b8693ccbd958ddfafeb",
    "stage_a_preflight_root_sha256":
        "bf9ee518d59053b3fe446c258c2606f318077b2f179ad73c45c4c6346030df27",
    "input_dependency_contract_root_sha256":
        "deb63753212964966f53ecc76b047fcdbcab013c162e045314c86581dbb09969",
    "authorization_record_root_sha256":
        "504bc8ac50781f3df37290e8626c92be1f22a5a7a77a3d92dc8851e89252e623",
    "at8_endpoint_identity": "percent AT8 positive area_Grey matter",
    "pathology_source_sha256":
        "ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a",
    "discovery_donor_set_sha256":
        "4395fec74bcf7abf192d731db3c827fa25cfde1b5297db4203b041984a780d33",
    "confirmation_donor_set_sha256":
        "96514f847ca81a99b8d33316db8fe717a20f0f566fe5851259f7154b7e077b98",
    "code_byte_semantics_audit": "NO_NEW_FALSE_LABELS",
}

_DIGEST_BINDINGS = tuple(
    name for name in REQUIRED_BINDINGS
    if name.endswith("_sha256"))

STOP_BINDING_ABSENT = "STOP_T0_READINESS_REQUIRED_BINDING_ABSENT"
STOP_BINDING_MISMATCH = "STOP_T0_READINESS_BINDING_DOES_NOT_MATCH_ACCEPTED_VALUE"
STOP_DONOR_SET = "STOP_T0_READINESS_DONOR_SET_DIGEST_MISMATCH"
STOP_ENDPOINT = "STOP_T0_READINESS_ENDPOINT_OR_PATHOLOGY_SOURCE_MISMATCH"
STOP_BYTE_SEMANTICS = "STOP_T0_READINESS_FALSE_BYTE_SEMANTICS_LABEL"
STOP_NOT_READY = "STOP_T0_READINESS_PRODUCTION_INPUT_NOT_READY"
STOP_DERIVATION = "STOP_T0_READINESS_NOT_DERIVED_FROM_THE_PARENT_CHAIN"
STOP_SELF_ATTESTED = "STOP_T0_READINESS_PACKAGE_ATTESTS_TO_ITS_OWN_IDENTITY"
STOP_FORBIDDEN_GATE = "STOP_T0_READINESS_FORBIDDEN_GATE_REPORTED_OPEN"
STOP_AUTHORIZATION = "STOP_T0_READINESS_STAGED_AUTHORIZATION_ABSENT"
STOP_ROLE_COUNTS = "STOP_T0_READINESS_DONOR_ROLE_COUNTS_NOT_THE_FROZEN_DESIGN"
STOP_NUMERIC_AT8 = "STOP_T0_READINESS_PACKAGE_CLAIMS_IT_READ_A_NUMERIC_AT8_VALUE"
STOP_PACKAGE_KIND = "STOP_T0_READINESS_PACKAGE_KIND_INVALID"
STOP_FIELD_SCHEMA = "STOP_T0_READINESS_FIELD_SCHEMA_VIOLATION"
STOP_ROOT_MISMATCH = "STOP_T0_READINESS_ROOT_MISMATCH"
STOP_PACKAGE_MEMBER = "STOP_T0_READINESS_PACKAGE_MEMBER_INVALID"


def _typed(value: Any) -> bytes:
    if isinstance(value, bool):
        tag, payload = b"b", (b"1" if value else b"0")
    elif isinstance(value, int):
        tag, payload = b"i", str(int(value)).encode("ascii")
    elif isinstance(value, str):
        tag, payload = b"s", value.encode("utf-8")
    elif isinstance(value, (tuple, list)):
        tag = b"l"
        payload = b"%d:%s" % (len(value), b"".join(_typed(v) for v in value))
    elif isinstance(value, dict):
        tag = b"d"
        items = []
        for key in sorted(value):
            items.append(_typed(str(key)))
            items.append(_typed(value[key]))
        payload = b"%d:%s" % (len(value), b"".join(items))
    else:
        raise AssertionError("%s: cannot frame %r"
                             % (STOP_FIELD_SCHEMA, type(value)))
    return b"%s%d:%s" % (tag, len(payload), payload)


def _is_hex64(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def donor_set_digest(role: str, donors: Iterable[str]) -> str:
    """Injective digest of a role's donor set, order-independent."""
    order = sorted((str(d) for d in donors), key=lambda v: v.encode("utf-8"))
    if len(set(order)) != len(order):
        raise AssertionError("%s: duplicate donor in %s" % (STOP_DONOR_SET, role))
    parts = [_typed(NAMESPACE), _typed("DONOR_SET"), _typed(str(role)),
             _typed(len(order)), _typed(list(order))]
    return hashlib.sha256(b"".join(parts)).hexdigest()


def readiness_root(obj: Mapping[str, Any]) -> str:
    """Digest over the whole readiness decision, including its derivation."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(str(obj["package_kind"])),
             _typed(bool(obj["real_execution_ready"])),
             _typed(str(obj["readiness_derivation"])),
             _typed(READINESS_DERIVATION_STATEMENT),
             _typed(list(REQUIRED_BINDINGS)),
             _typed(dict(obj["bindings"])),
             _typed(dict(obj["forbidden_gates_opened"])),
             _typed(str(obj["code_byte_semantics"])),
             _typed(bool(obj["numeric_at8_value_read"])),
             _typed(dict(obj["donor_role_counts"]))]
    return hashlib.sha256(b"".join(parts)).hexdigest()


def package_root(members: Mapping[str, bytes]) -> str:
    names = sorted(members)
    parts = [_typed(DOMAIN_TAG), _typed("PACKAGE"), _typed(len(names))]
    for name in names:
        parts.append(_typed([name,
                             hashlib.sha256(bytes(members[name])).hexdigest()]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


# ---------------------------------------------------------------------------
# The three conjuncts of the derivation, each computed rather than asserted.
# ---------------------------------------------------------------------------

def all_required_stage1_bindings_verified(
        bindings: Mapping[str, Any],
        *,
        expected: Mapping[str, Any] | None = None) -> bool:
    """Every required binding present and equal to its accepted value.

    `expected` defaults to the frozen ACCEPTED_BINDINGS in committed code. A
    caller may override it, which is what a reviewer does to test the check, but
    it may not be the package's own bindings object -- that is refused upstream
    in `assert_production_authority_lawful`.
    """
    # What this proves, stated precisely so the guarantee is not overread: that
    # the package CITES the accepted roots. It does not prove those roots still
    # reproduce from their sources -- that is Stage 1's job, and the production
    # materializer is driven by a live Stage 1 verification rather than by
    # hand-written bindings, so the two together give reproduction plus citation.
    reference = ACCEPTED_BINDINGS if expected is None else expected
    for name in REQUIRED_BINDINGS:
        if name not in bindings:
            raise AssertionError("%s: %s" % (STOP_BINDING_ABSENT, name))
    extra = [n for n in bindings if n not in REQUIRED_BINDINGS]
    if extra:
        raise AssertionError("%s: unexpected bindings %s"
                             % (STOP_FIELD_SCHEMA, sorted(extra)))
    for name in _DIGEST_BINDINGS:
        if not _is_hex64(bindings[name]):
            raise AssertionError("%s: %s is %r, not a lowercase hex sha256"
                                 % (STOP_FIELD_SCHEMA, name, bindings[name]))
    for name in ("discovery_donor_set_sha256", "confirmation_donor_set_sha256"):
        if str(bindings[name]) != str(reference[name]):
            raise AssertionError(
                "%s: %s is %s, accepted %s"
                % (STOP_DONOR_SET, name, bindings[name], reference[name]))
    for name in ("at8_endpoint_identity", "pathology_source_sha256"):
        if str(bindings[name]) != str(reference[name]):
            raise AssertionError(
                "%s: %s is %r, accepted %r"
                % (STOP_ENDPOINT, name, bindings[name], reference[name]))
    for name in REQUIRED_BINDINGS:
        if name in ("discovery_donor_set_sha256",
                    "confirmation_donor_set_sha256",
                    "at8_endpoint_identity", "pathology_source_sha256"):
            continue
        if str(bindings[name]) != str(reference[name]):
            raise AssertionError("%s: %s is %r, accepted %r"
                                 % (STOP_BINDING_MISMATCH, name,
                                    bindings[name], reference[name]))
    return True


def staged_authorization_present(obj: Mapping[str, Any]) -> bool:
    """The owner's staged authorization, by token, scope and record digest."""
    auth = obj.get("staged_authorization")
    if not isinstance(auth, dict):
        raise AssertionError("%s: no staged authorization block"
                             % STOP_AUTHORIZATION)
    if str(auth.get("token")) != STAGED_AUTHORIZATION_TOKEN:
        raise AssertionError("%s: token is %r, expected %r"
                             % (STOP_AUTHORIZATION, auth.get("token"),
                                STAGED_AUTHORIZATION_TOKEN))
    if str(auth.get("scope")) != STAGED_AUTHORIZATION_SCOPE:
        raise AssertionError("%s: scope is %r, expected %r"
                             % (STOP_AUTHORIZATION, auth.get("scope"),
                                STAGED_AUTHORIZATION_SCOPE))
    recorded = str(obj["bindings"]["authorization_record_root_sha256"])
    if str(auth.get("record_sha256")) != recorded:
        raise AssertionError(
            "%s: the authorization block cites record %r but the bindings cite "
            "%r" % (STOP_AUTHORIZATION, auth.get("record_sha256"), recorded))
    return True


def no_forbidden_gate_opened(obj: Mapping[str, Any]) -> bool:
    """Every forbidden gate declared and declared shut."""
    gates = obj.get("forbidden_gates_opened")
    if not isinstance(gates, dict):
        raise AssertionError("%s: no forbidden-gate declaration"
                             % STOP_FORBIDDEN_GATE)
    missing = [g for g in FORBIDDEN_GATES if g not in gates]
    if missing:
        raise AssertionError("%s: undeclared gates %s"
                             % (STOP_FORBIDDEN_GATE, missing))
    extra = [g for g in gates if g not in FORBIDDEN_GATES]
    if extra:
        raise AssertionError("%s: unknown gates %s"
                             % (STOP_FORBIDDEN_GATE, sorted(extra)))
    for gate in FORBIDDEN_GATES:
        if gates[gate] is not False:
            raise AssertionError("%s: %s is %r and must be False"
                                 % (STOP_FORBIDDEN_GATE, gate, gates[gate]))
    return True


def derive_readiness(obj: Mapping[str, Any],
                     *,
                     expected: Mapping[str, Any] | None = None) -> bool:
    """The derivation, exactly as stated. Never an assignment."""
    return bool(all_required_stage1_bindings_verified(obj["bindings"],
                                                      expected=expected)
                and staged_authorization_present(obj)
                and no_forbidden_gate_opened(obj))


# ---------------------------------------------------------------------------
# Lawfulness.
# ---------------------------------------------------------------------------

def _assert_common(obj: Mapping[str, Any]) -> None:
    if str(obj.get("schema")) != SCHEMA:
        raise AssertionError("%s: schema is %r" % (STOP_FIELD_SCHEMA,
                                                   obj.get("schema")))
    if obj.get("numeric_at8_value_read") is not False:
        raise AssertionError(
            "%s: this authority binds the endpoint identity and the source "
            "digest and must never parse a magnitude" % STOP_NUMERIC_AT8)
    if str(obj.get("code_byte_semantics")) == WAIVED_FALSE_CODE_BYTE_SEMANTICS:
        raise AssertionError(
            "%s: %r is the waived legacy label and no new real-T0 artifact may "
            "carry it" % (STOP_BYTE_SEMANTICS,
                          WAIVED_FALSE_CODE_BYTE_SEMANTICS))
    if str(obj.get("code_byte_semantics")) != ACCURATE_CODE_BYTE_SEMANTICS:
        raise AssertionError("%s: code_byte_semantics is %r, expected %r"
                             % (STOP_BYTE_SEMANTICS,
                                obj.get("code_byte_semantics"),
                                ACCURATE_CODE_BYTE_SEMANTICS))
    counts = obj.get("donor_role_counts")
    if not isinstance(counts, dict):
        raise AssertionError("%s: no donor_role_counts" % STOP_ROLE_COUNTS)
    frozen = {"CONFIRMATION": CONFIRMATION_DONORS,
              "DISCOVERY": DISCOVERY_DONORS,
              "INELIGIBLE": INELIGIBLE_DONORS}
    if {k: int(v) for k, v in counts.items()} != frozen:
        raise AssertionError("%s: %r, frozen design is %r"
                             % (STOP_ROLE_COUNTS, counts, frozen))


def assert_production_authority_lawful(
        obj: Mapping[str, Any],
        *,
        expected: Mapping[str, Any] | None = None) -> bool:
    """A production execution-input authority is lawful only if it earns it.

    `real_execution_ready` must be True *and* re-derivable here from the
    bindings, the staged authorization and the shut gates. A True that the
    derivation does not reproduce is refused, which is what makes readiness
    derived rather than declared.
    """
    if expected is not None and expected is obj.get("bindings"):
        raise AssertionError(
            "%s: the expected values are this package's own bindings object, so "
            "the package would be attesting to its own identity. Expectations "
            "must come from outside the package." % STOP_SELF_ATTESTED)
    if str(obj.get("package_kind")) != PACKAGE_KIND_PRODUCTION:
        raise AssertionError("%s: package_kind is %r, expected %r"
                             % (STOP_PACKAGE_KIND, obj.get("package_kind"),
                                PACKAGE_KIND_PRODUCTION))
    _assert_common(obj)
    if str(obj.get("readiness_derivation")) != READINESS_DERIVATION:
        raise AssertionError(
            "%s: readiness_derivation is %r, and production readiness is only "
            "lawful when marked %r"
            % (STOP_DERIVATION, obj.get("readiness_derivation"),
               READINESS_DERIVATION))
    if obj.get("real_execution_ready") is not True:
        raise AssertionError(
            "%s: real_execution_ready is %r; the canonical freeze and "
            "adjudicator require True on production execution input"
            % (STOP_NOT_READY, obj.get("real_execution_ready")))
    # Re-derive. Note what this does and does not do: `derive_readiness` either
    # returns True or raises with the specific conjunct that failed, so there is
    # no "returned False" branch to test for. An earlier draft of this function
    # had one, and it was unreachable decoration of exactly the kind this lane
    # keeps finding in its own verifiers. The discrimination is real and lives in
    # the raise: a package recording True over bindings that do not match the
    # accepted values fails here with STOP_T0_READINESS_BINDING_DOES_NOT_MATCH_
    # ACCEPTED_VALUE rather than being waved through.
    derive_readiness(obj, expected=expected)
    return True


def assert_non_production_authority_lawful(obj: Mapping[str, Any]) -> bool:
    """`False` stays lawful for pre-run, test, fixture and candidate packages."""
    kind = str(obj.get("package_kind"))
    if kind not in NON_PRODUCTION_KINDS:
        raise AssertionError("%s: %r is not a non-production kind %r"
                             % (STOP_PACKAGE_KIND, kind, NON_PRODUCTION_KINDS))
    _assert_common(obj)
    if obj.get("real_execution_ready") is not False:
        raise AssertionError(
            "%s: a %s package may not claim readiness"
            % (STOP_NOT_READY, kind))
    if str(obj.get("readiness_derivation")) != (
            READINESS_DERIVATION_NON_PRODUCTION):
        raise AssertionError("%s: readiness_derivation is %r, expected %r"
                             % (STOP_DERIVATION,
                                obj.get("readiness_derivation"),
                                READINESS_DERIVATION_NON_PRODUCTION))
    return True


def assert_frozen_v2_gate_would_be_satisfied(obj: Mapping[str, Any]) -> bool:
    """The frozen canonical gate's condition, evaluated against this object.

    `t0_canonical_freeze_v2._verified` and `t0_adjudicator_v2` both refuse
    unless `real_execution_ready is True`. A lawful production authority from
    this module satisfies that condition, which is the whole point of the
    repair: the gate is not weakened, it is made satisfiable by something that
    had to earn it.
    """
    assert_production_authority_lawful(obj)
    if obj["real_execution_ready"] is not True:
        raise AssertionError("%s: would still fail the frozen gate"
                             % STOP_NOT_READY)
    return True


# ---------------------------------------------------------------------------
# A lawful object, for tests and for the shape of the real one.
# ---------------------------------------------------------------------------

def lawful_fixture_object() -> dict[str, Any]:
    """A production-shaped object carrying the real accepted bindings.

    Used by the R7 suite to exercise each refusal by mutating one field at a
    time. It is production-shaped deliberately: a fixture that could not pass
    would not prove that the refusals discriminate.
    """
    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "package_kind": PACKAGE_KIND_PRODUCTION,
        "real_execution_ready": True,
        "readiness_derivation": READINESS_DERIVATION,
        "readiness_derivation_statement": READINESS_DERIVATION_STATEMENT,
        "bindings": dict(ACCEPTED_BINDINGS),
        "staged_authorization": {
            "token": STAGED_AUTHORIZATION_TOKEN,
            "scope": STAGED_AUTHORIZATION_SCOPE,
            "record_sha256":
                ACCEPTED_BINDINGS["authorization_record_root_sha256"],
        },
        "forbidden_gates_opened": {gate: False for gate in FORBIDDEN_GATES},
        "donor_role_counts": {"CONFIRMATION": CONFIRMATION_DONORS,
                              "DISCOVERY": DISCOVERY_DONORS,
                              "INELIGIBLE": INELIGIBLE_DONORS},
        "code_byte_semantics": ACCURATE_CODE_BYTE_SEMANTICS,
        "numeric_at8_value_read": False,
        "scientific_design_unchanged": SCIENTIFIC_DESIGN_UNCHANGED,
        "population_rows": POPULATION_ROWS,
        "candidate_donors": CANDIDATE_DONORS,
    }


# ---------------------------------------------------------------------------
# Materialize and replay.
# ---------------------------------------------------------------------------

def materialize_production_authority(
        outdir: Path | str,
        *,
        bindings: Mapping[str, Any],
        staged_authorization: Mapping[str, Any],
        forbidden_gates_opened: Mapping[str, bool],
        donor_role_counts: Mapping[str, int],
        expected: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a production authority whose readiness was derived, not supplied.

    Note the absent parameter: there is no `real_execution_ready` argument. The
    caller cannot pass it. It is computed by `derive_readiness` from the
    bindings, the staged authorization and the gate declaration, and if the
    derivation raises, no package is written.
    """
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output must be absent or empty: %s"
                             % (STOP_PACKAGE_MEMBER, out))

    candidate = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "package_kind": PACKAGE_KIND_PRODUCTION,
        "readiness_derivation": READINESS_DERIVATION,
        "readiness_derivation_statement": READINESS_DERIVATION_STATEMENT,
        "bindings": {k: bindings[k] for k in sorted(bindings)},
        "staged_authorization": dict(sorted(staged_authorization.items())),
        "forbidden_gates_opened": {g: bool(forbidden_gates_opened[g])
                                   for g in FORBIDDEN_GATES},
        "donor_role_counts": {k: int(v) for k, v
                              in sorted(donor_role_counts.items())},
        "code_byte_semantics": ACCURATE_CODE_BYTE_SEMANTICS,
        "numeric_at8_value_read": False,
        "scientific_design_unchanged": SCIENTIFIC_DESIGN_UNCHANGED,
        "population_rows": POPULATION_ROWS,
        "candidate_donors": CANDIDATE_DONORS,
    }
    # Derive. This is the only place readiness is set, and it is set to the
    # value the conjunction produces.
    candidate["real_execution_ready"] = derive_readiness(candidate,
                                                         expected=expected)
    assert_production_authority_lawful(candidate, expected=expected)

    root = readiness_root(candidate)
    candidate["readiness_root_sha256"] = root
    member = (json.dumps(candidate, sort_keys=True, indent=2)
              + "\n").encode("utf-8")

    manifest = io.StringIO()
    manifest.write("filename,bytes,sha256\n")
    manifest.write("%s,%d,%s\n" % (MEMBER, len(member),
                                   hashlib.sha256(member).hexdigest()))
    manifest_bytes = manifest.getvalue().encode("utf-8")

    members = {MEMBER: member, MANIFEST: manifest_bytes}
    pkg_root = package_root(members)

    out.mkdir(parents=True, exist_ok=True)
    for name, blob in members.items():
        with io.open(out / name, "wb") as handle:
            handle.write(blob)
    with io.open(out / ROOT_FILE, "w", encoding="utf-8", newline="\n") as h:
        h.write(pkg_root + "\n")

    return {"authority": candidate, "readiness_root_sha256": root,
            "package_root_sha256": pkg_root,
            "real_execution_ready": candidate["real_execution_ready"]}


def load_production_authority(
        outdir: Path | str,
        *,
        expected_package_root_sha256: str,
        expected_readiness_root_sha256: str,
        expected: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Load a production authority, re-deriving readiness rather than reading it.

    This is the repaired loader. It requires `real_execution_ready is True`,
    which the frozen loader refused, and it earns that by re-running the whole
    derivation against expectations from outside the package.
    """
    out = Path(outdir)
    captured: dict[str, bytes] = {}
    for name in MEMBERS:
        path = out / name
        if not path.is_file():
            raise AssertionError("%s: %s absent" % (STOP_PACKAGE_MEMBER, path))
        captured[name] = path.read_bytes()

    described = captured[MANIFEST].decode("utf-8").splitlines()
    if described[0] != "filename,bytes,sha256":
        raise AssertionError("%s: manifest header" % STOP_PACKAGE_MEMBER)
    name, size, digest = described[1].split(",")
    if (name != MEMBER or int(size) != len(captured[MEMBER])
            or digest != hashlib.sha256(captured[MEMBER]).hexdigest()):
        raise AssertionError("%s: manifest does not describe the member on disk"
                             % STOP_PACKAGE_MEMBER)

    pkg_root = package_root(captured)
    if pkg_root != str(expected_package_root_sha256):
        raise AssertionError("%s: package root is %s, expected %s"
                             % (STOP_ROOT_MISMATCH, pkg_root,
                                expected_package_root_sha256))

    obj = json.loads(captured[MEMBER].decode("utf-8"))
    stored_root = obj.pop("readiness_root_sha256", None)
    recomputed = readiness_root(obj)
    if stored_root != recomputed:
        raise AssertionError("%s: stored readiness root %r, recomputed %s"
                             % (STOP_ROOT_MISMATCH, stored_root, recomputed))
    if recomputed != str(expected_readiness_root_sha256):
        raise AssertionError("%s: readiness root is %s, expected %s"
                             % (STOP_ROOT_MISMATCH, recomputed,
                                expected_readiness_root_sha256))

    assert_production_authority_lawful(obj, expected=expected)
    assert_frozen_v2_gate_would_be_satisfied(obj)

    obj["readiness_root_sha256"] = recomputed
    return {"authority": obj, "readiness_root_sha256": recomputed,
            "package_root_sha256": pkg_root,
            "real_execution_ready": obj["real_execution_ready"],
            "frozen_v2_gate_satisfied": True}
