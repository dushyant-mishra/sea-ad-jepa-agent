# SCENIC+ lane handed back — verified, not taken on trust

**Good news with a real gap: the slow irreversible work is done; no network was built.**

## What I verified myself

- Branch `claude/v69-scenicplus-external-network-20261001` @ **`c56132f4`**, worktree clean, 24 commits ✓
- The 63.6 GB fragment file is on disk at **exactly 63,641,120,882 bytes** ✓
- All 17 self-audit headings **S0–S16** are genuinely in the file ✓ (this matters — see below)
- Route-B QC process **PID 5616 is still alive**, started 14:30

I'm re-hashing the 63.6 GB file independently right now rather than accepting the reported digest; size matches, digest verification pending.

## The thing to act on

**The Route-B fragment QC did not finish.** `V69_ROUTEB_FRAGMENT_QC_V1.json` is absent and `routeB/` is empty. The lane's own rule is right: *if the receipt is absent it did not finish — re-run rather than assume partial output.* The process is still running, so this may resolve on its own, but nothing downstream may treat Route-B QC as done.

## What's genuinely finished

Complete GSE214979 substrate authenticated against **server-declared Content-Length before** any digest — so a truncated download can't become an authenticated artifact. Motif collection v10 (10,249 motifs), hg38 analysis set, cbust, all pinned.

Cohort frozen pathology-blind, and **blindness demonstrated rather than promised**: flipping every `Status`/`Braak`/`Diagnosis`/`APOE_Status` value leaves both population digests bit-identical. ALL_MICROGLIA 3,179 nuclei/15 donors; development set 2,534/12.

Two findings I'd flag as unusually good:

- **The Stage-4 genome build was resolved empirically.** The design contract's "hg19-primary" wording and hg19-bearing pair keys invite the wrong answer; **57/57** enumerated-control pair keys match the **hg38** columns, 0/57 hg19. No liftOver needed. That's exactly the kind of coordinate assumption that has burned this project.
- **Control C1 has real teeth now.** 27,072 motifs, 1,605 TFs, direct motif supply ranging 0–144 with **median 6**, and **110 TFs with zero direct motifs** — against the prior Stage75F fact that 7 of 10 TFs reached "support" with zero direct motifs. Direct/orthology/similarity/extended counted separately.

## The cost finding that changes planning

Custom cisTarget database: **33.7–41.2 h per route, 67–83 h for both**, measured from two runs over 150,561 regions. Reported as a range with no model fitted, because a two-point fit gave a negative intercept. The lane surfaced the decision rather than taking it — and was right not to: shrinking the motif collection would directly weaken C1, and reverting a route to a generic database would defeat the only question Route B exists to answer.

## S0 — the self-audit finding worth your attention

Nine entries (S7–S15) were asserted in commit messages but **never written to the file**. `Path.read_text()` without an encoding decodes cp1252 on Windows, so UTF-8 em-dash anchors matched nothing; the replace was a silent no-op, the write succeeded, the snippets printed `ok`, the commits went through. **Six commits describe findings absent from their own diffs.**

Nothing was lost — the findings survive verbatim in the commit messages — but a commit message is a provenance record, and it asserted a file contained something it did not. It was found by grepping headings, not by any of the snippets that claimed success. That's the same disease as my own S86/S87 today: a check that couldn't fail.

Also: **S6** — its crosswalk counted only each peak's *first* overlapping Stage-4 interval, understating coverage from 13,325 to **22,991 (41.4% → 71.5%)**. Caught by re-reading its own receipt.

## Not done

No eRegulons on either route. No cisTarget database. Route-B consensus peaks, controls C2–C7, donor stability, Route-A/B comparison, frozen network receipt, program-level crosswalks, source adapters — none started.

Reported end state is short of the mandate's target, and the lane says so plainly: *"Reported as reached, not as achieved."* I'd rather have that than a claimed completion.

One caution I'd keep: its diagnosis that Stage75F's blocker was *absence of same-nucleus pairing* is a third account, after its own first misdiagnosis and my trace pointing at region-set size and annotation supply. It records that in S9. I wouldn't treat any single-sentence account of that failure as settled.

**Bash&#xA0;**&#x52;ead the independent digest verification

IN

```
cat "C:\Users\dushy\AppData\Local\Temp\claude\d--Jepa-project\cdf819f6-5db4-4119-9a97-37fef1d27909\tasks\b2pixhqrz.output"
```

OUT

```
bytes 63641120882
sha256 b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f
expected b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f
MATCH True
seconds 454.0

[exited with code 0]
```

Independent re-hash confirms the fragment file: **63,641,120,882 bytes**, SHA-256 `b7c5aa2d…1e8f`, exact match, 454 s. That asset is genuine and complete.

**Bash&#xA0;**&#x43;heck Route-B QC progress and process

IN

```
find "D:/jepa_v5_outputs_20260925/v69_scenicplus/routeB" -type f 2>/dev/null | head -5; echo "--- routeB file count: $(find "D:/jepa_v5_outputs_20260925/v69_scenicplus/routeB" -type f 2>/dev/null | wc -l) ---"; powershell -NoProfile -Command "if (Get-Process -Id 5616 -ErrorAction SilentlyContinue) {'PID 5616 ALIVE'} else {'PID 5616 GONE'}" 2>&1 | tail -1
```

OUT

```
--- routeB file count: 0 ---
PID 5616 ALIVE
```

Route-B QC still running, no output yet — correct behaviour, its receipt writes only on completion.

Back to Stage 4. The question has changed, so the measurement needs a fresh pre-commitment before anything runs.

**Write** D:\jepa_wt_v64_sampler_20260930\results\v64\phase_b_design\V64_STAGE4_CALIBRATION_PRECOMMIT_V2.json

65 lines

```
{
  "schema": "V64_STAGE4_CALIBRATION_PRECOMMIT_V2",
  "date": "2026-10-01",
  "written_before_any_draw_of_this_design_was_made": true,
  "supersedes": {
    "path": "results/v64/phase_b_design/V64_STAGE4_CALIBRATION_PRECOMMIT_V1.json",
    "sha256": "b23dcc2d2902f8d80c0aac6e7527e7c684677d0f4c30c3a365fd58dac915e2c2",
    "why_superseded": "V1 was executed faithfully and its stopping rule was honoured, but it ran against a synthetic fixture whose control arm was drawn uniformly at random instead of being built under the frozen PROMOTER_FIXED_DISTAL_MATCHED_CONTROL construction. Its measured rates -- a technical false-positive rate of 0.875 at 60 donors and 1.000 at 282 -- are therefore statements about that fixture and NOT about the frozen Stage-4 design. They are retained, not deleted, and must be cited only with that qualification.",
    "what_changed_in_the_fixture": "controls are now built at the same promoter, distance matched to the linked edge within 10 percent or 10 kb whichever is larger, on a 5,000 bp grid, non-overlapping with the linked interval, with the accessibility qualification symmetric across arms, and edges with no admissible control are trimmed and counted. The matching is audited in every world build and the build fails closed on any violation."
  },
  "why_this_measurement_is_now_different": "Under the repaired fixture a single run of each world showed the measured-technical confound producing no effect at all (adjusted Delta -0.0041, bound below zero) while the hidden confound passed all five frozen gates at Delta +0.5937 against genuine biology's +0.5543. The old question, how often a technical artifact is reported as a finding, appears answered in the design's favour. The new question is how often an unmeasured cross-modal factor orthogonal to depth passes the COMPLETE five-gate decision, and whether that rate changes with donor count. Single runs cannot answer either.",
  "question": "Per world, at what rate does the complete five-gate Stage-4 decision return ALL_FIVE_PASS, and how does that rate change between the qualification donor count and the real one?",
  "design": {
    "worlds": ["BIOLOGY_POSITIVE", "TRUE_NULL", "MEASURED_TECHNICAL", "HIDDEN_CONFOUND"],
    "why_all_four": "BIOLOGY_POSITIVE is the positive control and must pass at a high rate; a gate set that rejects genuine biology is not a safeguard but a defect, and without this arm a low pass rate everywhere would look like safety. TRUE_NULL anchors the nominal false-positive rate. MEASURED_TECHNICAL tests the confound the frozen basis is built to remove. HIDDEN_CONFOUND tests the one it cannot see.",
    "donor_counts": [60, 282],
    "why_these_counts": "60 is the count the end-to-end qualification used; 282 is the real substrate's qualifying donor count. Direction across the two is interpreted below.",
    "draws_per_cell": 40,
    "total_runs": 320,
    "seed_bases": "700000 + 1000 * draw_index, distinct from the canonical base 20260929, from 770101/880303/990505, and from the 600000 series spent on V1",
    "execution": "every draw is rebuilt to disk in the real Phase-B format and run through the real executor entrypoint. The world build fails closed if any control violates the frozen matching rule, so a draw that reaches the executor is a draw whose arms satisfy the construction."
  },
  "primary_statistic": "the fraction of draws in which FIVE_GATE_DECISION.ALL_FIVE_PASS is true, per (world, donor count) cell",
  "secondary_statistics": [
    "the per-gate pass rate for G1 through G5 separately, so a change can be attributed to a gate rather than guessed at",
    "the distribution of the adjusted GENE_BALANCED Delta and its one-sided lower bound",
    "the worst absolute standardised mean difference and which feature carried it",
    "the control-versus-control delta",
    "the number of edges trimmed for want of an admissible control"
  ],
  "stopping_rule": {
    "rule": "exactly 40 draws per cell. No extension, no early stop, no adding draws after seeing a rate.",
    "if_imprecise": "a cell whose Wilson 95 percent interval has a half-width greater than 0.20 is reported UNRESOLVED and is NOT topped up.",
    "if_a_run_fails": "a failed run is counted in the denominator and its error recorded. Runs are never silently dropped.",
    "if_a_world_build_fails_the_matching_audit": "that is a fixture defect, not a result. Stop the sweep and repair the generator; do not exclude the draw and continue."
  },
  "interpretation_fixed_in_advance": {
    "BIOLOGY_POSITIVE_passes_at_a_high_rate": "the five-gate decision is capable of returning a positive verdict and the other cells' low rates mean something",
    "BIOLOGY_POSITIVE_rate_is_low": "the gate set rejects genuine biology and no conclusion may be drawn from any other cell until that is explained",
    "TRUE_NULL_rate_consistent_with_0.05_or_below": "the complete decision is calibrated or conservative under a true null",
    "MEASURED_TECHNICAL_rate_near_the_TRUE_NULL_rate": "the frozen basis plus the matched control together remove measured depth confounding, and the V1 result was a fixture artifact",
    "MEASURED_TECHNICAL_rate_materially_above_TRUE_NULL": "a residual technical bias survives both the matching and the adjustment, and is an interpretation limit on every real Stage-4 result",
    "HIDDEN_CONFOUND_rate_near_the_TRUE_NULL_rate": "the gates other than G1 catch an orthogonal cross-modal factor, and the limit reported earlier is weaker than stated",
    "HIDDEN_CONFOUND_rate_materially_above_TRUE_NULL": "the complete five-gate decision cannot distinguish an unmeasured metacell-varying cross-modal factor from regulatory biology. This is an interpretation limit that travels with every Stage-4 result and is to be recorded, not repaired by changing the frozen design.",
    "HIDDEN_CONFOUND_delta_comparable_to_or_above_BIOLOGY_POSITIVE_delta": "the contract's remaining defence, that a negligibly small Delta must not be presented as biological confirmation, does not apply, because the artifact's magnitude is not small",
    "a_rate_rises_from_60_to_282_donors": "the quantity behaves like a bias: the bound tightens with n while the bias does not",
    "a_rate_falls_from_60_to_282_donors": "the quantity behaves like noise and the reduced-scale qualification was conservative"
  },
  "forbidden": [
    "changing any frozen statistical rule, basis term, weighting, bootstrap setting, gate threshold or success criterion in response to any rate measured here",
    "adding draws to a cell after seeing its rate",
    "pooling rates across worlds",
    "treating a rate measured on reduced-scale synthetic worlds as a calibration of the real Stage-4 result",
    "reporting the V1 technical rates without the qualification recorded in the supersedes block"
  ],
  "what_this_cannot_establish": "These are synthetic worlds whose generative structure and confound magnitudes I chose. The measured rates characterise the DECISION RULE under those structures. They are not an estimate of any rate the real Stage-4 analysis would exhibit, whose data-generating process is unknown. In particular the hidden confound's magnitude was set by me, and whether a cross-modal factor of that size exists in the real substrate is a separate question that this design does not address.",
  "governance": {
    "training": "OFF",
    "stage_4": "NOT_AUTHORIZED",
    "correspondence": "UNOPENED",
    "real_substrate_read": false,
    "computed_correspondence_values_on_real_data": 0
  }
}

```

You've hit your session limit · resets 6pm (America/New_York)

That monitor expiry is explained and needs no action — it was watching for the wrapper's `MEASURED_ELAPSED_SECONDS` line, which never printed because of S16 (I edited the script while bash was executing it). The benchmark itself finished; I took its timing from the tool's own output (1738.85 s for 120 motifs) and the feasibility receipt is committed.

The one thing genuinely still in flight is the Route-B fragment QC. Let me check it.

**Bash&#xA0;**&#x43;heck Route-B QC completion

IN

```
ls -1 /d/jepa_v5_outputs_20260925/v69_scenicplus/receipts/ | grep -i routeb && echo "ROUTEB_RECEIPT_PRESENT" || echo "ROUTEB_RECEIPT_ABSENT"; echo "--- outputs ---"; ls -la /d/jepa_v5_outputs_20260925/v69_scenicplus/routeB/ 2>/dev/null | tail -3; echo "--- log ---"; wc -c "/d/jepa_v5_outputs_20260925/v69_scenicplus/logs/routeb_qc.log" 2>/dev/null
```

OUT

```
ROUTEB_RECEIPT_ABSENT
--- outputs ---
total 0
drwxr-xr-x 1 dushy 197609 0 Oct  1 11:13 .
drwxr-xr-x 1 dushy 197609 0 Oct  1 11:09 ..
--- log ---
0 /d/jepa_v5_outputs_20260925/v69_scenicplus/logs/routeb_qc.log
```

**PowerShell&#xA0;**&#x43;heck Route-B QC process liveness and CPU

IN

```
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*routeb_fragment_qc*' } | Select-Object ProcessId, @{N='WS_MB';E={[math]::Round($_.WorkingSetSize/1MB,1)}}, @{N='CPU_s';E={[math]::Round($_.UserModeTime/10000000,0)}}, CreationDate | Format-List
```

OUT

```
ProcessId    : 5616
WS_MB        : 286.5
CPU_s        : 1621
CreationDate : 10/1/2026 2:30:00 PM
```

You've hit your session limit · resets 6pm (America/New_York)

You've hit your session limit · resets 6pm (America/New_York)