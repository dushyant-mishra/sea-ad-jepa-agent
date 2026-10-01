#!/usr/bin/env python3
"""Are the four worlds' conclusions a property of the method, or of one random draw?

S95, raised by my own self-audit. The end-to-end qualification reported four verdicts --
biology recovered, null stayed null, the depth effect was mostly removed, the hidden
confound won -- from ONE fixture per world. I raised exactly this weakness against the
other lane's evidence/measurement synthetic (single seed, SEED=6703), so leaving my own
conclusions resting on a single draw would be holding their work to a standard I had not
met. Two of those verdicts are now interpretation limits that will be quoted; they need to
survive resampling before they are worth quoting.

WHAT THIS DOES. Rebuilds all four worlds at several seed bases, runs each through the real
executor entrypoint, and asks whether the QUALITATIVE verdict is stable, not whether the
numbers repeat. The numbers will move; the question is whether the sign, the ordering and
the null-exclusion decision move with them.

WHAT IT RESTORES. The canonical worlds are the ones at CANONICAL_SEED_BASE and every
committed manifest is built from that base, so this harness rebuilds them at the end and
verifies by digest that the canonical state is back. A robustness check that left the
qualification artifacts pointing at a different draw would corrupt the thing it was
defending.

No real substrate is read. No correspondence value is computed on real data.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import build_stage4_synthetic_worlds_v1 as BW                        # noqa: E402

EXEC = "scripts/v64/stage4_executor_v1.py"
ROOT = BW.ROOT
OUT = os.path.join(ROOT, "_results")
WORLDS = BW.WORLDS
PRIMARY = "GENE_BALANCED"
EXTRA_SEED_BASES = (770101, 880303, 990505)


def build(seed_base):
    r = subprocess.run([sys.executable, "scripts/v64/build_stage4_synthetic_worlds_v1.py",
                        "--seed-base", str(seed_base)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("world build failed at seed base %d:\n%s"
                         % (seed_base, r.stdout + r.stderr))


def run(world):
    r = subprocess.run([sys.executable, EXEC, "--synthetic-world", world],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("world %s failed:\n%s" % (world, r.stdout + r.stderr))
    R = json.load(open(os.path.join(OUT, "V64_STAGE4_RESULT_%s.json" % world)))
    a = R["ADJUSTED"][PRIMARY]
    return dict(delta=a["delta"], lcb95=a["lcb95"],
                raw=R["RAW_UNADJUSTED_GENE_BALANCED"]["delta"],
                cvc=R["CONTROL_A_VS_CONTROL_B"]["delta"])


def main() -> int:
    bases = (BW.CANONICAL_SEED_BASE,) + EXTRA_SEED_BASES
    draws = {}
    for sb in bases:
        print("seed base %d ..." % sb, flush=True)
        build(sb)
        draws[sb] = {w: run(w) for w in WORLDS}
        for w in WORLDS:
            d = draws[sb][w]
            print("    %-20s delta=%+.4f lcb95=%+.4f raw=%+.4f cvc=%+.4f"
                  % (w, d["delta"], d["lcb95"], d["raw"], d["cvc"]))

    # ------------------------------------------------- is each verdict seed-stable?
    def across(w, key):
        return np.array([draws[sb][w][key] for sb in bases], float)

    checks = []

    def verdict(name, holds_per_value, statement, detail, unit="draws"):
        # The denominator is the number of VALUES tested, not the number of seed bases.
        # Getting that wrong printed "15/4" for the control-versus-control check, which
        # pools four worlds per draw -- S96 in my self-audit lane.
        holds_per_value = np.asarray(holds_per_value, bool)
        n, tot = int(holds_per_value.sum()), int(holds_per_value.size)
        checks.append(dict(check=name, statement=statement, unit=unit,
                           values_tested=tot, values_holding=n,
                           seed_stable=bool(n == tot), detail=detail))
        print("  %-52s %2d/%-2d %-6s %s"
              % (name, n, tot, unit, "STABLE" if n == tot else "SEED-DEPENDENT"))

    bio_d, bio_l = across("BIOLOGY_POSITIVE", "delta"), across("BIOLOGY_POSITIVE", "lcb95")
    verdict("planted biology is recovered in every draw", (bio_d > 0) & (bio_l > 0),
            "delta > 0 and LCB95 > 0",
            dict(delta_range=[bio_d.min(), bio_d.max()],
                 lcb_range=[bio_l.min(), bio_l.max()]))

    nul_l = across("TRUE_NULL", "lcb95")
    verdict("the true null never claims an effect", nul_l <= 0, "LCB95 <= 0",
            dict(lcb_range=[nul_l.min(), nul_l.max()],
                 delta_range=[across("TRUE_NULL", "delta").min(),
                              across("TRUE_NULL", "delta").max()]))

    tech_d, tech_r = across("MEASURED_TECHNICAL", "delta"), across("MEASURED_TECHNICAL", "raw")
    removed = 1.0 - np.abs(tech_d) / np.abs(tech_r)
    verdict("the adjustment removes most of a pure depth effect", removed > 0.5,
            "more than half the raw depth effect is removed",
            dict(fraction_removed=[float(x) for x in removed]))

    tech_l = across("MEASURED_TECHNICAL", "lcb95")
    residue = tech_l > 0
    verdict("LIMIT: the depth residue still excludes zero", residue,
            "a purely technical world ends with LCB95 > 0 -- the limit I reported",
            dict(lcb_per_draw=[float(x) for x in tech_l],
                 draws_where_residue_is_significant=int(residue.sum()),
                 reading="where this does NOT hold in a draw, the limit is weaker than "
                         "stated and the receipt must say so"))

    hid_d, hid_l = across("HIDDEN_CONFOUND", "delta"), across("HIDDEN_CONFOUND", "lcb95")
    frac = hid_d / bio_d
    verdict("LIMIT: the hidden confound fools the method", (hid_l > 0) & (frac > 0.4),
            "LCB95 > 0 and the confound reaches more than 40% of genuine biology",
            dict(fraction_of_biology=[float(x) for x in frac],
                 lcb_per_draw=[float(x) for x in hid_l]))

    cvc = np.concatenate([across(w, "cvc") for w in WORLDS])
    verdict("control-versus-control stays near zero everywhere",
            np.abs(cvc) < 0.1 * bio_d.min(),
            "the anti-false-green arm does not drift across draws",
            dict(max_absolute=float(np.abs(cvc).max()),
                 compared_against=float(0.1 * bio_d.min()),
                 note="four worlds per draw, so this tests %d values" % cvc.size),
            unit="world-draws")

    # ------------------------------------------- restore the canonical worlds
    print("")
    print("restoring the canonical worlds at seed base %d ..." % BW.CANONICAL_SEED_BASE)
    build(BW.CANONICAL_SEED_BASE)
    restored = {}
    for w in WORLDS:
        m = json.load(open(os.path.join(ROOT, w, "WORLD_MANIFEST.json")))
        ok = all(B.sha_file(os.path.join(ROOT, w, f)) == d
                 for f, d in m["digests"].items())
        restored[w] = dict(seed=m["seed"], digests_match_manifest=ok,
                           is_canonical=m["seed"] - WORLDS.index(w)
                           == BW.CANONICAL_SEED_BASE)
    canonical_ok = all(v["digests_match_manifest"] and v["is_canonical"]
                       for v in restored.values())
    print("  canonical state restored and digest-verified: %s" % canonical_ok)

    unstable = [c for c in checks if not c["seed_stable"]]
    out = dict(
        schema="V64_STAGE4_WORLD_SEED_ROBUSTNESS_V1", date="2026-10-01",
        raises="S95, from my own self-audit lane",
        why="the four end-to-end verdicts, two of which are interpretation limits that "
            "will be quoted, each rested on a single fixture. I raised the same "
            "single-seed weakness against the other lane, so my own conclusions had to "
            "meet it.",
        seed_bases=list(bases), draws_per_world=len(bases),
        per_draw={str(sb): draws[sb] for sb in bases},
        checks=checks,
        n_checks=len(checks), n_seed_stable=len(checks) - len(unstable),
        thresholds_were_frozen_before_the_draws=True,
        thresholds_unchanged_after_seeing_the_failures=True,
        seed_dependent=[c["check"] for c in unstable],
        canonical_worlds_restored=restored,
        canonical_state_verified=canonical_ok,
        real_substrate_read=False, computed_correspondence_values=0,
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        status="PASS" if not unstable and canonical_ok else "FAIL")
    p = "results/v64/phase_b_design/V64_STAGE4_WORLD_SEED_ROBUSTNESS_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print("%d/%d conclusions are seed-stable across %d draws -> %s"
          % (len(checks) - len(unstable), len(checks), len(bases), out["status"]))
    print("receipt sha256 " + B.sha_file(p))
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
