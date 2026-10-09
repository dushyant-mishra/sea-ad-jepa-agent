#!/usr/bin/env python3
"""S174 custody: prove that a transfer archive of the corrected TRAIN cache holds exactly the cache
that the S174 lane built and G1b authorized. Custody only; it changes no S174 finding.

Authorities, read from the committed S174 records (never from the archive):
  rebuilt HVS/SEA-AD shards  results/v77/S174_REBUILD_BUILD_RECEIPT_V1.json  (h5_shards: counts/meta sha256)
                             cross-checked against the G1b freeze's rebuilt_cache.shards, which G1b R7
                             verified the cache against (results/v77/S174_REBUILD_G1B_RESULT_V1.json)
  carried-over NPH shards    results/v77/S174_REBUILD_FREEZE_V1.json         (nph_shards: counts/meta sha256)

Procedure: hash the archive; list its members; run the archiver's own integrity test; extract into a NEW
directory that must not exist and must not lie inside the live cache; then, for every expected member,
compare the authority digest, the live canonical cache file and the extracted file.

Fails closed on: archive test or extraction error, a missing member, an extra member, a duplicate
basename, a byte-size mismatch, a digest mismatch, or a live cache that is not exactly the 84 expected
files. Nothing is regenerated or repaired.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REC = ROOT / "results" / "v77"
PASS = "PASS_S174_RAR_EXACTLY_MATCHES_G1B_AUTHORIZED_CORRECTED_CACHE"
FAIL = "FAIL_S174_RAR_DOES_NOT_MATCH_G1B_AUTHORIZED_CORRECTED_CACHE"


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name: str) -> dict:
    return json.loads((REC / name).read_text(encoding="utf-8"))


def authorities() -> tuple[dict, dict]:
    """Expected basename -> authority sha256, plus the provenance of that expectation."""
    build, freeze = load("S174_REBUILD_BUILD_RECEIPT_V1.json"), load("S174_REBUILD_FREEZE_V1.json")
    g1b_freeze, g1b = load("S174_REBUILD_G1B_FREEZE_V1.json"), load("S174_REBUILD_G1B_RESULT_V1.json")
    exp, origin = {}, {}
    for s in build["h5_shards"]:
        for kind in ("counts", "meta"):
            name = f"{s['stem']}.{kind}.npz"
            exp[name], origin[name] = s[f"{kind}_sha256"], f"rebuilt {s['matrix_id']}"
    for s in freeze["nph_shards"]:
        for kind in ("counts", "meta"):
            name = f"{s['stem']}.{kind}.npz"
            assert name not in exp, f"stem in both rebuilt and NPH sets: {name}"
            exp[name], origin[name] = s[f"{kind}_sha256"], "NPH carried over unchanged (freeze)"
    g1b_shards = g1b_freeze["rebuilt_cache"]["shards"]
    g1b_consistent = (len(g1b_shards) == len(build["h5_shards"]) and all(
        g1b_shards[s["stem"]]["counts"] == s["counts_sha256"] and g1b_shards[s["stem"]]["meta"] == s["meta_sha256"]
        for s in build["h5_shards"]))
    build_sha = sha_file(REC / "S174_REBUILD_BUILD_RECEIPT_V1.json")
    chain = dict(
        records={n: sha_file(REC / n) for n in ("S174_REBUILD_FREEZE_V1.json", "S174_REBUILD_BUILD_RECEIPT_V1.json",
                                                "S174_REBUILD_G1B_FREEZE_V1.json", "S174_REBUILD_G1B_RESULT_V1.json")},
        rebuilt_shards=len(build["h5_shards"]), nph_shards=len(freeze["nph_shards"]),
        g1b_freeze_shards_equal_build_receipt=g1b_consistent,
        g1b_freeze_cites_this_build_receipt=g1b_freeze["rebuilt_cache"]["build_receipt_sha256"] == build_sha,
        g1b_pass=g1b["G1b_pass"], g1b_r7_bytes_identical=g1b["requirements"].get("R7"),
        freeze_new_cache_path=freeze["new_cache"])
    return exp, dict(origin=origin, chain=chain)


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def files_under(d: Path) -> list[Path]:
    return sorted(p for p in d.rglob("*") if p.is_file())


def verify(rar: Path, cache: Path, extract_dir: Path, unrar: Path) -> dict:
    t0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reasons = []
    exp, prov = authorities()
    chain = prov["chain"]
    if not (chain["g1b_freeze_shards_equal_build_receipt"] and chain["g1b_freeze_cites_this_build_receipt"]
            and chain["g1b_pass"] and chain["g1b_r7_bytes_identical"]):
        reasons.append("authority chain inconsistent")
    if len(exp) != 84:
        reasons.append(f"authorities name {len(exp)} files, not 84")
    archive = dict(path=str(rar.resolve()), bytes=rar.stat().st_size, sha256=sha_file(rar), verification_utc=t0)
    version = run([str(unrar)]).stdout.strip().splitlines()[0] if run([str(unrar)]).stdout.strip() else None
    listing = run([str(unrar), "lb", "--", str(rar)])
    members = [ln.strip() for ln in listing.stdout.splitlines() if ln.strip()]
    archive.update(member_count=len(members), members=members, list_exit=listing.returncode)
    test = run([str(unrar), "t", "-idq", "--", str(rar)])
    archive.update(integrity_test_exit=test.returncode)
    if listing.returncode or test.returncode:
        reasons.append("archive listing or integrity test failed")
    # extraction target: new, empty, outside the live cache
    ext, live = extract_dir.resolve(), cache.resolve()
    if ext == live or live in ext.parents or ext in live.parents:
        raise SystemExit("refusing: extraction directory overlaps the live cache")
    if ext.exists():
        raise SystemExit(f"refusing: extraction directory already exists: {ext}")
    ext.mkdir(parents=True)
    x = run([str(unrar), "x", "-o-", "-idq", "--", str(rar), str(ext) + os.sep])
    if x.returncode:
        reasons.append(f"extraction failed (exit {x.returncode}): {x.stderr.strip()[:300]}")
    extracted = files_under(ext)
    base = Counter(p.name for p in extracted)
    dup = sorted(n for n, c in base.items() if c > 1)
    if dup:
        reasons.append(f"duplicate basenames: {dup}")
    extra = sorted(n for n in base if n not in exp)
    missing = sorted(n for n in exp if n not in base)
    if extra:
        reasons.append(f"extra members: {extra}")
    if missing:
        reasons.append(f"missing members: {missing}")
    live_files = files_under(live)
    live_names = Counter(p.name for p in live_files)
    live_extra = sorted(n for n in live_names if n not in exp)
    live_missing = sorted(n for n in exp if n not in live_names)
    if live_extra or live_missing or any(c > 1 for c in live_names.values()):
        reasons.append(f"live cache is not exactly the expected set (extra {live_extra}, missing {live_missing})")
    # every listed entry is either an extracted file or a directory record; anything else fails closed
    dirs = sorted(p.relative_to(ext).as_posix() for p in ext.rglob("*") if p.is_dir())
    non_file = [m for m in members if m not in base]
    unexplained = [m for m in non_file if m not in {Path(d).name for d in dirs}]
    if unexplained:
        reasons.append(f"listed entries that are neither files nor directories: {unexplained}")
    archive.update(layout=dict(
        listing_note=("UnRAR 4.00 prints member names without their directory; extraction shows where each file "
                      "is stored"),
        directory_records=non_file, extracted_directories=dirs,
        file_members=len(members) - len(non_file)))
    by_name = {p.name: p for p in extracted}
    rows = []
    for name in sorted(exp):
        c, e = live / name, by_name.get(name)
        cs = sha_file(c) if c.exists() else None
        es = sha_file(e) if e is not None else None
        row = dict(relative_path=name, archive_path=e.relative_to(ext).as_posix() if e is not None else None,
                   origin=prov["origin"][name], authority_sha256=exp[name],
                   canonical_bytes=c.stat().st_size if c.exists() else None, canonical_sha256=cs,
                   extracted_bytes=e.stat().st_size if e is not None else None, extracted_sha256=es)
        row["canonical_matches_authority"] = cs == exp[name]
        row["extracted_matches_authority"] = es == exp[name]
        row["bytes_equal"] = row["canonical_bytes"] is not None and row["canonical_bytes"] == row["extracted_bytes"]
        row["exact_match"] = row["canonical_matches_authority"] and row["extracted_matches_authority"] and row["bytes_equal"]
        rows.append(row)
    bad = [r["relative_path"] for r in rows if not r["exact_match"]]
    if bad:
        reasons.append(f"{len(bad)} members do not match exactly: {bad[:10]}")
    matched = sum(r["exact_match"] for r in rows)
    pairs = len({n.split(".")[0] for n in exp})
    return dict(
        schema="S174_LOCAL_CACHE_TRANSFER_VERIFICATION_V1",
        terminal=PASS if not reasons else FAIL, failure_reasons=reasons,
        scope="custody/transfer verification only; no S174 finding is changed; nothing regenerated or repaired",
        archive=archive, archiver=dict(path=str(unrar), version=version),
        extraction=dict(directory=str(ext), files=len(extracted), exit=x.returncode,
                        rule="new directory outside the live cache; -o- never overwrite"),
        canonical_cache=dict(root=str(live), files=len(live_files),
                             bytes=sum(p.stat().st_size for p in live_files)),
        expected=dict(files=len(exp), counts_meta_pairs=pairs),
        exact_matches=f"{matched}/{len(exp)}",
        authority_chain=chain, members=rows,
        code_sha256=sha_file(Path(__file__)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rar", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--extract-dir", required=True)
    ap.add_argument("--unrar", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rec = verify(Path(a.rar), Path(a.cache), Path(a.extract_dir), Path(a.unrar))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")
    print(rec["terminal"], rec["exact_matches"], rec["failure_reasons"])


if __name__ == "__main__":
    main()
