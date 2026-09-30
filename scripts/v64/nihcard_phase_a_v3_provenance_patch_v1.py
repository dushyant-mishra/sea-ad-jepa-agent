#!/usr/bin/env python3
"""Provenance-only successor patch to the Phase-A V3 receipt. No science is touched.

WHAT WENT WRONG. The V3 receipt recorded the RNA/ATAC pairing closeout as an unbound
receipt. That was false: the receipt was on the same branch at
results/v64/V64_NIH_CARD_PAIRING_EXECUTION_RECEIPT_V1.json, together with the NIH-CARD
byte-authentication receipt beside it. I had earlier listed that directory through a
keyword filter written for a different purpose, and nothing named PAIRING or
AUTHENTICATION could match it; I then relied on that stale impression instead of looking
again. A false missing-artifact claim is worse than an ordinary slip, because the natural remedy is to
regenerate the artifact -- here, rerunning authenticated pairing work that was already
done and already receipted.

WHY THIS IS A SUCCESSOR AND NOT AN IN-PLACE EDIT. The original receipt is left exactly as
written so the defect and its repair are both inspectable. Editing provenance in place
would erase the evidence that the gap was ever recorded.

HOW "PROVENANCE-ONLY" IS PROVEN RATHER THAN ASSERTED. Every top-level key except
PROVENANCE is compared byte-for-byte between the original and the successor under a
canonical JSON serialisation, and the patch refuses to write if any of them differs. The
PROVENANCE sub-keys that must survive untouched -- the emitted-artifact hashes, the
supplement bindings, the master seed, the frozen constants -- are checked the same way.
So the claim "no scientific count, funnel stage, control draw, artifact row, seed,
threshold or sampler output changed" is enforced by the code, not by my description of it.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys

SRC = "results/v64/phase_a_v3/PHASE_A_V3_RECEIPT.json"
DST = "results/v64/phase_a_v3/PHASE_A_V3_RECEIPT_PROVENANCE_PATCHED_V1.json"
PAIRING = "results/v64/V64_NIH_CARD_PAIRING_EXECUTION_RECEIPT_V1.json"
AUTHN = "results/v64/V64_NIH_CARD_LOCAL_BYTE_AUTHENTICATION_V1.json"
PRODUCER = "scripts/v64/nihcard_stage3_phase_a_full_funnel_successor_v3.py"

EXPECT = {
    PAIRING: "d51b9206b05064cb0d2e44fa162ef8d30c848cb5",
    AUTHN: "d0f85fb22ca584f0976dbcf76e5546ff9808a922",
    PRODUCER: "b08242247cc7a9e891c1eb11424434959e60df67",
}
PRODUCER_SHA = "9c33865e3da5250584e19988686928bc1fe9f2300c74bad4bf00c2a46fc28fba"
LIFTOVER_PATH = "C:/Users/dushy/jepa_c3/liftOver_v479"
LIFTOVER_SHA = "80c77de53b8bbd5fec661242f24d4b2f0ac54446df6954d934d1a838927dd19c"


class Stop(Exception):
    pass


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def blob(p):
    return subprocess.run(["git", "rev-parse", f"HEAD:{p}"], capture_output=True,
                          text=True, check=True).stdout.strip()


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def main() -> int:
    orig = json.load(open(SRC))

    # ---- every binding is verified against the repository before it is written
    for p, want in EXPECT.items():
        if not os.path.exists(p):
            raise Stop(f"{p} does not exist")
        got = blob(p)
        if got != want:
            raise Stop(f"git blob mismatch for {p}: {got} != {want}")
    if sha256(PRODUCER) != PRODUCER_SHA:
        raise Stop("producer sha256 changed since the run; the receipt would be false")
    if orig["PROVENANCE"]["producer_sha256"] != PRODUCER_SHA:
        raise Stop("original receipt producer_sha256 does not match the audited value")
    if not os.path.exists(LIFTOVER_PATH):
        raise Stop(f"liftOver binary absent at {LIFTOVER_PATH}")
    if sha256(LIFTOVER_PATH) != LIFTOVER_SHA:
        raise Stop("liftOver binary digest differs from the audited value")

    new = copy.deepcopy(orig)
    P = new["PROVENANCE"]

    P["producer_git_blob"] = EXPECT[PRODUCER]
    P["producer_git_blob_note"] = (
        "blob of the producer at the audited repository state; the producer_sha256 above "
        "is the digest of the same bytes and is unchanged")

    P["pairing_closeout_receipt"] = dict(
        path=PAIRING, git_blob=EXPECT[PAIRING], sha256=sha256(PAIRING),
        committed_in_git=True,
        note="RNA/ATAC pairing closeout. Previously and incorrectly recorded as an "
             "unbound receipt; the artifact was present on this branch the whole time. "
             "Pairing was NOT rerun.")

    P["nihcard_byte_authentication_receipt"] = dict(
        path=AUTHN, git_blob=EXPECT[AUTHN], sha256=sha256(AUTHN),
        committed_in_git=True,
        note="authoritative byte authentication for the NIH-CARD RNA and ATAC inputs")

    # bind the inputs THROUGH the authentication receipt rather than carrying loose MD5s
    for key, label in (("nihcard_rna_h5ad", "RNA"), ("nihcard_atac_h5ad", "ATAC")):
        e = P[key]
        e["authenticated_by"] = dict(path=AUTHN, git_blob=EXPECT[AUTHN])
        e["md5"] = e.pop("md5_from_authentication")
        e["committed_in_git"] = False
        e["note"] = (f"{label} matrix bytes are referenced by size and MD5 and are NOT "
                     f"committed; the authority for those values is the byte "
                     f"authentication receipt bound above, not this line")

    P["liftover_binary"] = dict(
        path=LIFTOVER_PATH, sha256=LIFTOVER_SHA, committed_in_git=False,
        note="the binary's BYTES ARE NOT IN GIT. It is referenced by path and digest "
             "only, and reproducing this run requires obtaining liftOver v479 with this "
             "exact digest independently.")

    P.pop("receipts_not_bound_here", None)
    P["binding_completeness"] = dict(
        all_v2_required_provenance_items_bound=True,
        items=["producer path", "producer sha256", "producer git blob",
               "Phase-A V2 contract sha256", "feature-artifact V2 contract sha256",
               "E2 table sha256", "NIH-CARD RNA byte receipt",
               "NIH-CARD ATAC byte receipt", "RNA/ATAC pairing closeout receipt",
               "NIH-CARD peak-source identity and digest", "Nott PU.1 track digest",
               "liftOver binary digest", "hg19ToHg38 chain digest",
               "hg38ToHg19 chain digest",
               "exact supplement shard receipts and aggregate binding",
               "master seed", "frozen constants", "emitted artifact hashes"],
        artifacts_hash_bound_but_not_committed=[
            "PHASE_A_V3_ROWS.jsonl.gz", "PHASE_A_V3_FUNNEL_PER_EDGE.jsonl.gz",
            "NIH-CARD RNA and ATAC h5ad matrices", "liftOver v479 binary"],
        practical_limitation="byte-level independent reinspection of the row and "
                             "per-edge artifacts requires those exact external files; "
                             "the hashes prove identity, they do not supply the bytes")

    new["PATCH"] = dict(
        schema="V64_PHASE_A_V3_PROVENANCE_ONLY_PATCH_V1", date="2026-09-30",
        supersedes_receipt=dict(path=SRC, sha256=sha256(SRC)),
        original_left_unmodified=True,
        scope="PROVENANCE ONLY. No scientific count, funnel stage, control draw, "
              "artifact row, seed, threshold or sampler output is changed.",
        phase_a_not_rerun=True,
        what_changed=["added producer_git_blob",
                      "bound the RNA/ATAC pairing closeout receipt by path, git blob "
                      "and sha256, replacing an incorrect unbound-receipt entry",
                      "bound the NIH-CARD byte authentication receipt by path, git blob "
                      "and sha256",
                      "routed the RNA/ATAC matrix identities through the authentication "
                      "receipt instead of carrying loose md5_from_authentication values",
                      "made liftOver custody explicit with committed_in_git=false",
                      "removed the receipts_not_bound_here entry",
                      "added binding_completeness"],
        why_the_unbound_claim_was_wrong="the pairing receipt was on this branch throughout. "
              "It was missed because an earlier directory listing had been filtered by "
              "keywords chosen for a different purpose, and that stale impression was "
              "relied on instead of searching again.")

    # ---- prove provenance-only, rather than asserting it
    changed = [k for k in set(orig) | set(new)
               if k not in ("PROVENANCE", "PATCH")
               and canon(orig.get(k)) != canon(new.get(k))]
    if changed:
        raise Stop(f"patch altered non-provenance keys: {changed}")
    for k in ("emitted_artifacts", "supplement_shard_receipt_sha256",
              "supplement_aggregate_binding", "master_seed", "frozen_constants",
              "e2_table_sha256", "producer_sha256", "phase_a_v2_contract_sha256",
              "feature_artifact_v2_contract_sha256", "nihcard_peaks_bed",
              "nott_pu1_hg38_sha256", "chain_hg19ToHg38_sha256",
              "chain_hg38ToHg19_sha256", "builder_sha256",
              "historical_executor_sha256", "producer_path"):
        if canon(orig["PROVENANCE"].get(k)) != canon(P.get(k)):
            raise Stop(f"patch altered preserved provenance key: {k}")

    # ---- emitted artifacts must still be exactly the bytes the run produced
    for name, e in P["emitted_artifacts"].items():
        if not os.path.exists(e["path"]):
            raise Stop(f"emitted artifact missing: {e['path']}")
        if os.path.getsize(e["path"]) != e["bytes"] or sha256(e["path"]) != e["sha256"]:
            raise Stop(f"emitted artifact changed since the run: {name}")

    with open(DST, "w", newline="\n") as fh:
        json.dump(new, fh, indent=2)

    print("PROVENANCE-ONLY PATCH WRITTEN")
    print(f"  source   {SRC}")
    print(f"  successor{'':1} {DST}")
    print(f"  non-provenance keys changed : {len(changed)}")
    print(f"  preserved provenance keys   : verified identical")
    print(f"  emitted artifacts re-hashed : "
          f"{len(P['emitted_artifacts'])} match the run exactly")
    print(f"  funnel (unchanged)          : "
          f"{json.dumps(new['PRIMARY_FUNNEL'], separators=(',', ':'))[:180]}")
    print(f"  patched receipt sha256      : {sha256(DST)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
