"""PART 3 PREREQUISITE - authenticate, then (only then) replay the ORIGINAL
historical Layer-2 linear LODO baseline.

Policy
------
This program is an AUTHENTICATOR first and a replayer second.  It computes the
SHA-256 of every physical input that `z5_lodo.py` actually opens and compares it
against the digest recorded by the historical branch.  If any input is absent or
mismatched it emits PENDING_PHYSICAL_INPUT_AUTHENTICATION and REFUSES to replay.
There is no flag to bypass that refusal: replaying against an absent or
substituted input would produce a number with no provenance chain, which is
worse than no number at all.

It never inspects reader_validation, reader_oracle, foundation development or
sealed holdout, Siletti, pathology or D_shared.  The historical analysis it
authenticates declared NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION,
PROTECTED_DATA_CLOSED and TRAINING_OFF; this program inherits those constraints
and additionally asserts, statically, that the replayed script names no
protected artifact.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Frozen anchors.  Declared here, before anything is measured, so that a later
# edit to widen a tolerance or relax a digest is visible in the diff.
# ---------------------------------------------------------------------------

HISTORICAL_COMMIT = "219831b899b914984369c7a41828bf750554d1d9"
HISTORICAL_BRANCH = "analysis/v5-layer2-cross-view-shortcut-claude-20260915"
ANALYSIS_DIR = "analysis/v5_layer2_cross_view_shortcut_20260915"

# Digests recorded by the historical branch for the code and results themselves,
# in V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT.json at HISTORICAL_COMMIT.
EXPECTED_CODE_AND_RESULT_DIGESTS = {
    "scripts/z5_lodo.py": "8b343279447d4c6d4122c7435bd808939e1a0f8bd11649f0f32e78599707ba7d",
    "results/z_lodo.json": "277eab6e11fefa25d52cdb72522dbd8e29e3cc1602c4f1e3a85b117947f63fdb",
    "results/y_source.json": "cfa899100411582db93a2586cfecb089c5852242c4abbb7203aad486b2a836d7",
}

# The physical inputs `z5_lodo.py` opens, with the digest and the absolute path
# recorded in LARGE_ARTIFACT_REFERENCES.json at HISTORICAL_COMMIT.
DECLARED_INPUTS = {
    "bind_population.npz": {
        "sha256": "4488bcc0226826de332c0ee5c3504dfe6a2c22853de17dce7b366397c56c99be",
        "size_bytes": 5118788,
        "consumed_as": "B['base_index'] (cell selector), B['donor_code'] (donor identity)",
    },
    "screen_out.npz": {
        "sha256": "0fc144a82a6b1bd6d8bcf41c7a2443601203307535fdffd6f882a59343289ffa",
        "size_bytes": 1403900426,
        "consumed_as": "z['p100_v0'] (features), z['p100_v1'] (target)",
    },
    "final_manifest.csv": {
        "sha256": "c409cdf3b5579022936c52e3ba9aee0144a9a3a663588545607684301d517726",
        "size_bytes": 22860892,
        "consumed_as": "fm['source'] (stratum), fm['operator_index'] (centring group)",
    },
    "y_source.json": {
        # read by z5_lodo.py only for its final side-by-side print-out
        "sha256": "cfa899100411582db93a2586cfecb089c5852242c4abbb7203aad486b2a836d7",
        "size_bytes": None,
        "consumed_as": "prev[s]['op_centred_r2'] comparison print",
    },
}

HISTORICAL_SCRATCHPAD = Path(
    r"C:\Users\dushy\AppData\Local\Temp\claude\d--Jepa-project"
    r"\cdf819f6-5db4-4119-9a97-37fef1d27909\scratchpad"
)

# Upstream substrate the frozen screen was cut from.  Not opened by z5_lodo.py,
# but recorded because it determines whether a future rebuild is even possible.
DECLARED_SUBSTRATE = {
    "V0_full.npy": "3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada",
    "V1_full.npy": "c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c",
    "ASSEMBLY_SEEN_V5.npy": "0339d2e79599419f369d78cddf14448019f89476eb674000437b72a1b4fb640e",
}
SUBSTRATE_DIR = Path(r"D:\jepa_v5_substrate_20260914")

# Historical values, restated here so the comparison target is frozen before any
# replayed number exists.  Source: results/z_lodo.json at HISTORICAL_COMMIT.
HISTORICAL_R2 = {
    "SEA_AD": {"n_donors": 36, "pooled_lodo_r2": 0.2410121580995348},
    "HVS": {"n_donors": 41, "pooled_lodo_r2": 0.04508741749145817},
    "NPH52": {"n_donors": 17, "pooled_lodo_r2": 0.05462934735003744},
    "ALL": {"n_donors": 94, "pooled_lodo_r2": 0.0687231474121911},
}

# A replay counts as reproducing only within this tolerance, fixed in advance.
REPLAY_ABS_TOLERANCE = 1e-12

# Names this program must never read, and must never see the replayed script name.
PROTECTED_TOKENS = (
    "reader_validation", "reader_oracle", "sealed", "holdout", "siletti",
    "pathology", "d_shared", "at8", "braak", "cerad", "foundation_dev",
)


def sha256_file(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_show(repo: Path, commit: str, relpath: str) -> bytes:
    return subprocess.run(
        ["git", "show", commit + ":" + relpath],
        cwd=str(repo), check=True, stdout=subprocess.PIPE,
    ).stdout


def git_out(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git"] + list(args), cwd=str(repo), check=True, stdout=subprocess.PIPE
    ).stdout.decode().strip()


def scan_protected(source: str):
    """Static pathology-blindness check on the script about to be replayed."""
    low = source.lower()
    return [t for t in PROTECTED_TOKENS if t in low]


def locate(filename: str, search_roots):
    """Every place `filename` is actually found, so that a same-named file
    sitting in a different directory cannot be silently substituted."""
    found = []
    for root in search_roots:
        root = Path(root)
        direct = root / filename
        if direct.is_file():
            found.append(direct)
    return found


def authenticate_inputs(search_roots):
    report = {}
    for name, spec in DECLARED_INPUTS.items():
        hits = locate(name, search_roots)
        entry = {
            "expected_sha256": spec["sha256"],
            "expected_size_bytes": spec["size_bytes"],
            "consumed_as": spec["consumed_as"],
            "declared_path": str(HISTORICAL_SCRATCHPAD / name),
            "candidates_found": [str(p) for p in hits],
        }
        if not hits:
            entry["status"] = "ABSENT"
            entry["found_sha256"] = None
        else:
            digests = {}
            for p in hits:
                digests[str(p)] = sha256_file(p)
            entry["found_sha256"] = digests
            ok = False
            for d in digests.values():
                if d == spec["sha256"]:
                    ok = True
            entry["status"] = "MATCH" if ok else "DIGEST_MISMATCH"
        report[name] = entry
    return report


def authenticate_substrate():
    out = {}
    for name, expected in DECLARED_SUBSTRATE.items():
        p = SUBSTRATE_DIR / name
        if not p.is_file():
            out[name] = {"status": "ABSENT", "expected_sha256": expected,
                         "found_sha256": None, "path": str(p)}
            continue
        got = sha256_file(p)
        out[name] = {
            "status": "MATCH" if got == expected else "DIGEST_MISMATCH",
            "expected_sha256": expected, "found_sha256": got,
            "path": str(p), "size_bytes": p.stat().st_size,
        }
    return out


def authenticate_code(repo: Path):
    out = {}
    for rel, expected in EXPECTED_CODE_AND_RESULT_DIGESTS.items():
        blob = git_show(repo, HISTORICAL_COMMIT, ANALYSIS_DIR + "/" + rel)
        got = sha256_bytes(blob)
        out[rel] = {
            "status": "MATCH" if got == expected else "DIGEST_MISMATCH",
            "expected_sha256": expected, "found_sha256": got,
            "size_bytes": len(blob),
        }
    return out


def repoint(script_source: str, scratch: Path) -> str:
    """Repoint only the input directory `S`, which the historical README
    explicitly permits ("repoint S to relocate the inputs").  Everything else --
    estimator, population, target, ridge lambda -- is left byte-identical."""
    patched, n = re.subn(
        r"^S = pathlib\.Path\(r'[^']*'\)$",
        "S = pathlib.Path(r'" + str(scratch) + "')",
        script_source, count=1, flags=re.M,
    )
    if n != 1:
        raise RuntimeError("refusing to replay: could not repoint S exactly once")
    return patched


def replay(scratch: Path, script_source: str):
    """Execute the ORIGINAL script verbatim apart from the input directory."""
    patched = repoint(script_source, scratch)
    ns = {"__name__": "__replay__"}
    exec(compile(patched, "z5_lodo.py<repointed>", "exec"), ns)
    return json.loads((scratch / "z_lodo.json").read_text())


def build_receipt(repo: Path, search_roots, skip_substrate_hash=False):
    live_head = git_out(
        repo, "ls-remote", "origin", "refs/heads/" + HISTORICAL_BRANCH
    ).split()[0]

    script_source = git_show(
        repo, HISTORICAL_COMMIT, ANALYSIS_DIR + "/scripts/z5_lodo.py"
    ).decode()
    protected_hits = scan_protected(script_source)

    code = authenticate_code(repo)
    inputs = authenticate_inputs(search_roots)
    substrate = {} if skip_substrate_hash else authenticate_substrate()

    all_inputs_ok = all(v["status"] == "MATCH" for v in inputs.values())
    code_ok = all(v["status"] == "MATCH" for v in code.values())
    head_ok = live_head == HISTORICAL_COMMIT

    verdict = ("AUTHENTICATED"
               if (all_inputs_ok and code_ok and head_ok and not protected_hits)
               else "PENDING_PHYSICAL_INPUT_AUTHENTICATION")

    receipt = {
        "receipt_id": "PART3_LAYER2_LINEAR_LODO_BASELINE_AUTHENTICATION_V1",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "verdict": verdict,
        "historical_branch": HISTORICAL_BRANCH,
        "historical_commit_recorded": HISTORICAL_COMMIT,
        "historical_commit_live_head": live_head,
        "live_head_matches_recorded": head_ok,
        "pathology_blindness": {
            "protected_tokens_found_in_replayed_script": protected_hits,
            "status": "CLEAN" if not protected_hits else "PROTECTED_ACCESS_DETECTED",
            "historical_declared_constraints": [
                "NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION",
                "TRAINING_OFF", "PROTECTED_DATA_CLOSED",
            ],
        },
        "code_and_result_authentication": code,
        "physical_input_authentication": inputs,
        "upstream_substrate_authentication": substrate,
        "search_roots": [str(r) for r in search_roots],
        "replay": None,
        "historical_values": HISTORICAL_R2,
        "replay_abs_tolerance": REPLAY_ABS_TOLERANCE,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "executor_repo": str(repo),
            "executor_head": git_out(repo, "rev-parse", "HEAD"),
            "executor_status_clean": git_out(repo, "status", "--porcelain") == "",
        },
    }
    try:
        import numpy
        import pandas
        receipt["environment"]["numpy"] = numpy.__version__
        receipt["environment"]["pandas"] = pandas.__version__
    except Exception as exc:  # pragma: no cover
        receipt["environment"]["numpy_pandas"] = "UNAVAILABLE: " + str(exc)

    if verdict != "AUTHENTICATED":
        receipt["replay"] = {
            "executed": False,
            "reason": ("REFUSED: physical inputs not authenticated. Replaying "
                       "against absent or substituted inputs would yield a "
                       "number with no provenance chain."),
            "replayed_r2": "UNMEASURED",
            "deltas_vs_historical": "UNMEASURED",
        }
    else:
        scratch = Path(search_roots[0])
        res = replay(scratch, script_source)
        deltas = {}
        for s, hist in HISTORICAL_R2.items():
            got = res[s]["pooled_lodo_r2"]
            deltas[s] = {
                "historical": hist["pooled_lodo_r2"],
                "replayed": got,
                "abs_delta": abs(got - hist["pooled_lodo_r2"]),
                "n_donors_historical": hist["n_donors"],
                "n_donors_replayed": res[s]["n_donors"],
                "donor_count_match": res[s]["n_donors"] == hist["n_donors"],
                "within_tolerance": abs(got - hist["pooled_lodo_r2"]) <= REPLAY_ABS_TOLERANCE,
            }
        receipt["replay"] = {
            "executed": True,
            "replayed_r2": {s: res[s]["pooled_lodo_r2"] for s in HISTORICAL_R2},
            "deltas_vs_historical": deltas,
            "reproduced": all(d["within_tolerance"] and d["donor_count_match"]
                              for d in deltas.values()),
            "full_result": res,
        }
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".",
                    help="git repo containing the historical commit")
    ap.add_argument("--out", required=True, help="path for the JSON receipt")
    ap.add_argument("--search-root", action="append", default=[],
                    help="extra directory to search for the declared inputs")
    ap.add_argument("--skip-substrate-hash", action="store_true",
                    help="skip hashing the 9.3 GB substrate files")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    roots = [HISTORICAL_SCRATCHPAD] + [Path(r) for r in args.search_root]
    receipt = build_receipt(repo, roots, args.skip_substrate_hash)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    print("VERDICT:", receipt["verdict"])
    print("live head matches recorded:", receipt["live_head_matches_recorded"])
    print("pathology-blindness:", receipt["pathology_blindness"]["status"])
    for rel, e in receipt["code_and_result_authentication"].items():
        print("  code      %-24s %s" % (rel, e["status"]))
    for name, e in receipt["physical_input_authentication"].items():
        print("  input     %-24s %s" % (name, e["status"]))
    for name, e in receipt["upstream_substrate_authentication"].items():
        print("  substrate %-24s %s" % (name, e["status"]))
    print("replay executed:", receipt["replay"]["executed"])
    print("receipt ->", out)
    return 0 if receipt["verdict"] == "AUTHENTICATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
