"""T0 eligible-donor authority and the deterministic donor-role split.

What this is
------------
The statistical population, derived from authenticated pathology-blind parents
and nothing else. It answers two questions in order:

    eligible(d)  = AT8_available(d) & technical_complete(d)
                   & age_present(d) & sex_present(d)
    role(d)      = eligible donors ordered by (split_hash, donor_id);
                   the first 18 are CONFIRMATION, the remainder DISCOVERY

Both are frozen rules, not choices made here. The predicate is read verbatim off
`t0_donor_role_authority_v2`, and the split hash is
`sha256("T0-DISCOVERY-CONFIRM-V2|" + donor_id)`.

What it may emit, and what it may not
-------------------------------------
It emits donor identity, eligibility and role status, boolean availability and
definedness fields, parent roots and provenance digests. It emits no numeric
pathology value, and it never reads one: AT8 enters only as the boolean
`AT8_available`, which the availability authority derived without parsing a
magnitude. `assert_no_pathology_in_artifact` refuses any emitted field that names
a pathology endpoint, and no age or sex VALUE is emitted either -- only whether
each was present -- so the artifact carries no donor-level covariate at all.

Fail-closed
-----------
A donor missing from a parent authority is a STOP, not an ineligible donor. If a
parent does not cover the candidate universe, the eligible set is undefined
rather than smaller, because letting a coverage gap present itself as
ineligibility is how an eligibility mechanism becomes a way to drop inconvenient
donors.

If the frozen eligible universe falls below 18 CONFIRMATION plus 18 minimum
DISCOVERY donors, that is
`STOP_T0_DESIGN_NOT_EXECUTABLE_UNDER_FROZEN_ELIGIBILITY`. No threshold is
relaxed and the split is not altered to rescue it. Likewise a single-sex
confirmation set is a loud design failure of the rank check downstream, never a
biological NOT_MEASURABLE.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "JEPA_T0_ELIGIBLE_DONOR_AUTHORITY_V1"
NAMESPACE = "T0-ELIGIBLE-DONOR-V1"
DOMAIN_TAG = "T0-ELIGIBLE-DONOR-V1-TYPED-LENGTH-PREFIXED"

# The frozen split namespace, from t0_discovery_confirmation_split_v2.
ROLE_NAMESPACE = "T0-DISCOVERY-CONFIRM-V2"
CONFIRMATION_DONORS = 18
MINIMUM_DISCOVERY_DONORS = 18
CANDIDATE_DONORS = 46

REGISTRY = "T0_ELIGIBLE_DONOR_REGISTRY.csv"
METADATA = "T0_ELIGIBLE_DONOR_METADATA.json"
MANIFEST = "T0_ELIGIBLE_DONOR_MANIFEST.csv"
ROOT_FILE = "T0_ELIGIBLE_DONOR_PACKAGE_ROOT_SHA256.txt"
MEMBERS = (REGISTRY, METADATA, MANIFEST)

REGISTRY_FIELDS = ("donor_id", "at8_available", "technical_complete",
                   "age_present", "sex_present", "eligible", "split_hash",
                   "donor_role")

STOP_PARENT_COVERAGE = "STOP_T0_ELIGIBLE_DONOR_PARENT_DOES_NOT_COVER_THE_UNIVERSE"
STOP_PARENT_IDENTITY = "STOP_T0_ELIGIBLE_DONOR_PARENT_IDENTITY_NOT_BOUND"
STOP_DUPLICATE_DONOR = "STOP_T0_ELIGIBLE_DONOR_DUPLICATE_DONOR"
STOP_NOT_BOOLEAN = "STOP_T0_ELIGIBLE_DONOR_FIELD_NOT_BOOLEAN"
STOP_DESIGN_NOT_EXECUTABLE = "STOP_T0_DESIGN_NOT_EXECUTABLE_UNDER_FROZEN_ELIGIBILITY"
STOP_PATHOLOGY_IN_ARTIFACT = "STOP_T0_ELIGIBLE_DONOR_PATHOLOGY_FIELD_IN_ARTIFACT"
STOP_ROOT_MISMATCH = "STOP_T0_ELIGIBLE_DONOR_ROOT_MISMATCH"
STOP_PACKAGE_MEMBER = "STOP_T0_ELIGIBLE_DONOR_PACKAGE_MEMBER_INVALID"
STOP_FIELD_SCHEMA = "STOP_T0_ELIGIBLE_DONOR_FIELD_SCHEMA_VIOLATION"
STOP_ROLE_RULE = "STOP_T0_ELIGIBLE_DONOR_ROLE_RULE_ALTERED"
STOP_PREDICATE_CONTRADICTED = "STOP_T0_ELIGIBLE_DONOR_PREDICATE_CONTRADICTED"
STOP_MANIFEST_MISMATCH = "STOP_T0_ELIGIBLE_DONOR_MANIFEST_DOES_NOT_MATCH_MEMBERS"
STOP_COUNTS_MISMATCH = "STOP_T0_ELIGIBLE_DONOR_METADATA_COUNTS_MISMATCH"

PATHOLOGY_MARKERS = ("at8_value", "at8_percent", "6e10", "gfap", "iba1", "neun",
                     "abeta", "ptau", "ttau", "braak", "thal", "cerad",
                     "positive area", "percent at8")


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
    else:
        raise AssertionError("%s: cannot frame %r" % (STOP_FIELD_SCHEMA, type(value)))
    return b"%s%d:%s" % (tag, len(payload), payload)


def _is_hex64(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def assert_no_pathology_in_artifact(fields: Iterable[str] = REGISTRY_FIELDS) -> bool:
    """No emitted field may name a pathology endpoint or magnitude."""
    for field in fields:
        lowered = str(field).lower()
        for marker in PATHOLOGY_MARKERS:
            if marker in lowered:
                raise AssertionError("%s: emitted field %r matches %r"
                                     % (STOP_PATHOLOGY_IN_ARTIFACT, field, marker))
    return True


def split_hash(donor_id: str, *, namespace: str = ROLE_NAMESPACE) -> str:
    """The frozen split hash. Deterministic and outcome-independent."""
    if not isinstance(donor_id, str) or not donor_id:
        raise AssertionError("%s: donor_id must be a non-empty string"
                             % STOP_FIELD_SCHEMA)
    return hashlib.sha256(("%s|%s" % (namespace, donor_id)).encode("utf-8")
                          ).hexdigest()


def assert_role_rule_unaltered() -> bool:
    """The split rule is frozen; drift here would refit a pre-registered design."""
    if ROLE_NAMESPACE != "T0-DISCOVERY-CONFIRM-V2":
        raise AssertionError("%s: namespace is %r" % (STOP_ROLE_RULE, ROLE_NAMESPACE))
    if CONFIRMATION_DONORS != 18 or MINIMUM_DISCOVERY_DONORS != 18:
        raise AssertionError("%s: the frozen floors are 18 and 18, not %d and %d"
                             % (STOP_ROLE_RULE, CONFIRMATION_DONORS,
                                MINIMUM_DISCOVERY_DONORS))
    return True


def _boolean(value: Any, *, what: str, allow_text: bool = False) -> bool:
    """Accept a real boolean; accept its exact textual form only on reload.

    The textual form exists because CSV has no booleans, so the loader has to
    parse one back. A derivation must not enjoy that latitude: a parent authority
    handing over the string "True" has not been validated as boolean by anything,
    and accepting it here would let an unparsed CSV column decide eligibility.
    So `allow_text` is opened by the loader alone.
    """
    if isinstance(value, bool):
        return value
    if allow_text and isinstance(value, str) and value.strip() in ("True",
                                                                   "False"):
        return value.strip() == "True"
    raise AssertionError("%s: %s is %r" % (STOP_NOT_BOOLEAN, what, value))


def derive_eligible_donors(
        *,
        candidate_donors: Sequence[str],
        at8_available: Mapping[str, Any],
        technical_complete: Mapping[str, Any],
        age_present: Mapping[str, Any],
        sex_present: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Apply the frozen predicate, then the frozen split, in that order.

    Every parent must cover the whole candidate universe. A donor a parent does
    not mention is a STOP rather than an ineligible donor, because a coverage gap
    presenting itself as ineligibility is exactly how an eligibility mechanism
    turns into a way to drop donors.
    """
    assert_role_rule_unaltered()
    universe = [str(d) for d in candidate_donors]
    if len(universe) != len(set(universe)):
        duplicates = sorted({d for d in universe if universe.count(d) > 1})
        raise AssertionError("%s: %s" % (STOP_DUPLICATE_DONOR, duplicates))

    parents = {"at8_available": at8_available,
               "technical_complete": technical_complete,
               "age_present": age_present, "sex_present": sex_present}
    for name, mapping in parents.items():
        missing = [d for d in universe if d not in mapping]
        if missing:
            raise AssertionError(
                "%s: %s does not cover %d candidate donors, e.g. %s"
                % (STOP_PARENT_COVERAGE, name, len(missing), missing[:5]))
        extra = [d for d in mapping if str(d) not in set(universe)]
        if extra:
            raise AssertionError(
                "%s: %s covers %d donors outside the candidate universe, e.g. %s"
                % (STOP_PARENT_COVERAGE, name, len(extra), sorted(extra)[:5]))

    rows = []
    for donor in sorted(universe, key=lambda d: d.encode("utf-8")):
        flags = {name: _boolean(mapping[donor], what="%s for %s" % (name, donor))
                 for name, mapping in parents.items()}
        rows.append({
            "donor_id": donor,
            "at8_available": flags["at8_available"],
            "technical_complete": flags["technical_complete"],
            "age_present": flags["age_present"],
            "sex_present": flags["sex_present"],
            "eligible": all(flags.values()),
            "split_hash": split_hash(donor),
            "donor_role": "",
        })

    eligible = [row for row in rows if row["eligible"]]
    if len(eligible) < CONFIRMATION_DONORS + MINIMUM_DISCOVERY_DONORS:
        raise AssertionError(
            "%s: %d eligible donors, and the frozen design needs %d CONFIRMATION "
            "plus at least %d DISCOVERY. Do not relax eligibility, introduce a "
            "cutoff, or alter the split."
            % (STOP_DESIGN_NOT_EXECUTABLE, len(eligible), CONFIRMATION_DONORS,
               MINIMUM_DISCOVERY_DONORS))

    ordered = sorted(eligible, key=lambda row: (row["split_hash"],
                                                row["donor_id"]))
    confirmation = {row["donor_id"] for row in ordered[:CONFIRMATION_DONORS]}
    for row in rows:
        if not row["eligible"]:
            row["donor_role"] = "INELIGIBLE"
        elif row["donor_id"] in confirmation:
            row["donor_role"] = "CONFIRMATION"
        else:
            row["donor_role"] = "DISCOVERY"

    discovery = sum(1 for row in rows if row["donor_role"] == "DISCOVERY")
    if discovery < MINIMUM_DISCOVERY_DONORS:
        raise AssertionError("%s: %d DISCOVERY donors, minimum %d"
                             % (STOP_DESIGN_NOT_EXECUTABLE, discovery,
                                MINIMUM_DISCOVERY_DONORS))
    return tuple(rows)


def assert_predicate_holds_on_every_row(
        rows: Sequence[Mapping[str, Any]]) -> bool:
    """`eligible` must equal the conjunction of the four flags on its own row.

    Without this, a package could carry `eligible=True` beside a `False`
    conjunct and stay internally consistent under every digest it publishes:
    the roots would simply certify the contradiction. The predicate is the whole
    content of this authority, so it is recomputed rather than trusted.
    """
    for row in rows:
        conjuncts = (bool(row["at8_available"]), bool(row["technical_complete"]),
                     bool(row["age_present"]), bool(row["sex_present"]))
        if bool(row["eligible"]) != all(conjuncts):
            raise AssertionError(
                "%s: %s records eligible=%r beside flags %r, and the predicate "
                "yields %r" % (STOP_PREDICATE_CONTRADICTED, row["donor_id"],
                               bool(row["eligible"]), conjuncts,
                               all(conjuncts)))
        if not bool(row["eligible"]) and str(row["donor_role"]) != "INELIGIBLE":
            raise AssertionError(
                "%s: %s is not eligible but carries role %r"
                % (STOP_PREDICATE_CONTRADICTED, row["donor_id"],
                   row["donor_role"]))
    return True


def eligible_donor_root(rows: Sequence[Mapping[str, Any]]) -> str:
    """Digest over the eligibility decision for every candidate donor."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(list(REGISTRY_FIELDS)), _typed(len(rows))]
    for row in rows:
        parts.append(_typed([
            str(row["donor_id"]),
            bool(row["at8_available"]), bool(row["technical_complete"]),
            bool(row["age_present"]), bool(row["sex_present"]),
            bool(row["eligible"]), str(row["split_hash"]),
            str(row["donor_role"]),
        ]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def donor_role_root(rows: Sequence[Mapping[str, Any]]) -> str:
    """Digest over the role assignment alone, so it can be cited separately."""
    assigned = sorted((row for row in rows if row["eligible"]),
                      key=lambda row: (row["split_hash"], row["donor_id"]))
    parts = [_typed(DOMAIN_TAG), _typed("DONOR_ROLE"), _typed(ROLE_NAMESPACE),
             _typed(int(CONFIRMATION_DONORS)), _typed(len(assigned))]
    for row in assigned:
        parts.append(_typed([str(row["donor_id"]), str(row["split_hash"]),
                             str(row["donor_role"])]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def parent_contract_root(parents: Mapping[str, str]) -> str:
    """One root over every parent authority identity this decision rests on."""
    names = sorted(parents)
    parts = [_typed(DOMAIN_TAG), _typed("PARENT_CONTRACT"), _typed(len(names))]
    for name in names:
        value = parents[name]
        if not _is_hex64(value):
            raise AssertionError("%s: %s is %r, not a lowercase hex sha256"
                                 % (STOP_PARENT_IDENTITY, name, value))
        parts.append(_typed([name, str(value)]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def package_root(members: Mapping[str, bytes]) -> str:
    names = sorted(members)
    parts = [_typed(DOMAIN_TAG), _typed("PACKAGE"), _typed(len(names))]
    for name in names:
        parts.append(_typed([name,
                             hashlib.sha256(bytes(members[name])).hexdigest()]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def build_authority(
        outdir: Path | str,
        *,
        rows: Sequence[Mapping[str, Any]],
        parents: Mapping[str, str],
        derivation_code_sha256: str,
        at8_availability_independently_verified: bool,
        expected_candidate_donors: int = CANDIDATE_DONORS,
) -> dict[str, Any]:
    """Write the eligible-donor authority as immutable artifacts."""
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output directory must be absent or empty: %s"
                             % (STOP_PACKAGE_MEMBER, out))
    assert_no_pathology_in_artifact()
    assert_role_rule_unaltered()
    if len(rows) != int(expected_candidate_donors):
        raise AssertionError("%s: %d donor rows, expected the %d-donor universe"
                             % (STOP_PARENT_COVERAGE, len(rows),
                                int(expected_candidate_donors)))

    assert_predicate_holds_on_every_row(rows)
    assert_roles_agree_with_frozen_rule(rows)

    # The code identity is a digest, and a field named `_sha256` must carry one.
    # A 40-character Git SHA-1 was recorded here once; the width check is what
    # turns that class of mislabelling into a refusal.
    if not _is_hex64(derivation_code_sha256):
        raise AssertionError(
            "%s: derivation_code_sha256 is %r, which is not a lowercase "
            "64-character hex SHA-256"
            % (STOP_PARENT_IDENTITY, derivation_code_sha256))

    root = eligible_donor_root(rows)
    role_root = donor_role_root(rows)
    parent_root = parent_contract_root(parents)

    registry = io.StringIO()
    writer = csv.writer(registry, lineterminator="\n")
    writer.writerow(list(REGISTRY_FIELDS))
    for row in rows:
        writer.writerow([row["donor_id"], bool(row["at8_available"]),
                         bool(row["technical_complete"]),
                         bool(row["age_present"]), bool(row["sex_present"]),
                         bool(row["eligible"]), row["split_hash"],
                         row["donor_role"]])
    registry_bytes = registry.getvalue().encode("utf-8")

    roles = {}
    for row in rows:
        roles[row["donor_role"]] = roles.get(row["donor_role"], 0) + 1
    meta = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "finalized": True,
        "registry_fields": list(REGISTRY_FIELDS),
        "candidate_donors": len(rows),
        "eligible_donors": sum(1 for row in rows if row["eligible"]),
        "role_counts": roles,
        "eligibility_predicate": (
            "AT8_available & technical_complete & age_present & sex_present"),
        "role_rule": (
            "eligible donors ordered by (split_hash, donor_id); first 18 "
            "CONFIRMATION, remainder DISCOVERY"),
        "role_namespace": ROLE_NAMESPACE,
        "binding_role_rule": ROLE_AUTHORITY_RULE,
        "confirmation_donors": CONFIRMATION_DONORS,
        "minimum_discovery_donors": MINIMUM_DISCOVERY_DONORS,
        "eligible_donor_root_sha256": root,
        "donor_role_root_sha256": role_root,
        "parent_contract_root_sha256": parent_root,
        "parents": {name: str(parents[name]) for name in sorted(parents)},
        "derivation_code_sha256": str(derivation_code_sha256),
        # Deliberately not "GIT_BLOB_BYTES". A Git blob digest frames the
        # content as b"blob <len>\0" + content and would be a different value;
        # every package in this lane in fact records the plain SHA-256 of the
        # LF-normalized content, and the older ones label that as Git blob
        # bytes. That mislabelling is reported for external review rather than
        # silently re-stamped, because correcting it there means re-running and
        # re-rooting artifacts already cited. It is not propagated here.
        "derivation_code_byte_semantics": "SHA256_OVER_LF_NORMALIZED_FILE_CONTENT__NOT_GIT_BLOB_FRAMED_AND_NOT_WORKTREE_BYTES",
        "at8_availability_independently_verified": bool(
            at8_availability_independently_verified),
        "numeric_at8_value_read": False,
        "numeric_at8_value_emitted": False,
        "numeric_covariate_values_emitted": False,
        "pathology_fields_in_artifact": False,
        "real_execution_ready": False,
    }
    meta_bytes = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8")

    manifest = io.StringIO()
    mwriter = csv.writer(manifest, lineterminator="\n")
    mwriter.writerow(["filename", "bytes", "sha256"])
    for name, blob in ((REGISTRY, registry_bytes), (METADATA, meta_bytes)):
        mwriter.writerow([name, len(blob), hashlib.sha256(blob).hexdigest()])
    manifest_bytes = manifest.getvalue().encode("utf-8")

    members = {REGISTRY: registry_bytes, METADATA: meta_bytes,
               MANIFEST: manifest_bytes}
    pkg_root = package_root(members)

    out.mkdir(parents=True, exist_ok=True)
    for name, blob in members.items():
        with io.open(out / name, "wb") as handle:
            handle.write(blob)
    with io.open(out / ROOT_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(pkg_root + "\n")

    return {"eligible_donor_root_sha256": root,
            "donor_role_root_sha256": role_root,
            "parent_contract_root_sha256": parent_root,
            "package_root_sha256": pkg_root,
            "candidate_donors": len(rows),
            "eligible_donors": meta["eligible_donors"],
            "role_counts": roles,
            "real_execution_ready": False}


def load_authority(
        outdir: Path | str,
        *,
        expected_package_root_sha256: str,
        expected_eligible_donor_root_sha256: str,
        expected_donor_role_root_sha256: str,
        expected_parent_contract_root_sha256: str,
        expected_candidate_donors: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Replay the authority from disk and re-verify every root it claims."""
    out = Path(outdir)
    captured: dict[str, bytes] = {}
    for name in MEMBERS:
        path = out / name
        if not path.is_file():
            raise AssertionError("%s: %s absent" % (STOP_PACKAGE_MEMBER, path))
        captured[name] = path.read_bytes()

    # The manifest is reconciled against the bytes on disk. The package root
    # covers the manifest as a member, so a manifest that disagrees with its own
    # members is an internally broken package even when every root matches.
    manifest_rows = list(csv.DictReader(
        io.StringIO(captured[MANIFEST].decode("utf-8"))))
    described = {str(r["filename"]): (int(r["bytes"]), str(r["sha256"]))
                 for r in manifest_rows}
    for name in (REGISTRY, METADATA):
        if name not in described:
            raise AssertionError("%s: %s is not described in the manifest"
                                 % (STOP_MANIFEST_MISMATCH, name))
        want_bytes, want_digest = described[name]
        blob = captured[name]
        if len(blob) != want_bytes or hashlib.sha256(
                blob).hexdigest() != want_digest:
            raise AssertionError(
                "%s: %s is %d bytes / %s on disk but the manifest says %d / %s"
                % (STOP_MANIFEST_MISMATCH, name, len(blob),
                   hashlib.sha256(blob).hexdigest(), want_bytes, want_digest))

    pkg_root = package_root(captured)
    if pkg_root != str(expected_package_root_sha256):
        raise AssertionError("%s: package root is %s, expected %s"
                             % (STOP_ROOT_MISMATCH, pkg_root,
                                expected_package_root_sha256))

    text = captured[REGISTRY].decode("utf-8")
    records = list(csv.DictReader(io.StringIO(text)))
    assert_no_pathology_in_artifact(records[0].keys() if records else ())
    donors = [str(r["donor_id"]) for r in records]
    if len(donors) != len(set(donors)):
        duplicates = sorted({d for d in donors if donors.count(d) > 1})
        raise AssertionError("%s: %s" % (STOP_DUPLICATE_DONOR, duplicates))

    rows = []
    for record in records:
        row = {
            "donor_id": str(record["donor_id"]),
            "at8_available": _boolean(record["at8_available"],
                                      what="at8_available", allow_text=True),
            "technical_complete": _boolean(record["technical_complete"],
                                           what="technical_complete",
                                           allow_text=True),
            "age_present": _boolean(record["age_present"], what="age_present",
                                    allow_text=True),
            "sex_present": _boolean(record["sex_present"], what="sex_present",
                                    allow_text=True),
            "eligible": _boolean(record["eligible"], what="eligible",
                                 allow_text=True),
            "split_hash": str(record["split_hash"]),
            "donor_role": str(record["donor_role"]),
        }
        # The split hash is recomputed rather than trusted.
        recomputed = split_hash(row["donor_id"])
        if row["split_hash"] != recomputed:
            raise AssertionError(
                "%s: %s carries split hash %s but the frozen rule yields %s"
                % (STOP_ROLE_RULE, row["donor_id"], row["split_hash"],
                   recomputed))
        rows.append(row)

    if expected_candidate_donors is not None:
        expected = {str(d) for d in expected_candidate_donors}
        if set(donors) != expected:
            raise AssertionError(
                "%s: registry-only %s, expected-only %s"
                % (STOP_PARENT_COVERAGE, sorted(set(donors) - expected),
                   sorted(expected - set(donors))))

    assert_predicate_holds_on_every_row(rows)

    # The role assignment is re-derived, not trusted. A registry that carries a
    # role the frozen rule would not produce is refused even when every digest
    # in the package is internally consistent, because a self-consistent package
    # with a swapped role is exactly the artifact this check exists to catch.
    assert_roles_agree_with_frozen_rule(rows)

    root = eligible_donor_root(rows)
    if root != str(expected_eligible_donor_root_sha256):
        raise AssertionError("%s: eligible donor root is %s, expected %s"
                             % (STOP_ROOT_MISMATCH, root,
                                expected_eligible_donor_root_sha256))
    role_root = donor_role_root(rows)
    if role_root != str(expected_donor_role_root_sha256):
        raise AssertionError("%s: donor role root is %s, expected %s"
                             % (STOP_ROOT_MISMATCH, role_root,
                                expected_donor_role_root_sha256))

    meta = json.loads(captured[METADATA].decode("utf-8"))
    if meta.get("schema") != SCHEMA or meta.get("finalized") is not True:
        raise AssertionError("%s: metadata schema or finalized flag invalid"
                             % STOP_FIELD_SCHEMA)
    if meta.get("eligible_donor_root_sha256") != root:
        raise AssertionError("%s: metadata records %r but the registry yields %s"
                             % (STOP_ROOT_MISMATCH,
                                meta.get("eligible_donor_root_sha256"), root))
    if meta.get("donor_role_root_sha256") != role_root:
        raise AssertionError("%s: metadata records role root %r, recomputed %s"
                             % (STOP_ROOT_MISMATCH,
                                meta.get("donor_role_root_sha256"), role_root))
    if not isinstance(meta.get("parents"), dict) or not meta["parents"]:
        raise AssertionError("%s: the package names no parent authorities"
                             % STOP_PARENT_IDENTITY)
    recomputed_parent = parent_contract_root(meta["parents"])
    if str(meta.get("parent_contract_root_sha256")) != recomputed_parent:
        raise AssertionError(
            "%s: stored parent contract root %r does not match the root "
            "recomputed from the stored parents %s"
            % (STOP_PARENT_IDENTITY, meta.get("parent_contract_root_sha256"),
               recomputed_parent))
    if recomputed_parent != str(expected_parent_contract_root_sha256):
        raise AssertionError("%s: parent contract root is %s, expected %s"
                             % (STOP_PARENT_IDENTITY, recomputed_parent,
                                expected_parent_contract_root_sha256))
    counted_roles: dict[str, int] = {}
    for row in rows:
        counted_roles[row["donor_role"]] = counted_roles.get(
            row["donor_role"], 0) + 1
    eligible_count = sum(1 for row in rows if row["eligible"])
    for field, produced in (("candidate_donors", len(rows)),
                            ("eligible_donors", eligible_count)):
        if int(meta.get(field, -1)) != produced:
            raise AssertionError("%s: metadata %s is %r but the registry has %d"
                                 % (STOP_COUNTS_MISMATCH, field,
                                    meta.get(field), produced))
    if {k: int(v) for k, v in dict(meta.get("role_counts") or {}).items()
            } != counted_roles:
        raise AssertionError("%s: metadata role_counts %r, registry %r"
                             % (STOP_COUNTS_MISMATCH, meta.get("role_counts"),
                                counted_roles))
    if int(meta.get("confirmation_donors", -1)) != CONFIRMATION_DONORS:
        raise AssertionError("%s: metadata confirmation_donors is %r, frozen %d"
                             % (STOP_ROLE_RULE, meta.get("confirmation_donors"),
                                CONFIRMATION_DONORS))
    if str(meta.get("binding_role_rule")) != ROLE_AUTHORITY_RULE:
        raise AssertionError("%s: metadata binding_role_rule is %r, expected %r"
                             % (STOP_ROLE_RULE, meta.get("binding_role_rule"),
                                ROLE_AUTHORITY_RULE))

    for flag in ("numeric_at8_value_read", "numeric_at8_value_emitted",
                 "numeric_covariate_values_emitted",
                 "pathology_fields_in_artifact", "real_execution_ready"):
        if meta.get(flag) is not False:
            raise AssertionError("%s: %s must be False"
                                 % (STOP_FIELD_SCHEMA, flag))

    # No numeric value may appear anywhere in the registry beyond the booleans
    # and the hex split hash.
    for record in records:
        for field, value in record.items():
            if field in ("donor_id", "split_hash", "donor_role"):
                continue
            _boolean(value, what="%s for %s" % (field, record["donor_id"]),
                     allow_text=True)

    return {"rows": tuple(rows), "metadata": meta,
            "eligible_donor_root_sha256": root,
            "donor_role_root_sha256": role_root,
            "parent_contract_root_sha256": recomputed_parent,
            "package_root_sha256": pkg_root}


# ---------------------------------------------------------------------------
# Agreement with the frozen role authority.
#
# Two frozen modules assign roles and they are not equivalent:
#
#   t0_discovery_confirmation_split_v2.generate(support)
#       ranks every SEA_AD op31 support donor and takes the first 18.
#   t0_donor_role_authority_v2.build_role_authority(support, metadata)
#       ranks only the metadata-complete donors and takes the first 18.
#
# They coincide only when every support donor is eligible. If any ineligible
# donor ranks inside the top 18 of the full support set, the two disagree, and
# the role authority is the binding one: it is the module that writes a package,
# re-derives the assignment on load, and refuses a registry that does not match
# the frozen rule. `generate()` is the split primitive, not the authority.
#
# This module reproduces the role-authority rule, over eligible donors only, and
# the function below states that correspondence executably rather than in prose.
# ---------------------------------------------------------------------------

ROLE_AUTHORITY_RULE = (
    "RANK_ELIGIBLE_DONORS_ONLY__NOT_ALL_SUPPORT_DONORS")


def roles_under_frozen_role_authority_rule(
        eligible_donor_ids: Iterable[str]) -> dict[str, str]:
    """The frozen rule of `build_role_authority`, restated over a donor set.

    Ranks the given donors by `(split_hash, donor_id)`, calls the first 18
    CONFIRMATION and the rest DISCOVERY. Refuses a set that cannot carry the
    frozen design rather than returning a smaller one.
    """
    donors = [str(d) for d in eligible_donor_ids]
    if len(donors) != len(set(donors)):
        duplicates = sorted({d for d in donors if donors.count(d) > 1})
        raise AssertionError("%s: %s" % (STOP_DUPLICATE_DONOR, duplicates))
    if len(donors) < CONFIRMATION_DONORS + MINIMUM_DISCOVERY_DONORS:
        raise AssertionError(
            "%s: %d eligible donors cannot carry %d CONFIRMATION plus %d "
            "DISCOVERY" % (STOP_DESIGN_NOT_EXECUTABLE, len(donors),
                           CONFIRMATION_DONORS, MINIMUM_DISCOVERY_DONORS))
    ordered = sorted(donors, key=lambda d: (split_hash(d), d))
    confirmation = set(ordered[:CONFIRMATION_DONORS])
    return {d: ("CONFIRMATION" if d in confirmation else "DISCOVERY")
            for d in donors}


def assert_roles_agree_with_frozen_rule(
        rows: Sequence[Mapping[str, Any]]) -> bool:
    """Every emitted role must be the frozen rule's answer for that donor."""
    eligible = [str(row["donor_id"]) for row in rows if row["eligible"]]
    expected = roles_under_frozen_role_authority_rule(eligible)
    for row in rows:
        donor = str(row["donor_id"])
        want = expected.get(donor, "INELIGIBLE")
        if str(row["donor_role"]) != want:
            raise AssertionError("%s: %s is %r but the frozen rule says %r"
                                 % (STOP_ROLE_RULE, donor, row["donor_role"],
                                    want))
    return True


def split_rule_divergence(all_support_donors: Iterable[str],
                          eligible_donor_ids: Iterable[str]) -> dict[str, Any]:
    """Report whether the two frozen role paths agree on this donor set.

    Diagnostic only: it emits no role decision. It exists so the divergence is
    measured on the real donor set instead of argued about.
    """
    support = [str(d) for d in all_support_donors]
    eligible = [str(d) for d in eligible_donor_ids]
    ineligible = sorted(set(support) - set(eligible))
    ranked_support = sorted(support, key=lambda d: (split_hash(d), d))
    top18_of_support = set(ranked_support[:CONFIRMATION_DONORS])
    authority = roles_under_frozen_role_authority_rule(eligible)
    authority_confirmation = {d for d, role in authority.items()
                              if role == "CONFIRMATION"}
    return {
        "support_donors": len(support),
        "eligible_donors": len(eligible),
        "ineligible_donors": ineligible,
        "ineligible_donors_inside_support_top_18": sorted(
            set(ineligible) & top18_of_support),
        "confirmation_under_generate": sorted(top18_of_support),
        "confirmation_under_role_authority": sorted(authority_confirmation),
        "paths_agree": top18_of_support == authority_confirmation,
        "binding_rule": ROLE_AUTHORITY_RULE,
    }
