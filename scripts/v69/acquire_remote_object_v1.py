#!/usr/bin/env python3
"""V69 receipt-bound remote object acquisition with resume and remote-identity binding.

Acquisition tools report success on incomplete files. This utility therefore binds
every receipt to the *server-declared* object identity (Content-Length, Last-Modified,
ETag where offered) and refuses to emit a PASS receipt unless the locally stored byte
count equals the authoritative remote length exactly.

Fail-closed semantics:
  * no authoritative Content-Length  -> status REMOTE_LENGTH_UNAVAILABLE (never PASS)
  * local bytes != remote bytes      -> status INCOMPLETE
  * remote identity changed mid-run  -> status REMOTE_OBJECT_CHANGED
Only an exact byte-count match plus a computed SHA-256 yields PASS.

Never writes an estimated number into a receipt. Unmeasured quantities are emitted
as the literal string "UNMEASURED" or null, never as a plausible-looking value.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

CHUNK = 8 << 20


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def head(url: str, timeout: int = 120) -> dict:
    """Return the server-declared identity of the remote object."""
    proc = subprocess.run(
        ["curl", "-sIL", "--max-time", str(timeout), url],
        capture_output=True, text=True, check=False,
    )
    raw = proc.stdout
    ident = {
        "http_status": None,
        "content_length": None,
        "last_modified": None,
        "etag": None,
        "accept_ranges": None,
        "raw_header_sha256": hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest(),
    }
    for line in raw.splitlines():
        s = line.strip()
        low = s.lower()
        if low.startswith("http/"):
            parts = s.split()
            if len(parts) > 1:
                ident["http_status"] = parts[1]
        elif low.startswith("content-length:"):
            try:
                ident["content_length"] = int(s.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif low.startswith("last-modified:"):
            ident["last_modified"] = s.split(":", 1)[1].strip()
        elif low.startswith("etag:"):
            ident["etag"] = s.split(":", 1)[1].strip()
        elif low.startswith("accept-ranges:"):
            ident["accept_ranges"] = s.split(":", 1)[1].strip()
    return ident


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def fetch(url: str, dest: Path, expect_bytes: int, max_attempts: int = 12) -> list:
    """Resume-download until the local size equals expect_bytes. Returns attempt log."""
    log = []
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, max_attempts + 1):
        have = dest.stat().st_size if dest.exists() else 0
        if have == expect_bytes:
            log.append({"attempt": attempt, "action": "ALREADY_COMPLETE", "bytes_before": have})
            break
        if have > expect_bytes:
            log.append({"attempt": attempt, "action": "LOCAL_LARGER_THAN_REMOTE__ABORT",
                        "bytes_before": have, "remote_bytes": expect_bytes})
            break
        started = utcnow()
        proc = subprocess.run(
            ["curl", "-L", "--fail", "--retry", "5", "--retry-delay", "5",
             "--retry-all-errors", "-C", "-", "-o", str(dest), url],
            check=False,
        )
        after = dest.stat().st_size if dest.exists() else 0
        log.append({
            "attempt": attempt, "curl_returncode": proc.returncode,
            "bytes_before": have, "bytes_after": after,
            "started_utc": started, "finished_utc": utcnow(),
        })
        if after == expect_bytes:
            break
        if after == have and proc.returncode != 0:
            # no forward progress this attempt
            if attempt >= 3 and log[-2].get("bytes_after") == after:
                log.append({"attempt": attempt, "action": "NO_FORWARD_PROGRESS__ABORT"})
                break
    return log


def acquire(url: str, dest: Path, label: str, licence: str, recovery: str) -> dict:
    ident_pre = head(url)
    receipt = {
        "schema": "V69_REMOTE_OBJECT_ACQUISITION_RECEIPT_V1",
        "label": label,
        "source_url": url,
        "local_path": str(dest),
        "acquisition_started_utc": utcnow(),
        "remote_identity_before": ident_pre,
        "licence_terms": licence,
        "recovery_locator": recovery,
        "download_attempts": [],
        "remote_identity_after": None,
        "local_bytes": None,
        "sha256": None,
        "status": None,
    }
    expect = ident_pre.get("content_length")
    if expect is None:
        receipt["status"] = "REMOTE_LENGTH_UNAVAILABLE__NO_PASS_POSSIBLE"
        receipt["acquisition_finished_utc"] = utcnow()
        return receipt

    receipt["download_attempts"] = fetch(url, dest, expect)
    ident_post = head(url)
    receipt["remote_identity_after"] = ident_post
    local = dest.stat().st_size if dest.exists() else 0
    receipt["local_bytes"] = local

    if (ident_post.get("content_length") != expect
            or ident_post.get("last_modified") != ident_pre.get("last_modified")):
        receipt["status"] = "REMOTE_OBJECT_CHANGED_DURING_ACQUISITION"
        receipt["acquisition_finished_utc"] = utcnow()
        return receipt
    if local != expect:
        receipt["status"] = "INCOMPLETE__LOCAL_BYTES_NE_REMOTE_CONTENT_LENGTH"
        receipt["bytes_missing"] = expect - local
        receipt["acquisition_finished_utc"] = utcnow()
        return receipt

    receipt["sha256"] = sha256_file(dest)
    receipt["status"] = "PASS__BYTE_COMPLETE_AND_DIGESTED"
    receipt["acquisition_finished_utc"] = utcnow()
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--licence", required=True)
    ap.add_argument("--recovery", required=True)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    r = acquire(a.url, Path(a.dest), a.label, a.licence, a.recovery)
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({k: v for k, v in r.items() if k != "download_attempts"}, indent=2))
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
