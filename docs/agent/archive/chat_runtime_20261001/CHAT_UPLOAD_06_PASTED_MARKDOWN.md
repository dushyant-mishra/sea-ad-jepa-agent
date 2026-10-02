Consolidated to a single watch on terminal states only — done, error, or container-gone — so silence means running and any ending produces exactly one event.

**Curve so far (idle machine, pinned seed, pinned BLAS, identical digests at every point):**

```
t4   wall 604s   cbust 339.6s   non-scoring 264.4s
t8   wall 486s   cbust 222.4s   non-scoring 263.6s   ← minimum
t16  wall 513s   cbust 184.0s   non-scoring 329.0s

```

t2 has been running \~5 min of an expected \~16; then t1 at \~27 min. Completion near 05:31 UTC.

The recommendation is already bracketed at **8 workers**, and I can say *why* rather than only *that*: scoring keeps improving past 8 but only weakly (1.21× for a doubling), while the non-scoring phase gains nothing from extra workers and takes a 65 s penalty once workers exceed the 8 physical cores. The remaining two points add parallel efficiency against a 1-worker baseline, which the mandate asked for; they cannot move the minimum.

I'll hold the recommendation until the curve is complete, then run the 128-motif decomposition for shard size, write the full benchmark receipt, and move to Route-B consensus peaks in the agreed order. Every receipt citing the worker count will record that it was read off a **16-motif** curve, per your instruction that the S21 deviation must not be silently upgraded later.

One more self-audit item worth checking before the curve runs, and it bears directly on the headline V2 finding. G2 is the gate rejecting 38% of genuine biology — let me verify I implemented it the way the contract specifies, rather than the way I chose.

**Bash&#xA0;**&#x43;heck what the contract specifies for the G2 test

IN

```
cd "/d/jepa_wt_v64_sampler_20260930" && python -c "
import json
A=json.load(open('results/v64/phase_b_design/V64_STAGE4_EXECUTION_AUTHORITY_V1.json'))
afg=A['SUCCESS_CRITERION_FROZEN_BEFORE_ANY_RESULT']['anti_false_green']
print(json.dumps([x for x in afg if 'CONTROL_VS_CONTROL' in x.get('name','')],indent=1))
print('--- design contract ANTI_FALSE_GREEN ---')
D=json.load(open('results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json'))
print(json.dumps(D.get('ANTI_FALSE_GREEN_CONTROLS'),indent=1)[:1800])
"
```

OUT

```
[
 {
  "name": "CONTROL_VS_CONTROL_NULL",
  "construction": "the two independent control draws are contrasted against each other through the identical pipeline",
  "requirement": "must not show excess. A nonzero control-vs-control contrast indicates the pipeline itself manufactures a difference, and any linked-vs-control result is then uninterpretable.",
  "if_it_fails": "STOP. Do not report the primary as a biological result."
 }
]
--- design contract ANTI_FALSE_GREEN ---
[
 {
  "name": "CONTROL_VS_CONTROL_NULL",
  "construction": "the two independent control draws are contrasted against each other through the identical pipeline",
  "requirement": "must not show excess. A nonzero control-vs-control contrast indicates the pipeline itself manufactures a difference, and any linked-vs-control result is then uninterpretable.",
  "if_it_fails": "STOP. Do not report the primary as a biological result."
 },
 {
  "name": "COVARIATE_BALANCE",
  "requirement": "worst |standardised mean difference| across the 14 frozen features <= 0.25 between linked and matched control"
 },
 {
  "name": "SUPPORT_CONCENTRATION",
  "requirement": "top 1% of donors contribute <= 10% of the primary statistic's weight; Kish ESS over donors reported"
 },
 {
  "name": "PAIRING_CORROBORATION",
  "requirement": "the blocking pairing precondition passed, with its exact mismatch counts reported"
 }
]
Shell cwd was reset to d:\Jepa project
```

**S102, and it's a significant one.** The contract specifies *no test and no level* for G2 — only "must not show excess. A nonzero control-vs-control contrast indicates the pipeline itself manufactures a difference."

I implemented it as a two-sided 95% bootstrap CI containing zero. That's **my choice, not the design's** — and it has a consequence that explains the V2 result:

**A null test of "no difference" gets stricter as n grows.** The CI shrinks around any residual drift, so with enough donors it rejects regardless of whether the pipeline is sound. That is exactly why G2 rejects 22% of genuine biology at 60 donors and 38% at 282 — *the rate rises with data*. For a gate whose job is "the pipeline isn't manufacturing a difference," that's the wrong shape.

So my headline V2 finding — "the design discards a third of real signal" — may be an artifact of a test I chose, not a property of the frozen design.

**Bash&#xA0;**&#x41;dd the scale-free diagnostic and verify

IN

```
cd "/d/jepa_wt_v64_sampler_20260930" && python - <<'PY'
import hashlib
p="scripts/v64/stage4_executor_v1.py"
s=open(p,encoding="utf-8").read(); b0=hashlib.sha256(s.encode()).hexdigest()
old='''        G2_CONTROL_VS_CONTROL_NOT_DISTINGUISHABLE_FROM_ZERO=dict(
            passed=g2, delta=cvc_val,
            ci95=None if boot_cvc is None else
            [float(np.quantile(boot_cvc, 0.025)), float(np.quantile(boot_cvc, 0.975))]),'''
new='''        G2_CONTROL_VS_CONTROL_NOT_DISTINGUISHABLE_FROM_ZERO=dict(
            passed=g2, delta=cvc_val,
            ci95=None if boot_cvc is None else
            [float(np.quantile(boot_cvc, 0.025)), float(np.quantile(boot_cvc, 0.975))],
            TEST_IS_NOT_SPECIFIED_BY_THE_CONTRACT=dict(
                what_the_contract_says="must not show excess. A nonzero control-versus-"
                                       "control contrast indicates the pipeline itself "
                                       "manufactures a difference.",
                what_is_implemented="a two-sided 95 percent donor-bootstrap interval must "
                                    "contain zero",
                who_chose_it="the executor, not the contract. No test and no level is "
                             "frozen anywhere for this gate.",
                consequence="a null test of no-difference becomes STRICTER as the donor "
                            "count rises, because the interval tightens around residual "
                            "drift faster than the drift disappears. The gate therefore "
                            "rejects more often with more data regardless of whether the "
                            "pipeline is sound, which is the wrong shape for a gate whose "
                            "purpose is to detect manufactured differences. This is "
                            "recorded as an open specification gap, S102, and the choice "
                            "belongs to the contract owner rather than to this code.",
                scale_free_alternative_reported_below="the magnitude ratio, which does "
                                                      "not tighten with n and is reported "
                                                      "WITHOUT a threshold so that no "
                                                      "second unfrozen number is invented "
                                                      "here"),
            magnitude_ratio_diagnostic=dict(
                value=None if (cvc_val is None
                               or not results[FROZEN["primary_weighting"]]["delta"])
                else abs(cvc_val) / abs(results[FROZEN["primary_weighting"]]["delta"]),
                definition="|control-versus-control delta| divided by |primary delta|",
                is_not_a_gate=True,
                why_no_threshold="choosing one now would repeat the defect this entry "
                                 "exists to disclose")),'''
assert s.count(old)==1
s=s.replace(old,new)
open(p,"w",newline="\n",encoding="utf-8").write(s)
import ast; ast.parse(open(p,encoding="utf-8").read())
print("changed:", b0!=hashlib.sha256(open(p,encoding="utf-8").read().encode()).hexdigest())
PY
cd "/d/jepa_wt_v64_sampler_20260930" && timeout 900 python scripts/v64/stage4_executor_v1.py --synthetic-world BIOLOGY_POSITIVE >/dev/null 2>&1; python -c "
import json;R=json.load(open('D:/jepa_v5_outputs_20260925/v64_stage4_synthetic/_results/V64_STAGE4_RESULT_BIOLOGY_POSITIVE.json'))
g=R['FIVE_GATE_DECISION']['G2_CONTROL_VS_CONTROL_NOT_DISTINGUISHABLE_FROM_ZERO']
print('G2 passed:',g['passed'],' delta=%.5f'%g['delta'],' ci95=',[round(x,5) for x in g['ci95']])
print('magnitude ratio |cvc|/|primary| = %.5f'%g['magnitude_ratio_diagnostic']['value'])
"
```

OUT

```
changed: True
G2 passed: True  delta=0.00280  ci95= [-0.0063, 0.01198]
magnitude ratio |cvc|/|primary| = 0.00505
Shell cwd was reset to d:\Jepa project
```

**Bash&#xA0;**&#x43;ommit the G2 specification-gap disclosure

IN

```
cd "/d/jepa_wt_v64_sampler_20260930" && git add scripts/v64/stage4_executor_v1.py && git commit -q -m "$(cat <<'EOF'
S102: the G2 test is not specified by the contract, and the one I chose gets stricter with n

The contract says only that the control-versus-control contrast "must not show
excess" and that "a nonzero control-versus-control contrast indicates the
pipeline itself manufactures a difference". It specifies no test, no statistic
and no level for this gate. I implemented a two-sided 95 percent donor-bootstrap
interval containing zero, and that was my choice rather than the design's.

The choice has a consequence that explains the V2 result. A null test of
no-difference becomes STRICTER as the donor count rises, because the interval
tightens around residual drift faster than the drift disappears. So the gate
rejects more often with more data regardless of whether the pipeline is sound --
which is the wrong shape for a gate whose stated purpose is to detect
manufactured differences.

That means my V2 headline, that the complete decision discards roughly a third
of real signal at 282 donors, may be an artifact of the test I picked rather than
a property of the frozen design. The 22 percent at 60 donors rising to 38 percent
at 282 is exactly the signature of a null test tightening, not of a design
failing. The same caveat attaches to the hidden-confound rejection rates, since
G2 is what rejects that world.

I have NOT changed the gate. Changing it now, after seeing which way it falls,
would be the post-hoc repair this project forbids, and the choice belongs to the
contract owner rather than to this code. What the executor now does instead is
disclose the gap in the result itself and report a scale-free companion -- the
ratio of the control-versus-control delta to the primary delta, which does not
tighten with n.

That ratio is reported WITHOUT a threshold, deliberately. Attaching one would
invent a second unfrozen number in the act of disclosing the first. On the
canonical biology world it reads 0.00505 against a gate interval of [-0.0063,
0.01198], so both readings agree there; the point is that they need not agree as
n grows, and now a reader can see both.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)" && git push -q origin claude/v64-exact-sampler-successor-20260930 && git log --oneline -1
```

OUT

```
759bf0f2 S102: the G2 test is not specified by the contract, and the one I chose gets stricter with n
Shell cwd was reset to d:\Jepa project
```

**This changes how my V2 headline should be read, and I want to flag it before it gets quoted.**

The 22% → 38% rise in G2 rejecting genuine biology is **exactly the signature of a null test tightening with sample size**, not of a design failing. More donors shrink the interval around residual drift faster than the drift disappears, so the gate rejects more as data accumulates. That's the wrong shape for a gate whose stated job is detecting manufactured differences — and the shape came from my implementation, not from anything frozen.

The same caveat attaches to the hidden-confound rejection rates, since G2 is the gate doing that work too.

**I have not changed the gate.** Changing it now, after seeing which way it falls, is the post-hoc repair this project forbids — and more importantly, the choice belongs to you, not to my code. What the executor does instead is disclose the gap inside the result and report a **scale-free companion**: the ratio of control-vs-control delta to primary delta, which doesn't tighten with n.

That ratio is reported **without a threshold**, deliberately. Attaching one would invent a second unfrozen number in the very act of disclosing the first. On the canonical biology world it reads `0.00505` against a gate interval of `[-0.0063, +0.01198]` — both readings agree there. The point is they need not agree as n grows, and now both are visible.

**The decision you and Sol face** is which reading G2 should use, made prospectively:

- **Null-test reading** (what I implemented): "no detectable difference." Gets stricter with data; at full scale may reject sound pipelines.
- **Magnitude reading**: "the manufactured difference is small relative to the effect." Scale-free; needs a threshold nobody has frozen.

Neither is wrong under the contract's wording. But the choice materially changes the Stage-4 pass rate, and it should be made before a real result exists rather than after.

This also conditions the G2 sensitivity curve I'm holding — it measures G2, so its result inherits whichever reading is in force. The receipt will record both so the curve can be re-read without re-running.

Scaling table still has the machine.