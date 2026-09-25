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

# Producer scripts named in results/aud_hashes.json at HISTORICAL_COMMIT for the
# frozen Layer-1 artifacts.  Listed so that whether they still exist is MEASURED
# rather than asserted: if they are gone, the frozen screen cannot be rebuilt
# even though the upstream substrate survives.
DECLARED_PRODUCERS = {
    "screen.py": {
        "sha256": "d0fe0ab135585586b27c2c23af0cacc0ea3380ccf3eb270a3c640f4c41976fd6",
        "produces": "screen_out.npz",
    },
    "rebuild.py": {
        "sha256": "abe8ecff642af47e07e9657835a88d4ca0c90a0fe97de111f353ea4cf7e8297b",
        "produces": "final_manifest.csv (frozen sample manifest)",
    },
}

# What the replayed number actually IS.  Recorded in the receipt so a later
# comparison cannot be made against an incompatible baseline by accident.
BASELINE_DEFINITION = {
    "model_class": (
        "Ridge linear map, closed-form, lambda = 1e-2 * n_train, refit "
        "completely for every held-out donor. NOT a trained JEPA."
    ),
    "representation": (
        "256-dimensional VALUE_ONLY channels of the V5 disjoint-view substrate. "
        "The substrate is (4553407, 512) float32 per view = 256 value + 256 "
        "visibility channels; only the 256 value channels are used."
    ),
    "features_X": "p100_v0 - view-0 VALUE_ONLY vector of a cell, at full depth p=1.00",
    "target_Y": (
        "p100_v1 - view-1 VALUE_ONLY vector of the SAME CELL, at full depth, "
        "operator-mean-centred. The target is the other molecular view of the "
        "same cell. It is NOT pathology, NOT a donor-level outcome, and NOT a "
        "reader_fit target."
    ),
    "metric": (
        "Pooled total-variance-explained R2 = 1 - sum||y-yhat||^2 / "
        "sum||y-ybar||^2, summed over all 256 output dimensions and all "
        "held-out CELLS of the held-out donor."
    ),
    "unit_of_evaluation": "CELL (many cells per held-out donor), not donor",
    "held_out_split": (
        "Leave-one-donor-out. For each donor, every cell of that donor is "
        "removed from training and the entire pipeline - operator means, "
        "standardisation and the ridge solution - is refit from scratch."
    ),
    "population": (
        "SELECTED 94-donor BASE_MECHANICS stratum: 196,817 cells, 42 operators. "
        "SEA_AD 36 donors / 67,584 cells; HVS 41 donors / 88,015 cells; "
        "NPH52 17 donors / 41,218 cells. 36+41+17 = 94, NOT 104."
    ),
    "population_is_a_probability_sample": (
        "Cells enter by an operator-stratified whole-block hash-rank sample with "
        "unequal inclusion probability q_i = min(12,B_o)/B_o (q_min 0.008386, "
        "q_median 0.406897, q_max 1.0). z5_lodo.py applies NO weights, so these "
        "R2 values are UNWEIGHTED SAMPLE quantities, not FULL104 population "
        "quantities. The historical audits index records that the molecular "
        "increment over context moved from +0.0311 unweighted to +0.1207 under "
        "empirical FULL104 weighting, so the unweighted/weighted distinction is "
        "known to be material on this substrate."
    ),
    "donor_identity_rule": (
        "z5_lodo.py takes donor identity from B['donor_code'] in "
        "bind_population.npz and applies pd.factorize to it within each source "
        "stratum. Because bind_population.npz is ABSENT, it could NOT be "
        "verified in this run that donor_code is a 1:1 encoding of the donor ID "
        "STRING rather than a storage position. This is UNVERIFIED, not assumed "
        "correct, and must be checked against the physical source before the "
        "baseline is used."
    ),
    "cell_identity_rule": (
        "Cells are selected by B['base_index'] into the frozen screen arrays. "
        "Whether that index resolves cells by selection_row rather than block "
        "order could NOT be verified in this run, because the artifact is absent."
    ),
    "stress_strata": "excluded from the LODO population",
}

# What a later comparison against a trained JEPA would have to satisfy.
VALID_COMPARISON_REQUIREMENTS = {
    "population": (
        "The SAME 94 donors and the SAME 196,817 BASE_MECHANICS cells, keyed by "
        "donor ID string and by selection_row. A trained JEPA evaluated on all "
        "104 donors is a DIFFERENT population and is not comparable to this "
        "number. If the JEPA population differs, the baseline must be recomputed "
        "on the JEPA's population, not the number quoted across."
    ),
    "target": (
        "The SAME estimand: predict the 256-dim VALUE_ONLY view-1 vector of the "
        "same cell from view-0, operator-mean-centred, pooled total-variance R2 "
        "over cells. A JEPA scored on a donor-level pathology outcome, on a "
        "reader_fit target, or on a different embedding dimensionality is "
        "measuring a different quantity and the two numbers must not be placed "
        "in the same column."
    ),
    "held_out_split": (
        "Leave-one-donor-out with COMPLETE refit per held-out donor, including "
        "the operator means and the standardisation. A JEPA evaluated under a "
        "5-fold donor split, or one whose normalisation statistics were fit on "
        "all donors, is not comparable. Any JEPA whose pretraining saw cells "
        "from the held-out donor voids the comparison entirely."
    ),
    "weighting": (
        "Both sides must use the same weighting. These values are unweighted on "
        "a probability sample with unequal inclusion probabilities; a "
        "population-weighted JEPA number is not comparable to them."
    ),
    "reporting": (
        "Report per source. Pooling across sources inflates R2 through "
        "between-source mean structure: pooled ALL is 0.0687 while SEA_AD alone "
        "is 0.2410. A single pooled headline number would misrepresent both."
    ),
    "direction_of_evidence": (
        "The historical closeout records SEA_AD as demonstrating donor-"
        "generalisable linear cross-view signal at this model class, and HVS and "
        "NPH52 as NOT demonstrating it. Non-demonstration is not absence. A JEPA "
        "beating 0.045 on HVS is not thereby shown to be finding biology."
    ),
}

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


def assess_recovery(repo: Path, search_roots):
    """Measure whether the absent inputs could be REBUILT.

    The substrate surviving is not sufficient: the frozen screen can only be
    regenerated if the code that produced it also survives.  This checks for the
    producer scripts in git history and on disk, and checks whether any committed
    script actually WRITES bind_population.npz, whose regenerability
    LARGE_ARTIFACT_REFERENCES.json asserts.
    """
    producers = {}
    for name, spec in DECLARED_PRODUCERS.items():
        in_git = subprocess.run(
            ["git", "log", "--all", "--format=%H", "--", "*" + name],
            cwd=str(repo), stdout=subprocess.PIPE,
        ).stdout.decode().split()
        on_disk = []
        for root in search_roots:
            p = Path(root) / name
            if p.is_file():
                on_disk.append(str(p))
        producers[name] = {
            "produces": spec["produces"],
            "sha256_recorded_in_aud_hashes": spec["sha256"],
            "commits_touching_this_filename": in_git,
            "found_on_disk": on_disk,
            "status": "PRESENT" if (in_git or on_disk) else "NOT_IN_GIT_AND_NOT_ON_DISK",
        }

    # Does any committed file in the historical analysis dir WRITE bind_population?
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", HISTORICAL_COMMIT, "--", ANALYSIS_DIR],
        cwd=str(repo), check=True, stdout=subprocess.PIPE,
    ).stdout.decode().split()
    reads, writes = [], []
    for rel in listing:
        if not rel.endswith(".py"):
            continue
        body = git_show(repo, HISTORICAL_COMMIT, rel).decode("utf-8", "replace")
        if "bind_population" not in body:
            continue
        for line in body.splitlines():
            if "bind_population" not in line:
                continue
            if "savez" in line or "open(" in line and "'w'" in line:
                writes.append(rel + ": " + line.strip())
            else:
                reads.append(rel + ": " + line.strip())

    return {
        "producer_scripts": producers,
        "bind_population_write_sites_in_committed_code": writes,
        "bind_population_read_sites_in_committed_code": reads,
        "regenerability_claim_in_manifest": (
            "bind_population.npz is described as 'deterministically regenerable "
            "from final_manifest.csv'"
        ),
        "regenerability_claim_status": (
            "DISCHARGED" if writes else "UNDISCHARGED_NO_COMMITTED_PRODUCER"
        ),
        "conclusion": None,  # filled by build_receipt once substrate state is known
    }


def repoint(script_source: str, scratch: Path) -> str:
    """Repoint only the input directory `S`, which the historical README
    explicitly permits ("repoint S to relocate the inputs").  Everything else --
    estimator, population, target, ridge lambda -- is left byte-identical."""
    replacement = "S = pathlib.Path(r'" + str(scratch) + "')"
    # A function replacement, not a string: a Windows path such as
    # C:\Users\... would otherwise be interpreted as regex escapes ("\U",
    # "\s") and either raise or silently mangle the input directory.
    patched, n = re.subn(
        r"^S = pathlib\.Path\(r'[^']*'\)$",
        lambda _m: replacement,
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
    recovery = assess_recovery(repo, list(search_roots) + [SUBSTRATE_DIR])

    substrate_ok = bool(substrate) and all(
        v["status"] == "MATCH" for v in substrate.values())
    producers_gone = all(
        v["status"] == "NOT_IN_GIT_AND_NOT_ON_DISK"
        for v in recovery["producer_scripts"].values())
    if substrate_ok and producers_gone:
        recovery["conclusion"] = (
            "NOT_REBUILDABLE_FROM_WHAT_SURVIVES: the upstream V0/V1 substrate "
            "authenticates, but the scripts that cut the frozen screen from it "
            "(screen.py, rebuild.py) are in neither git history nor on disk, and "
            "no committed code writes bind_population.npz. Recovering this "
            "baseline requires locating the original artifacts themselves, not "
            "re-deriving them."
        )
    elif not substrate_ok:
        recovery["conclusion"] = (
            "SUBSTRATE_NOT_AUTHENTICATED: rebuild feasibility cannot be assessed "
            "because the upstream substrate did not verify or was not hashed."
        )
    else:
        recovery["conclusion"] = (
            "PARTIAL: some producer code survives; rebuild feasibility needs "
            "case-by-case review against the entries above."
        )

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
        "recovery_feasibility": recovery,
        "baseline_definition": BASELINE_DEFINITION,
        "valid_future_comparison_requirements": VALID_COMPARISON_REQUIREMENTS,
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
    for name, e in receipt["recovery_feasibility"]["producer_scripts"].items():
        print("  producer  %-24s %s" % (name, e["status"]))
    print("  regenerability claim:",
          receipt["recovery_feasibility"]["regenerability_claim_status"])
    print("replay executed:", receipt["replay"]["executed"])
    print("receipt ->", out)
    return 0 if receipt["verdict"] == "AUTHENTICATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
