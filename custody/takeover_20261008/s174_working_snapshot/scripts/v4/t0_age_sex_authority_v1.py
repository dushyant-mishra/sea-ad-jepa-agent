"""Pathology-blind donor demographics authority for T0.

Why this exists
---------------
`t0_donor_role_authority_v2` consumes `age` and `sex` for the eligibility
predicate and for the nuisance design, and until now they were handed to it as an
informal frame. Eligibility is the statistical population, so each of its
conjuncts needs an authority behind it rather than a caller-assembled table.

The source is the frozen SEA-AD MTG donor table, whose columns `Age at Death` and
`Sex` are read here. That same file also carries the AT8 magnitude and every other
pathology endpoint, so the discipline that matters in this module is what it does
NOT read: no pathology column is parsed, retained or emitted, and the module
asserts that its own emitted schema contains no pathology field.

What the design actually requires of these two columns
------------------------------------------------------
`nuisance_design` builds `[1, age_c, age_c^2, sex]` and refuses any donor set
whose sex encoding is not complete binary. So a single-sex donor set is a hard
build-time failure of the role authority rather than a silent degeneracy, and
that is the correct behaviour: it is a design failure, not a biological
NOT_MEASURABLE, and the split must never be altered to rescue it. This authority
therefore reports the sex composition it found, so the condition is visible
before the split is computed rather than after.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "JEPA_T0_AGE_SEX_AUTHORITY_V1"
NAMESPACE = "T0-AGE-SEX-V1"
DOMAIN_TAG = "T0-AGE-SEX-V1-TYPED-LENGTH-PREFIXED"

REGISTRY = "T0_AGE_SEX_REGISTRY.csv"
METADATA = "T0_AGE_SEX_METADATA.json"
MANIFEST = "T0_AGE_SEX_MANIFEST.csv"
ROOT_FILE = "T0_AGE_SEX_PACKAGE_ROOT_SHA256.txt"
MEMBERS = (REGISTRY, METADATA, MANIFEST)

STOP_SOURCE_DIGEST = "STOP_T0_AGE_SEX_SOURCE_DIGEST_MISMATCH"
STOP_COLUMNS = "STOP_T0_AGE_SEX_REQUIRED_COLUMN_ABSENT"
STOP_DUPLICATE_DONOR = "STOP_T0_AGE_SEX_DUPLICATE_DONOR"
STOP_DONOR_SET = "STOP_T0_AGE_SEX_CANDIDATE_DONOR_SET_MISMATCH"
STOP_AGE_INVALID = "STOP_T0_AGE_SEX_AGE_NOT_FINITE_NUMBER"
STOP_SEX_INVALID = "STOP_T0_AGE_SEX_SEX_NOT_IN_FROZEN_VOCABULARY"
STOP_PATHOLOGY_LEAK = "STOP_T0_AGE_SEX_PATHOLOGY_FIELD_IN_EMITTED_SCHEMA"
STOP_ROOT_MISMATCH = "STOP_T0_AGE_SEX_ROOT_MISMATCH"
STOP_PACKAGE_MEMBER = "STOP_T0_AGE_SEX_PACKAGE_MEMBER_INVALID"
STOP_FIELD_SCHEMA = "STOP_T0_AGE_SEX_FIELD_SCHEMA_VIOLATION"

# Frozen source identity and the two columns this authority is permitted to read.
SOURCE_RELATIVE_PATH = "data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv"
SOURCE_SHA256 = "ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a"
DONOR_ID_FIELD = "Donor ID"
AGE_FIELD = "Age at Death"
SEX_FIELD = "Sex"
PERMITTED_SOURCE_FIELDS = (DONOR_ID_FIELD, AGE_FIELD, SEX_FIELD)

SEX_VOCABULARY = ("Female", "Male")
EMITTED_FIELDS = ("donor_id", "age", "sex")
PRODUCTION_DONORS = 46

# Any substring here appearing in an emitted field name would mean a pathology
# endpoint had leaked into this authority's schema.
PATHOLOGY_MARKERS = ("at8", "6e10", "gfap", "iba1", "neun", "abeta", "ptau",
                     "ttau", "braak", "thal", "cerad", "positive area")


def _typed(value: Any) -> bytes:
    """Type-tagged, length-prefixed framing; injective over the declared types."""
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


def _rows(raw: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    text = bytes(raw).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return tuple(reader.fieldnames or ()), [dict(row) for row in reader]


def exact_age(value: Any, *, what: str) -> int:
    """Accept an exact non-negative integer age.

    The frozen source column is clean `int64` with no censored `"90+"` string, so
    an integer is required rather than coerced. A float would make the authority
    root depend on binary formatting.
    """
    if isinstance(value, bool):
        raise AssertionError("%s: %s is a bool" % (STOP_AGE_INVALID, what))
    if isinstance(value, int):
        number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text or not text.isdigit():
            raise AssertionError("%s: %s is %r" % (STOP_AGE_INVALID, what, value))
        number = int(text)
    else:
        raise AssertionError("%s: %s is %r" % (STOP_AGE_INVALID, what, type(value)))
    if number < 0:
        raise AssertionError("%s: %s is %d" % (STOP_AGE_INVALID, what, number))
    return number


def exact_sex(value: Any, *, what: str) -> str:
    """Accept only the frozen vocabulary. `nuisance_design` needs complete binary."""
    text = str(value).strip()
    if text not in SEX_VOCABULARY:
        raise AssertionError("%s: %s is %r, expected one of %s"
                            % (STOP_SEX_INVALID, what, value, list(SEX_VOCABULARY)))
    return text


def assert_no_pathology_in_emitted_schema(
        fields: Iterable[str] = EMITTED_FIELDS) -> bool:
    """The emitted schema must carry no pathology endpoint.

    The source file this reads is the donor pathology table, so the meaningful
    guarantee is about what leaves this module, not about what it opened.
    """
    for field in fields:
        lowered = str(field).lower()
        for marker in PATHOLOGY_MARKERS:
            if marker in lowered:
                raise AssertionError("%s: emitted field %r matches %r"
                                    % (STOP_PATHOLOGY_LEAK, field, marker))
    return True


def read_demographics(
        *,
        source_bytes: bytes,
        expected_source_sha256: str = SOURCE_SHA256,
        candidate_donors: Sequence[str] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Authenticate the source, then read ONLY donor id, age and sex from it.

    The bytes are authenticated before anything is parsed, and only the three
    permitted columns are touched. Rows outside the candidate universe are
    ignored rather than refused, because the source table covers 84 donors while
    the T0 candidate universe is 46 of them.
    """
    payload = bytes(source_bytes)
    actual = hashlib.sha256(payload).hexdigest()
    if actual != str(expected_source_sha256):
        raise AssertionError("%s: source is %s, expected %s"
                            % (STOP_SOURCE_DIGEST, actual, expected_source_sha256))

    columns, records = _rows(payload)
    for required in PERMITTED_SOURCE_FIELDS:
        if required not in columns:
            raise AssertionError("%s: source lacks %r" % (STOP_COLUMNS, required))

    wanted = None if candidate_donors is None else {str(d) for d in candidate_donors}
    seen: dict[str, dict[str, Any]] = {}
    for record in records:
        donor = str(record[DONOR_ID_FIELD]).strip()
        if wanted is not None and donor not in wanted:
            continue
        if donor in seen:
            raise AssertionError("%s: %s appears more than once in the source"
                                % (STOP_DUPLICATE_DONOR, donor))
        seen[donor] = {
            "donor_id": donor,
            "age": exact_age(record[AGE_FIELD], what="age for %s" % donor),
            "sex": exact_sex(record[SEX_FIELD], what="sex for %s" % donor),
        }

    if wanted is not None and set(seen) != wanted:
        raise AssertionError(
            "%s: source-only %s, candidate-only %s"
            % (STOP_DONOR_SET, sorted(set(seen) - wanted), sorted(wanted - set(seen))))

    assert_no_pathology_in_emitted_schema()
    # Deterministic ordering, by UTF-8 bytes, matching the frozen role builder.
    return tuple(seen[donor] for donor in
                 sorted(seen, key=lambda d: d.encode("utf-8")))


def sex_composition(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Counts per sex, so a degenerate design is visible before the split."""
    return {value: sum(1 for row in rows if row["sex"] == value)
            for value in SEX_VOCABULARY}


def age_sex_root(rows: Sequence[Mapping[str, Any]]) -> str:
    """Digest over the bound demographics, with explicit cardinality."""
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(list(EMITTED_FIELDS)), _typed(len(rows))]
    for row in rows:
        parts.append(_typed([str(row["donor_id"]), int(row["age"]),
                             str(row["sex"])]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def package_root(members: Mapping[str, bytes]) -> str:
    names = sorted(members)
    parts = [_typed(DOMAIN_TAG), _typed("PACKAGE"), _typed(len(names))]
    for name in names:
        parts.append(_typed([name,
                             hashlib.sha256(bytes(members[name])).hexdigest()]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def build_production_authority(
        outdir: Path | str,
        *,
        source_bytes: bytes,
        expected_source_sha256: str = SOURCE_SHA256,
        candidate_donors: Sequence[str],
        derivation_code_sha256: str,
        expected_donors: int = PRODUCTION_DONORS,
) -> dict[str, Any]:
    """Authenticate the source, read the two columns, and package.

    Bytes in, package out. The candidate donor set must be supplied and matched
    exactly, because a demographics authority covering the wrong donors would
    silently change the statistical population.
    """
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output directory must be absent or empty: %s"
                            % (STOP_PACKAGE_MEMBER, out))
    if not _is_hex64(derivation_code_sha256):
        raise AssertionError("%s: derivation_code_sha256 is not a lowercase hex sha256"
                            % STOP_FIELD_SCHEMA)

    payload = bytes(source_bytes)
    rows = read_demographics(source_bytes=payload,
                             expected_source_sha256=expected_source_sha256,
                             candidate_donors=candidate_donors)
    if len(rows) != int(expected_donors):
        raise AssertionError("%s: %d donors, expected %d"
                            % (STOP_DONOR_SET, len(rows), int(expected_donors)))

    root = age_sex_root(rows)
    composition = sex_composition(rows)

    registry = io.StringIO()
    writer = csv.writer(registry, lineterminator="\n")
    writer.writerow(list(EMITTED_FIELDS))
    for row in rows:
        writer.writerow([row["donor_id"], int(row["age"]), row["sex"]])
    registry_bytes = registry.getvalue().encode("utf-8")

    ages = sorted(int(row["age"]) for row in rows)
    meta = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "finalized": True,
        "donor_count": len(rows),
        "emitted_fields": list(EMITTED_FIELDS),
        "age_sex_root_sha256": root,
        "source_relative_path": SOURCE_RELATIVE_PATH,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "source_fields_read": list(PERMITTED_SOURCE_FIELDS),
        "derivation_code_sha256": str(derivation_code_sha256),
        "derivation_code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES",
        "sex_vocabulary": list(SEX_VOCABULARY),
        "sex_composition": composition,
        "age_min": ages[0], "age_max": ages[-1],
        "age_distinct_values": len(set(ages)),
        "ordering": "DONOR_ID_ASCENDING_BY_UTF8_BYTES",
        "nuisance_design_note": (
            "nuisance_design builds [1, age_c, age_c^2, sex] and refuses any donor "
            "set whose sex encoding is not complete binary. A single-sex donor set "
            "is therefore a loud build-time failure of the role authority, not a "
            "biological NOT_MEASURABLE, and the split must not be altered to rescue "
            "it. The composition is reported here so the condition is visible before "
            "the split is computed."),
        "numeric_at8_value_read": False,
        "numeric_at8_value_emitted": False,
        "pathology_fields_in_emitted_schema": False,
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

    return {"age_sex_root_sha256": root, "package_root_sha256": pkg_root,
            "donor_count": len(rows), "sex_composition": composition,
            "source_sha256": meta["source_sha256"],
            "real_execution_ready": False}


def load_authority(
        outdir: Path | str,
        *,
        expected_package_root_sha256: str,
        expected_age_sex_root_sha256: str,
        expected_source_sha256: str,
        expected_derivation_code_sha256: str | None = None,
) -> dict[str, Any]:
    """Read the authority back, binding its source identity externally."""
    out = Path(outdir)
    captured: dict[str, bytes] = {}
    for name in MEMBERS:
        path = out / name
        if not path.is_file():
            raise AssertionError("%s: %s absent" % (STOP_PACKAGE_MEMBER, path))
        captured[name] = path.read_bytes()

    pkg_root = package_root(captured)
    if pkg_root != str(expected_package_root_sha256):
        raise AssertionError("%s: package root is %s, expected %s"
                            % (STOP_ROOT_MISMATCH, pkg_root,
                               expected_package_root_sha256))

    columns, records = _rows(captured[REGISTRY])
    for required in EMITTED_FIELDS:
        if required not in columns:
            raise AssertionError("%s: registry lacks %r" % (STOP_COLUMNS, required))
    rows = tuple({"donor_id": str(r["donor_id"]).strip(),
                  "age": exact_age(r["age"], what="age for %s" % r["donor_id"]),
                  "sex": exact_sex(r["sex"], what="sex for %s" % r["donor_id"])}
                 for r in records)
    root = age_sex_root(rows)
    if root != str(expected_age_sex_root_sha256):
        raise AssertionError("%s: age/sex root is %s, expected %s"
                            % (STOP_ROOT_MISMATCH, root,
                               expected_age_sex_root_sha256))

    meta = json.loads(captured[METADATA].decode("utf-8"))
    if meta.get("schema") != SCHEMA or meta.get("finalized") is not True:
        raise AssertionError("%s: metadata schema or finalized flag invalid"
                            % STOP_FIELD_SCHEMA)
    if meta.get("age_sex_root_sha256") != root:
        raise AssertionError("%s: metadata records %r but the registry yields %s"
                            % (STOP_ROOT_MISMATCH, meta.get("age_sex_root_sha256"),
                               root))
    if str(meta.get("source_sha256")) != str(expected_source_sha256):
        raise AssertionError("%s: source is stored as %r, externally expected %r"
                            % (STOP_ROOT_MISMATCH, meta.get("source_sha256"),
                               expected_source_sha256))
    if expected_derivation_code_sha256 is not None:
        if str(meta.get("derivation_code_sha256")) != str(expected_derivation_code_sha256):
            raise AssertionError(
                "%s: derivation code is stored as %r, externally expected %r"
                % (STOP_ROOT_MISMATCH, meta.get("derivation_code_sha256"),
                   expected_derivation_code_sha256))
    if meta.get("numeric_at8_value_emitted") is not False:
        raise AssertionError("%s: this authority must emit no AT8 value"
                            % STOP_PATHOLOGY_LEAK)
    assert_no_pathology_in_emitted_schema(meta.get("emitted_fields") or ())
    if meta.get("real_execution_ready") is not False:
        raise AssertionError("%s: real_execution_ready must be False"
                            % STOP_FIELD_SCHEMA)
    return {"rows": rows, "metadata": meta, "age_sex_root_sha256": root,
            "package_root_sha256": pkg_root}
