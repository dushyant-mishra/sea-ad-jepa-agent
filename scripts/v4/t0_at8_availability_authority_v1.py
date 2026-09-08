"""T0 AT8 availability-only authority.

The frozen V18 donor-role contract needs a per-donor boolean `AT8_available`.
That predicate is the only thing this module is authorized to derive from the
frozen SEA-AD donor pathology source. Numeric AT8 values may not be parsed,
retained, emitted, logged, ranked, summarized, compared or modelled here, and
the emitted registry carries only donor identity and the boolean.

The value-blindness is structural rather than promised:

* the source is read with the `csv` module, so every field arrives as text and
  nothing is coerced. No pandas, and no `float`, `int`, `to_numeric`, `astype`,
  `mean` or `sum` call appears anywhere in this file; a test asserts that by
  walking this module's own AST, because a conversion would be a latent leak
  even where today's path does not emit its result;
* the raw AT8 text is consumed inside `_is_available` and reduced to a boolean
  there. It is never bound to a name that outlives that call, never stored on a
  row, and never written to any artifact;
* the behavioural proof is metamorphic. Replacing every numeric value while
  holding presence fixed must leave `availability_root_sha256` byte-identical,
  and blanking one value must change it. `package_root_sha256` is a different
  claim: it binds the source digest and the derivation code, so it is expected
  to move whenever the source bytes move.

The raw field text is read in order to decide missingness, which is the whole
point, so the metadata says exactly that rather than the looser claim that no
outcome value was read: the token is read, and it is never parsed numerically,
never retained and never emitted.

Availability means present and non-missing, so a measured zero is available. A
zero is a measurement, not an absence, and treating it as missing would silently
drop donors from the role pool.

Nothing here authorizes real T0 execution: the metadata records
`real_execution_ready` false, and donor roles remain a separate step gated on
independent verification of this authority.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "JEPA_T0_AT8_AVAILABILITY_AUTHORITY_V1"
NAMESPACE = "T0-AT8-AVAILABILITY-V1"

AT8_FIELD = "percent AT8 positive area_Grey matter"
DONOR_ID_FIELD = "Donor ID"

# Frozen missingness vocabulary, compared case-insensitively after stripping.
# Deliberately does not include "0": a measured zero is a measurement.
NA_TOKENS = ("", "na", "n/a", "nan", "none", "null", ".")

REGISTRY = "T0_AT8_AVAILABILITY_REGISTRY.csv"
METADATA = "T0_AT8_AVAILABILITY_METADATA.json"
MANIFEST = "T0_AT8_AVAILABILITY_MANIFEST.csv"
ROOT_FILE = "T0_AT8_AVAILABILITY_PACKAGE_ROOT_SHA256.txt"
MEMBERS = (REGISTRY, METADATA)

STOP_SOURCE_DIGEST = "STOP_T0_AT8_PATHOLOGY_SOURCE_DIGEST_MISMATCH"
STOP_FIELD_ABSENT = "STOP_T0_AT8_FIELD_ABSENT"
STOP_ID_FIELD_ABSENT = "STOP_T0_AT8_DONOR_ID_FIELD_ABSENT"
STOP_IDENTITY = "STOP_T0_AT8_DONOR_IDENTITY_NOT_UNIQUE"
STOP_MEMBERSHIP = "STOP_T0_AT8_MEMBERSHIP_DONOR_UNRESOLVED"
STOP_OUTPUT = "STOP_T0_AT8_OUTPUT_NOT_EMPTY"
STOP_PACKAGE = "STOP_T0_AT8_AVAILABILITY_PACKAGE_INVALID"
STOP_SOURCE_PATH = "STOP_T0_AT8_SOURCE_PATH_NOT_PORTABLE"
STOP_CODE_DIGEST = "STOP_T0_AT8_DERIVATION_CODE_DIGEST_MALFORMED"
STOP_PACKAGE_CONTENTS = "STOP_T0_AT8_AVAILABILITY_PACKAGE_CONTENTS_UNEXPECTED"
STOP_EXTERNAL_ROOT = "STOP_T0_AT8_AVAILABILITY_EXTERNAL_ROOT_MISMATCH"


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_available(raw_field_text: str) -> bool:
    """Presence predicate over the raw field text.

    The argument is text and stays text. It is compared against the frozen
    missingness vocabulary and discarded; no numeric interpretation occurs, so
    the result cannot depend on the magnitude, sign or precision of a value.
    """
    stripped = str(raw_field_text).strip()
    return stripped.lower() not in NA_TOKENS


def read_authenticated_source(
    source_path: Path | str, expected_source_sha256: str
) -> bytes:
    """Read the source once and authenticate those exact bytes.

    Hashing the path and then reopening it later is a time-of-check to
    time-of-use hole: the recorded digest could describe one revision of the
    file while availability was derived from another. The authenticated bytes
    are therefore returned and everything downstream parses them from memory;
    the path is never reopened, and the recorded byte count is the length of
    these bytes rather than a later filesystem stat.

    Runs before the output directory is created, so a source STOP leaves no
    artifact behind at all.
    """
    payload = Path(source_path).read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    if actual != str(expected_source_sha256):
        raise AssertionError(
            "%s: %s has digest %s, expected %s"
            % (STOP_SOURCE_DIGEST, Path(source_path).as_posix(), actual,
               expected_source_sha256)
        )
    return payload


def derive_availability(authenticated_source_bytes: bytes) -> list[dict[str, str]]:
    """Return one `{donor_id, AT8_available}` row per donor, in UTF-8 order.

    Parses the authenticated bytes from memory, so the derivation cannot drift
    from the digest that was verified. The AT8 column is reduced to a boolean
    inside this function and never leaves it in any other form.
    """
    handle = io.StringIO(bytes(authenticated_source_bytes).decode("utf-8-sig"))
    reader = csv.DictReader(handle)
    columns = list(reader.fieldnames or [])
    if AT8_FIELD not in columns:
        raise AssertionError("%s: %r is not in the source header"
                             % (STOP_FIELD_ABSENT, AT8_FIELD))
    if DONOR_ID_FIELD not in columns:
        raise AssertionError("%s: %r is not in the source header"
                             % (STOP_ID_FIELD_ABSENT, DONOR_ID_FIELD))
    rows = []
    for record in reader:
        donor = str(record.get(DONOR_ID_FIELD) or "").strip()
        available = _is_available(record.get(AT8_FIELD) or "")
        rows.append({"donor_id": donor, "AT8_available": str(bool(available))})

    identities = [row["donor_id"] for row in rows]
    if any(not identity for identity in identities):
        raise AssertionError("%s: blank donor identity present" % STOP_IDENTITY)
    if len(set(identities)) != len(identities):
        raise AssertionError("%s: %d rows carry %d distinct donor identities"
                             % (STOP_IDENTITY, len(identities), len(set(identities))))
    return sorted(rows, key=lambda row: row["donor_id"].encode("utf-8"))


def _write_flat_package(outdir: Path, payloads: Mapping[str, bytes]) -> str:
    """Write a package whose manifest authenticates the caller's exact bytes.

    The manifest is derived from the in-memory payload buffers before any member
    is written. Hashing paths after writing creates another check/use interval:
    a same-length substitution between `write_bytes` and `sha256_file` can make
    the returned package root describe bytes the builder never intended.

    By committing to `payloads` first, any subsequent filesystem substitution
    makes the frozen directory fail verification against the returned roots
    instead of silently becoming the authority.
    """
    outdir.mkdir(parents=True, exist_ok=True)

    captured = {str(name): bytes(blob) for name, blob in payloads.items()}
    manifest_buffer = io.StringIO()
    writer = csv.writer(manifest_buffer, lineterminator="\n")
    writer.writerow(["filename", "bytes", "sha256"])
    for name in sorted(captured, key=lambda value: value.encode("utf-8")):
        blob = captured[name]
        writer.writerow([name, len(blob), hashlib.sha256(blob).hexdigest()])
    manifest_bytes = manifest_buffer.getvalue().encode("utf-8")
    root = hashlib.sha256(manifest_bytes).hexdigest()

    frozen = {
        **captured,
        MANIFEST: manifest_bytes,
        ROOT_FILE: (root + "\n").encode("utf-8"),
    }
    for name, blob in frozen.items():
        (outdir / name).write_bytes(blob)
    return root


def _donor_set_digest(donor_ids: Iterable[str]) -> str:
    """Canonical digest over an exact donor-identity set."""
    ordered = sorted({str(donor).strip() for donor in donor_ids},
                     key=lambda value: value.encode("utf-8"))
    digest = hashlib.sha256()
    digest.update(b"T0_DONOR_IDENTITY_SET_V1")
    for donor in ordered:
        digest.update(b"|")
        digest.update(donor.encode("utf-8"))
    return digest.hexdigest()


def _portable_source_identity(source_relative_path: str) -> str:
    """Require a portable, repository-relative source identity.

    An absolute path is environment noise, not provenance: the same authority
    built from the same bytes on another machine would carry a different
    metadata string and therefore a different package root. The digest is the
    identity; the path is only a label, so the label must be portable.
    """
    label = str(source_relative_path)
    if any(character in label for character in ("\x00", "\\", ":")):
        raise AssertionError(
            "%s: %r is not a portable repository-relative path" % (STOP_SOURCE_PATH, label)
        )
    if any(part in ("", ".", "..") for part in label.split("/")):
        raise AssertionError(
            "%s: %r is not a portable repository-relative path" % (STOP_SOURCE_PATH, label)
        )
    return label


def build_availability_authority(
    *,
    outdir: Path | str,
    source_path: Path | str,
    expected_source_sha256: str,
    membership_donor_ids: Iterable[str],
    source_relative_path: str,
    derivation_code_sha256: str,
) -> dict[str, Any]:
    """Freeze the availability-only authority for the given pathology source."""
    authenticated = read_authenticated_source(source_path, expected_source_sha256)
    source_digest = hashlib.sha256(authenticated).hexdigest()
    source_label = _portable_source_identity(source_relative_path)
    code_digest = str(derivation_code_sha256).strip().lower()
    if len(code_digest) != 64 or any(c not in "0123456789abcdef" for c in code_digest):
        raise AssertionError("%s: %r is not a SHA-256 hex digest"
                             % (STOP_CODE_DIGEST, derivation_code_sha256))

    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: %s must be absent or empty"
                             % (STOP_OUTPUT, out.as_posix()))

    rows = derive_availability(authenticated)
    by_donor = {row["donor_id"]: row["AT8_available"] for row in rows}

    membership = sorted({str(donor).strip() for donor in membership_donor_ids},
                        key=lambda value: value.encode("utf-8"))
    unresolved = [donor for donor in membership if donor not in by_donor]
    if unresolved:
        raise AssertionError("%s: %d of %d membership donors are absent from the "
                             "source: %r" % (STOP_MEMBERSHIP, len(unresolved),
                                             len(membership), unresolved[:5]))

    available_rows = [row for row in rows if row["AT8_available"] == "True"]
    membership_available = [donor for donor in membership if by_donor[donor] == "True"]

    registry_buffer = io.StringIO()
    writer = csv.writer(registry_buffer, lineterminator="\n")
    writer.writerow(["donor_id", "AT8_available"])
    for row in rows:
        writer.writerow([row["donor_id"], row["AT8_available"]])
    registry_bytes = registry_buffer.getvalue().encode("utf-8")

    metadata = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "finalized": True,
        "at8_field": AT8_FIELD,
        "donor_id_field": DONOR_ID_FIELD,
        "missingness_tokens": list(NA_TOKENS),
        "availability_semantics": (
            "present and non-missing after stripping and case-folding against the "
            "frozen missingness vocabulary; a measured zero is available"
        ),
        "source_relative_path": source_label,
        "source_bytes": len(authenticated),
        "source_sha256": source_digest,
        # Supplied by the caller, not computed from __file__. This module is a
        # tracked file, so its on-disk bytes are platform-transformed: hashing
        # them recorded a digest that no fresh checkout could reproduce. The
        # caller passes the Git blob digest, which is the stable identity.
        "derivation_code_sha256": code_digest,
        "derivation_code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES",
        "total_donor_count": len(rows),
        "available_donor_count": len(available_rows),
        "membership_donor_count": len(membership),
        "membership_donors_available": len(membership_available),
        "membership_fully_available": len(membership_available) == len(membership),
        # A count alone does not identify a donor set. With every donor
        # available, any 46 of the 84 would satisfy "46 of 46", so the claim is
        # only meaningful alongside a digest of the exact set it refers to.
        "membership_donor_set_sha256": _donor_set_digest(membership),
        "root_byte_semantics": (
            "DISK_BYTES_AS_WRITTEN__NEVER_STORE_THIS_PACKAGE_AS_CRLF_FILTERED_TRACKED_TEXT"
        ),
        "verification_rule": (
            "Reproduce by rebuilding from the frozen source digest with the recorded "
            "derivation code; do not hash a Git-checked-out copy, because a platform "
            "line-ending transform changes the bytes and therefore the root."
        ),
        # Precise, because "no outcome value was read" was not literally true:
        # the raw token must be read to decide missingness.
        "raw_at8_token_read_for_missingness": True,
        "numeric_at8_value_parsed": False,
        "numeric_at8_value_retained": False,
        "numeric_at8_value_emitted": False,
        "real_execution_ready": False,
        "claim": (
            "Availability predicate only. This authority does not qualify any "
            "biological association and does not authorize real T0 execution."
        ),
    }
    metadata_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")

    package_root = _write_flat_package(
        out, {REGISTRY: registry_bytes, METADATA: metadata_bytes}
    )
    # Two roots, because they carry two different claims and conflating them
    # would make the value-blindness claim uncheckable.
    #
    # `availability_root_sha256` covers the derived predicate alone. It must be
    # invariant to every numeric AT8 value, and a metamorphic attack asserts
    # exactly that by rebuilding from a source whose values all differ.
    #
    # `package_root_sha256` covers the manifest, so it binds the source digest
    # and the derivation code. It is *expected* to change when the source bytes
    # change; that is provenance working, not leakage.
    return {
        "availability_root_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "package_root_sha256": package_root,
        "registry": rows,
        "metadata": metadata,
    }


def load_availability_authority(
    outdir: Path | str,
    *,
    expected_package_root_sha256: str,
    expected_availability_root_sha256: str,
) -> dict[str, Any]:
    """Re-verify a frozen availability package from bytes captured exactly once.

    The previous implementation authenticated each member by path and then
    reopened the metadata and registry to parse them. That interval was
    exploitable and the exploit was demonstrated: replacing the metadata with a
    same-length forgery immediately after its authenticated hash read produced a
    loader result carrying `membership_donor_set_sha256` of all zeros while both
    external roots were still reported correct. Authentication and use must
    therefore act on the same bytes, exactly as the source-side repair does.

    So: enumerate the directory, refuse a symlink or reparse-point member,
    refuse anything but the four known files, read each member once into memory,
    verify every length and digest from those captured bytes, compute the
    manifest and availability roots from those captured bytes, compare both
    against the externally supplied roots, and parse only from the captured
    buffers. No package member is reopened after authentication.
    """
    out = Path(outdir)
    expected_contents = sorted([*MEMBERS, MANIFEST, ROOT_FILE])

    present: dict[str, Path] = {}
    for item in sorted(out.rglob("*"), key=lambda value: value.as_posix()):
        relative = item.relative_to(out).as_posix()
        if item.is_symlink():
            raise AssertionError("%s: %s is a symlink or reparse point"
                                 % (STOP_PACKAGE_CONTENTS, relative))
        if item.is_dir():
            raise AssertionError("%s: %s is a directory; the package is flat"
                                 % (STOP_PACKAGE_CONTENTS, relative))
        present[relative] = item
    if sorted(present) != expected_contents:
        raise AssertionError(
            "%s: directory holds %r, expected exactly %r"
            % (STOP_PACKAGE_CONTENTS, sorted(present), expected_contents)
        )

    # Capture once. Everything below reads only from `captured`.
    captured = {relative: path.read_bytes() for relative, path in present.items()}

    manifest_text = captured[MANIFEST].decode("utf-8")
    declared = list(csv.DictReader(io.StringIO(manifest_text)))
    names = [record["filename"] for record in declared]
    if sorted(names) != sorted(MEMBERS):
        raise AssertionError("%s: manifest members %r are not %r"
                             % (STOP_PACKAGE, sorted(names), sorted(MEMBERS)))
    for record in declared:
        name = record["filename"]
        if name not in captured:
            raise AssertionError("%s: %s is absent" % (STOP_PACKAGE, name))
        payload = captured[name]
        if str(len(payload)) != str(record["bytes"]):
            raise AssertionError("%s: %s is %d bytes, manifest says %s"
                                 % (STOP_PACKAGE, name, len(payload), record["bytes"]))
        actual = hashlib.sha256(payload).hexdigest()
        if actual != record["sha256"]:
            raise AssertionError("%s: %s digest %s does not match manifest %s"
                                 % (STOP_PACKAGE, name, actual, record["sha256"]))

    recorded_root = captured[ROOT_FILE].decode("utf-8").strip()
    actual_root = hashlib.sha256(captured[MANIFEST]).hexdigest()
    if recorded_root != actual_root:
        raise AssertionError("%s: recorded root %s is not the manifest digest %s"
                             % (STOP_PACKAGE, recorded_root, actual_root))
    availability_root = hashlib.sha256(captured[REGISTRY]).hexdigest()

    # The decisive checks, against values supplied from OUTSIDE this directory.
    if actual_root != str(expected_package_root_sha256):
        raise AssertionError(
            "%s: package root %s is not the expected %s"
            % (STOP_EXTERNAL_ROOT, actual_root, expected_package_root_sha256)
        )
    if availability_root != str(expected_availability_root_sha256):
        raise AssertionError(
            "%s: availability root %s is not the expected %s"
            % (STOP_EXTERNAL_ROOT, availability_root, expected_availability_root_sha256)
        )

    metadata = json.loads(captured[METADATA].decode("utf-8"))
    if metadata.get("schema") != SCHEMA or metadata.get("namespace") != NAMESPACE:
        raise AssertionError("%s: metadata identity mismatch" % STOP_PACKAGE)
    if metadata.get("real_execution_ready") is not False:
        raise AssertionError("%s: availability authority may not claim readiness"
                             % STOP_PACKAGE)

    rows = []
    reader = csv.DictReader(io.StringIO(captured[REGISTRY].decode("utf-8")))
    if list(reader.fieldnames or []) != ["donor_id", "AT8_available"]:
        raise AssertionError("%s: registry columns are not the two authorized columns"
                             % STOP_PACKAGE)
    for record in reader:
        if record["AT8_available"] not in ("True", "False"):
            raise AssertionError("%s: %s carries a non-boolean availability"
                                 % (STOP_PACKAGE, record["donor_id"]))
        rows.append(dict(record))
    if len(rows) != metadata["total_donor_count"]:
        raise AssertionError("%s: registry row count disagrees with metadata"
                             % STOP_PACKAGE)
    available = [row for row in rows if row["AT8_available"] == "True"]
    if len(available) != metadata["available_donor_count"]:
        raise AssertionError("%s: available count disagrees with metadata"
                             % STOP_PACKAGE)

    return {
        "availability_root_sha256": availability_root,
        "package_root_sha256": actual_root,
        "registry": rows,
        "metadata": metadata,
        "authenticated_member_bytes": {name: len(blob)
                                       for name, blob in sorted(captured.items())},
    }