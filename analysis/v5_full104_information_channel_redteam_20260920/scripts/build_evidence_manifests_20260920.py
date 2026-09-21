"""Build and verify the red-team lane's evidence manifests.

Produces two artifacts, both committed:

``EVIDENCE_SHA256.csv``
    Every committed file in this audit directory, with byte size and SHA-256.
    Regenerating it is the verification: a mismatch means a committed artifact
    changed without the manifest being rebuilt.

``EXTERNAL_ARTIFACTS.json``
    Every large artifact deliberately NOT committed, each carrying the full
    record the review protocol requires -- absolute GPU-machine path, byte size,
    SHA-256, producer Git SHA, producer script SHA-256, schema/role, whether it
    contains cell-level material, and ``GPU_MACHINE_NOT_COMMITTED``.

Why external artifacts are recorded rather than committed
---------------------------------------------------------
Committing row-level matrices would make the GitHub package self-contained at
the cost of pushing hundreds of megabytes of cell-level material into version
control. The review protocol's answer is content-addressing: a reviewer cannot
recompute the artifact from GitHub, but can verify that the artifact a machine
holds is byte-identical to the one the reported numbers came from, and every
aggregate needed to challenge the conclusion is committed alongside.

Cell-level material is flagged explicitly so that anything carrying per-cell
rows is visible as such rather than buried in a size field.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

LANE = Path("analysis/v5_full104_information_channel_redteam_20260920")
MANIFEST = LANE / "EVIDENCE_SHA256.csv"
EXTERNAL = LANE / "EXTERNAL_ARTIFACTS.json"
FIELDS = ("path", "bytes", "sha256", "location")


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


def git_head(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


#: Large artifacts held on the GPU machine. Each entry names its producer so a
#: reviewer can tell which code and which commit the bytes came from.
EXTERNAL_SPECS = [
    {
        "role": "AUDIT_A_PER_CELL_NORMALIZATION_DENOMINATOR",
        "path": "D:/jepa_full104_redteam_20260920_external/audit_a_cell_level_denominator_v1.npz",
        "bytes": 42283767,
        "sha256": "9ff45071fb09f5d89340a7cca76ab77ab826533f29e9dd80b33a821645283cd1",
        "producer_git_sha": "abcea57c1934ed70dea16fbad32e73b3d07d719d",
        "producer_script": "analysis/v5_full104_information_channel_redteam_20260920/scripts/"
                           "audit_a_normalization_denominator_20260920.py",
        "producer_script_sha256": "b1c7d745bacfd31bfd69c52fd1eda937644cffbb049e497eecd7641c9e9252ab",
        "schema": "V5_FULL104_NORMALIZATION_DENOMINATOR_AUDIT_V1",
        "contains_cell_level_material": True,
        "cell_level_content": "per-cell L_total, L_ledger, L_core, donor code, source code, "
                              "operator index for all 4,553,407 cells; keyed by selection_row "
                              "position, no raw cell identifiers",
        "why_not_committed": "4.55M rows across six int64 vectors; aggregate distributions and "
                             "every stratum table are committed instead",
        "reuse_status": "CURRENT_PRODUCER_SEMANTICS_UNCHANGED__CONTENT_ADDRESS_REUSE_ALLOWED",
    },
    {
        "role": "CORE_SUFFICIENT_STATISTICS_FOR_AUDITS_B_C_AND_E",
        "path": "D:/jepa_full104_redteam_20260920_external/core_sufficient_statistics_v1.npz",
        "bytes": 242087519,
        "sha256": "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae",
        "producer_git_sha": "abcea57c1934ed70dea16fbad32e73b3d07d719d",
        "producer_script": "analysis/v5_full104_information_channel_redteam_20260920/scripts/"
                           "build_core_sufficient_statistics_20260920.py",
        "producer_script_sha256": "230ae5420ca3daef1cd1b2743c7f9466bec96d71f8829afc7d7eb85cde2d639f",
        "schema": "V5_FULL104_CORE_SUFFICIENT_STATISTICS_V1",
        "contains_cell_level_material": True,
        "cell_level_content": "per-donor/per-address and stratum aggregates plus per-cell "
                              "library/source vectors keyed by selection_row position; no raw "
                              "cell identifiers",
        "why_not_committed": "large per-donor/per-address matrices plus cell-level vectors; "
                             "compact aggregate evidence is committed separately",
        "reuse_status": "REQUIRES_METADATA_ONLY_STRICT_PARSE_EQUIVALENCE_CHECK_BEFORE_REUSE",
    },
]


def build_external(repo: Path, head: str) -> dict:
    """Describe immutable external-artifact provenance without rewriting history.

    The artifact's producer commit/script hash belong to the bytes and therefore
    come from EXTERNAL_SPECS. The current checkout is recorded separately. A
    manifest rebuild must never relabel an old heavy artifact as if the current
    code produced it.
    """
    entries = []
    for spec in EXTERNAL_SPECS:
        path = Path(spec["path"])
        script = repo / spec["producer_script"]
        current_script_sha = sha256_file(script)[0] if script.is_file() else None
        local_state = "REFERENCED_NOT_LOCAL"
        local_verification = None
        if path.is_file():
            local_sha, local_size = sha256_file(path)
            if local_sha != spec["sha256"] or local_size != spec["bytes"]:
                local_state = "LOCAL_CONTENT_MISMATCH"
                local_verification = {
                    "observed_bytes": local_size,
                    "observed_sha256": local_sha,
                }
            else:
                local_state = "PRESENT_AND_CONTENT_VERIFIED"
                local_verification = "MATCH"
        entries.append({
            "role": spec["role"],
            "path": spec["path"],
            "bytes": spec["bytes"],
            "sha256": spec["sha256"],
            "producer_git_sha": spec["producer_git_sha"],
            "producer_script": spec["producer_script"],
            "producer_script_sha256": spec["producer_script_sha256"],
            "current_checkout_git_sha": head,
            "current_producer_script_sha256": current_script_sha,
            "producer_script_matches_current":
                current_script_sha == spec["producer_script_sha256"],
            "schema": spec["schema"],
            "contains_cell_level_material": spec["contains_cell_level_material"],
            "cell_level_content": spec["cell_level_content"],
            "why_not_committed": spec["why_not_committed"],
            "reuse_status": spec["reuse_status"],
            "state": local_state,
            "local_verification": local_verification,
            "location": "GPU_MACHINE_NOT_COMMITTED",
        })
    return {
        "schema": "V5_FULL104_REDTEAM_EXTERNAL_ARTIFACTS_V2_IMMUTABLE_PROVENANCE",
        "note": "Producer commit/script hashes are immutable properties of the referenced "
                "artifact bytes. Current checkout/script hashes are recorded separately so "
                "a manifest rebuild cannot falsely relabel historical heavy bytes as current.",
        "artifacts": entries,
        "training_authorized": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    head = git_head(repo)

    lane = repo / LANE
    if not lane.is_dir():
        raise SystemExit(f"audit lane not found: {lane}")

    rows = []
    for path in sorted(p for p in lane.rglob("*") if p.is_file()):
        rel = path.relative_to(repo).as_posix()
        if rel == (LANE / MANIFEST.name).as_posix():
            continue                      # a manifest cannot contain its own digest
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue                      # environment bytecode is never canonical evidence
        sha, size = sha256_file(path)
        rows.append({"path": rel, "bytes": str(size), "sha256": sha, "location": "repository"})

    manifest_path = repo / MANIFEST
    mismatches = []
    if manifest_path.is_file():
        prior = {r["path"]: r for r in csv.DictReader(manifest_path.open(newline="", encoding="utf-8"))}
        for row in rows:
            old = prior.get(row["path"])
            if old and (old["sha256"] != row["sha256"] or old["bytes"] != row["bytes"]):
                mismatches.append(row["path"])
        print(f"  previously recorded rows : {len(prior)}")
        print(f"  changed since last build : {len(mismatches)}")
        for path in mismatches[:20]:
            print("    CHANGED:", path)

    print(f"  repository files          : {len(rows)}")
    external = build_external(repo, head)
    present = sum(1 for a in external["artifacts"]
                  if a["state"] == "PRESENT_AND_CONTENT_VERIFIED")
    mismatched = [a["role"] for a in external["artifacts"]
                  if a["state"] == "LOCAL_CONTENT_MISMATCH"]
    print(f"  external artifacts        : {len(external['artifacts'])} "
          f"({present} locally content-verified)")
    if mismatched:
        raise SystemExit("external artifact content mismatch: " + ", ".join(mismatched))

    if args.write:
        with manifest_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        (repo / EXTERNAL).write_text(json.dumps(external, indent=2) + "\n", encoding="utf-8")
        print(f"\n  wrote {manifest_path}")
        print(f"  wrote {repo / EXTERNAL}")
    else:
        print("\n  (--write not given; nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
