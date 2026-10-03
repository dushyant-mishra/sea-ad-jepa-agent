#!/usr/bin/env python3
"""V69/V74 shared custody primitives: bind the BYTES, never the path or the size.

WHY THIS MODULE EXISTS. The V69 Route-B producers checked that the 63.6 GB fragment
file still had the byte LENGTH recorded in its acquisition receipt, and then copied the
acquisition receipt's SHA-256 into their own receipt as if they had verified it. Two
separate defects live in that pattern:

  1. SIZE IS NOT IDENTITY. A file can be corrupted, truncated-and-repadded, partially
     overwritten, or replaced by a different file of the same length, and a length check
     cannot see any of it. `assert_bytes_match` and `HashingReader` close this.

  2. A COPIED DIGEST IS AN ASSERTION, NOT A MEASUREMENT. Writing
     `"fragments_sha256": acq["sha256"]` into a downstream receipt makes that receipt
     look cryptographically bound when nothing was hashed. The downstream receipt is
     then a claim about history that the run did not establish. Every digest this
     module reports was computed from bytes this process actually read, and every field
     carries a `digest_source` saying so.

STREAMING VERIFICATION, NOT A SEPARATE REHASH. `HashingReader` digests the compressed
bytes as they are handed to the decompressor, so the digest covers exactly the bytes the
run consumed. A standalone rehash followed by a separate read has a time-of-check /
time-of-use gap between them; this does not. It also avoids a redundant 63.6 GB read.

The cost is that the verdict is only available at end of stream. Producers must
therefore write their outputs to a staging directory and promote them only after the
digest matches -- see `StagedOutputDir`.

UNMEASURED IS A VALID VALUE. When a quantity was not measured (for example the full-file
digest during a deliberately truncated smoke scan), these helpers return an explicit
`UNVERIFIED__*` string. They never substitute a plausible-looking number, and they never
encode "not measured" as zero.
"""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

CHUNK = 8 << 20

#: Honest value for a digest that this run did not compute. Never a number, never None,
#: never silently omitted -- a reader of the receipt must be able to see the absence.
UNVERIFIED_PARTIAL = "UNVERIFIED__PARTIAL_SCAN_DID_NOT_READ_WHOLE_FILE"
UNMEASURED = "UNMEASURED"


class CustodyError(Exception):
    """Raised when bytes on disk do not match the identity they are claimed to have."""

    def __init__(self, status: str, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def sha256_file(path, chunk: int = CHUNK) -> str:
    """SHA-256 of a file, computed here and now from the bytes on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def assert_bytes_match(observed: str, expected: str, *, label: str, path) -> None:
    """Fail closed unless two digests are equal. Case-insensitive, whitespace-tolerant."""
    o = str(observed).strip().lower()
    e = str(expected).strip().lower()
    if o != e:
        raise CustodyError(
            "FAIL__BOUND_FILE_DIGEST_MISMATCH",
            label=label, path=str(path), expected_sha256=e, observed_sha256=o,
            note=("The bytes on disk are not the bytes the authority names. Size "
                  "agreement, if any, is irrelevant: size is not identity."))


def bind_file(path, *, label: str, role: str, expected_sha256: str | None = None,
              expected_bytes: int | None = None, digest: bool = True) -> dict:
    """Return a content identity for `path`, verifying it against an authority.

    `expected_sha256` / `expected_bytes` come from the authenticated authority (an
    acquisition receipt, a cohort freeze, an upstream producer receipt). Either may be
    omitted, and the returned record says plainly which checks were performed, so a
    reader can never mistake an unchecked field for a verified one.

    Raises CustodyError on a missing file, a size mismatch or a digest mismatch.
    """
    p = Path(path)
    if not p.is_file():
        raise CustodyError("FAIL__BOUND_FILE_MISSING", label=label, path=str(p),
                           role=role)
    size = p.stat().st_size
    if expected_bytes is not None and size != int(expected_bytes):
        raise CustodyError("FAIL__BOUND_FILE_BYTES_MISMATCH", label=label,
                           path=str(p), expected_bytes=int(expected_bytes),
                           observed_bytes=size)
    rec = {
        "label": label,
        "role": role,
        "path": str(p),
        "bytes": size,
        "expected_bytes": (int(expected_bytes) if expected_bytes is not None
                           else UNMEASURED),
        "bytes_checked_against_authority": expected_bytes is not None,
    }
    if digest:
        observed = sha256_file(p)
        rec["sha256"] = observed
        rec["digest_source"] = "COMPUTED_FROM_BYTES_READ_BY_THIS_RUN"
        if expected_sha256 is not None:
            assert_bytes_match(observed, expected_sha256, label=label, path=p)
            rec["expected_sha256"] = str(expected_sha256).strip().lower()
            rec["digest_checked_against_authority"] = True
        else:
            rec["expected_sha256"] = UNMEASURED
            rec["digest_checked_against_authority"] = False
    else:
        rec["sha256"] = UNMEASURED
        rec["digest_source"] = "NOT_COMPUTED"
        rec["digest_checked_against_authority"] = False
    return rec


class HashingReader:
    """A read-only binary wrapper that digests every byte it hands out.

    Wrap the raw file object BEFORE the decompressor, so the digest covers the stored
    bytes -- the same bytes the acquisition receipt hashed -- rather than the
    decompressed stream.

    After the consumer has finished, call `drain()` so any bytes the consumer did not
    request (gzip trailers, a short tail) are still read and digested; only then is
    `hexdigest()` a whole-file digest. `complete` reports whether end of file was
    actually reached, so a truncated consume can never be mistaken for a full one.
    """

    def __init__(self, path, chunk: int = CHUNK):
        self._path = Path(path)
        self._fh = open(self._path, "rb")
        self._h = hashlib.sha256()
        self._chunk = chunk
        self.n_bytes = 0
        self.eof = False

    # -- file-object protocol used by gzip.GzipFile(fileobj=...) ------------------
    def read(self, size: int = -1) -> bytes:
        b = self._fh.read(size) if size is not None else self._fh.read()
        if not b:
            self.eof = True
        else:
            self._h.update(b)
            self.n_bytes += len(b)
        return b

    def readinto(self, buf) -> int:  # pragma: no cover - gzip uses read()
        n = self._fh.readinto(buf)
        if not n:
            self.eof = True
        else:
            self._h.update(memoryview(buf)[:n])
            self.n_bytes += n
        return n

    def seekable(self) -> bool:
        # Declaring this unseekable is deliberate. If a consumer could seek backwards
        # the digest would double-count or skip bytes and would silently stop being a
        # whole-file digest.
        return False

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def tell(self) -> int:
        return self.n_bytes

    def close(self) -> None:
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # -- digest -------------------------------------------------------------------
    def drain(self) -> None:
        """Read and digest anything the consumer left unread, up to end of file."""
        while True:
            b = self._fh.read(self._chunk)
            if not b:
                self.eof = True
                break
            self._h.update(b)
            self.n_bytes += len(b)

    @property
    def complete(self) -> bool:
        """True only if every byte of the file has passed through the digest."""
        return self.eof and self.n_bytes == self._path.stat().st_size

    def hexdigest(self) -> str:
        return self._h.hexdigest()


class StagedOutputDir:
    """Write outputs somewhere provisional; promote only once custody is proven.

    A streaming digest is only decidable at end of stream, so a producer that writes
    straight into its final output directory will leave files there even when the input
    turns out not to be the authenticated input. Those files look exactly like valid
    outputs. This class makes the failure visible instead: on failure the staging
    directory is renamed to a `__QUARANTINE_FAILED_CUSTODY` sibling and the final
    directory is never created.
    """

    def __init__(self, final_dir):
        self.final = Path(final_dir)
        self.staging = self.final.parent / (self.final.name + "__STAGING")
        self.quarantine = self.final.parent / (self.final.name
                                               + "__QUARANTINE_FAILED_CUSTODY")

    def open(self) -> Path:
        if self.staging.exists():
            shutil.rmtree(self.staging)
        self.staging.mkdir(parents=True, exist_ok=True)
        return self.staging

    def promote(self) -> Path:
        if self.final.exists():
            shutil.rmtree(self.final)
        os.replace(self.staging, self.final)
        return self.final

    def quarantine_failed(self) -> str:
        if self.quarantine.exists():
            shutil.rmtree(self.quarantine)
        if self.staging.exists():
            os.replace(self.staging, self.quarantine)
            return str(self.quarantine)
        return "NOTHING_STAGED"


def remap(p, host_prefix: str, container_prefix: str) -> Path:
    """Translate a host path recorded in a receipt to its bind-mounted location.

    Receipts record the absolute HOST path at which an artifact actually lived. That is
    the honest provenance record and is deliberately never rewritten. A producer running
    inside a container sees the same bytes at a different mount point, so the
    translation is applied at read time, explicitly, and recorded in the output receipt.

    Same contract as build_routea_cistopic_object_v1.remap, lifted here so Route-B and
    Route-A cannot drift apart. Matching is case-insensitive because the host prefix is
    a Windows path, and a path that does not start with the host prefix is returned
    unchanged rather than guessed at.
    """
    if not host_prefix:
        return Path(p)
    n = str(p).replace("\\", "/")
    h = host_prefix.replace("\\", "/").rstrip("/")
    if n.lower().startswith(h.lower()):
        return Path(container_prefix.rstrip("/") + n[len(h):])
    return Path(p)
