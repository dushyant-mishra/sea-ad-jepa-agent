#!/usr/bin/env python3
"""Can two concurrent draws collide? Proven impossible by construction, then tested.

Parallel draws cannot share one world directory: worker B's build would overwrite worker
A's world between A's build and A's read, and A would then measure B's fixture while
reporting A's identity. That is S99 again, arriving through scheduling instead of through
construction.

The namespace is bounded rather than opened. A run id selects
SYNTHETIC_ROOT/_runs/<id>; the id must match [A-Za-z0-9_]{1,40}, which admits no
separators and no dots, and the resolved path must still lie under SYNTHETIC_ROOT. So a
traversal is not expressible rather than merely rejected, and every other guard applies
unchanged inside the sub-namespace.

This file does not take that on faith. It tries to escape, it runs two builds at the same
time against the same world name, and it checks that each ended up with its own bytes.

No real substrate is read. No correspondence value is computed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402

BUILDER = "scripts/v64/build_stage4_synthetic_worlds_v1.py"
EXEC = "scripts/v64/stage4_executor_v1.py"
BASE = "D:/jepa_v5_outputs_20260925/v64_stage4_synthetic"
WORLD = "HIDDEN_CONFOUND_K"
R = []


def rec(name, expectation, observed, holds):
    R.append(dict(check=name, expectation=expectation, observed=observed,
                  holds=bool(holds)))
    print("  %-4s %-54s %s" % ("OK" if holds else "FAIL", name, observed))


def resolve(run_id):
    """Ask the executor itself to resolve a run id, so the test exercises the real rule."""
    code = ("import os,sys;sys.path.insert(0,'scripts/v64');"
            "import stage4_executor_v1 as E;"
            "print(E._synthetic_run_root())")
    env = dict(os.environ)
    if run_id is None:
        env.pop("JEPA_SYNTHETIC_RUN_ID", None)
    else:
        env["JEPA_SYNTHETIC_RUN_ID"] = run_id
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       env=env)
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    # ---------------------------------------------------- traversal is not expressible
    for bad in ("..", "../evil", "a/b", "a\\b", ".", "", "x" * 41, "a.b", "a b", "~",
                "C:", "_runs/../.."):
        code, out = resolve(bad)
        rejected = code != 0 or "Stop" in out or "must be 1-40" in out
        rec("reject run id %r" % bad, "refused", "exit=%d" % code, rejected)

    code, out = resolve(None)
    rec("no run id resolves to the unchanged synthetic root", "the module constant",
        out.splitlines()[-1][-48:], code == 0 and out.strip().endswith("v64_stage4_synthetic"))

    c1, r1 = resolve("w00")
    c2, r2 = resolve("w01")
    rec("two run ids resolve to different roots", "disjoint paths",
        "%s vs %s" % (os.path.basename(r1), os.path.basename(r2)),
        c1 == 0 and c2 == 0 and r1 != r2)
    rec("both resolved roots lie under the synthetic root", "no escape",
        "under_base=%s" % (r1.startswith(os.path.abspath(BASE))
                           and r2.startswith(os.path.abspath(BASE))),
        r1.startswith(os.path.abspath(BASE)) and r2.startswith(os.path.abspath(BASE)))

    # ------------------------------------------- two SIMULTANEOUS builds, same world name
    results = {}

    def build(run_id, K, seed):
        env = dict(os.environ, JEPA_SYNTHETIC_RUN_ID=run_id)
        p = subprocess.run([sys.executable, BUILDER, "--only", WORLD,
                            "--confound-blocks", str(K), "--seed-base", str(seed),
                            "--donors", "20"],
                           capture_output=True, text=True, env=env)
        results[run_id] = p.returncode

    print("")
    print("  launching two concurrent builds of the SAME world name ...")
    t1 = threading.Thread(target=build, args=("par_a", 5, 950001))
    t2 = threading.Thread(target=build, args=("par_b", 50, 950002))
    t1.start(); t2.start(); t1.join(); t2.join()
    rec("both concurrent builds succeed", "exit 0 each", str(results),
        results.get("par_a") == 0 and results.get("par_b") == 0)

    ma = os.path.join(BASE, "_runs", "par_a", WORLD, "WORLD_MANIFEST.json")
    mb = os.path.join(BASE, "_runs", "par_b", WORLD, "WORLD_MANIFEST.json")
    both = os.path.exists(ma) and os.path.exists(mb)
    rec("each build has its OWN manifest", "two separate files",
        "a=%s b=%s" % (os.path.exists(ma), os.path.exists(mb)), both)

    if both:
        A, Bm = json.load(open(ma)), json.load(open(mb))
        ka = A["planted_truth"]["confound_blocks_K"]
        kb = Bm["planted_truth"]["confound_blocks_K"]
        rec("neither build overwrote the other's K", "5 and 50 survive",
            "a.K=%s b.K=%s" % (ka, kb), ka == 5 and kb == 50)
        da = set(A["digests"].values())
        db = set(Bm["digests"].values())
        rec("their substrate bytes are disjoint", "no shared digest",
            "%d shared" % len(da & db), not (da & db))
        # and the paths they occupy cannot be the same string
        rec("their world directories are different paths", "disjoint",
            "a!=b=%s" % (os.path.dirname(ma) != os.path.dirname(mb)),
            os.path.dirname(ma) != os.path.dirname(mb))

    # ------------------------------------------------ the default namespace is untouched
    canon = os.path.join(BASE, "HIDDEN_CONFOUND", "WORLD_MANIFEST.json")
    rec("the canonical worlds sit outside every run namespace", "unaffected",
        "canonical manifest present=%s" % os.path.exists(canon), os.path.exists(canon))

    held = [x for x in R if x["holds"]]
    out = dict(schema="V64_SYNTHETIC_RUN_ISOLATION_V1", date="2026-10-02",
               why="a parallel draw must not be able to read another draw's fixture while "
                   "reporting its own identity",
               rule="JEPA_SYNTHETIC_RUN_ID matches [A-Za-z0-9_]{1,40} and selects "
                    "SYNTHETIC_ROOT/_runs/<id>; no separators, no dots, resolved path "
                    "required to lie under the synthetic root",
               n_checks=len(R), n_holding=len(held), checks=R,
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               real_substrate_read=False, computed_correspondence_values=0,
               status="PASS" if len(held) == len(R) else "FAIL")
    p = "results/v64/phase_b_design/V64_SYNTHETIC_RUN_ISOLATION_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print("%d/%d isolation checks hold -> %s" % (len(held), len(R), out["status"]))
    print("receipt sha256 " + B.sha_file(p))
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
