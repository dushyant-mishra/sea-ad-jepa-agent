# JEPA premise V3 self-review — 2026-10-06

Role: `SELF_REVIEW__NOT_INDEPENDENT_REVIEW`
Branch reviewed: `design/premise-qualification-contract-v3-20261006`
Reviewed through: `b90eb8104d464693cdf0367bf08a4dd88e2fa178`

## Scope

This artifact records internal review and subsequent audit repairs. It is not independent review, merge authority, Stage-A authority or training authority.

## Findings discovered and repaired during self-review

### SR-1 — machine-readable source-document paths were stale

Four machine-state paths did not match the actual V3 filenames.

Repair: add source-document existence test, observe RED (16 passed / 1 failed naming exactly four paths), then correct only those four paths. Subsequent guard GREEN.

### SR-2 — CLI ignored a supplied state path

The validator CLI accepted an optional path syntactically but always loaded the canonical state file. A deliberately corrupt supplied file therefore returned PASS.

Repair: add supplied-corrupt-state CLI test, observe RED (26 passed / 1 failed), then make the CLI validate the supplied path. Subsequent guard GREEN.

## Independent-audit addendum repairs

A later independent audit identified five bounded defects/ambiguities. They were repaired without reopening the premise design.

### IA-1 — Stage-A verdicts and diagnostic firewall were not enforced by `validate_state()`

New adversarial supplied-file CLI tests changed the verdict roster and diagnostic firewall and correctly failed before repair.

Repair: validator now enforces the frozen Stage-A verdict roster and the inner-TRAIN-only / freeze-before-held-donor diagnostic firewall.

### IA-2 — whole-JSON fail-closed behavior was incomplete

The prior validator ignored missing and unexpected contract fields.

Repair: the validator now checks the complete top-level schema and the nested contract objects used by V3 governance, rejecting missing required fields and unrecognized fields.

### IA-3 — CI path coverage omitted binding V3 source documents

The guard did not run for every document named by the machine-readable `source_documents` roster.

Repair: CI path coverage now includes every binding V3 source document, and a test requires that every machine-bound source document appears in the workflow trigger.

### IA-4 — biological-evidence convergence could collapse into count-depth thinning

The conceptual distinction was present but the operator was not frozen strongly enough.

Repair: biological-evidence perturbation is now restricted to feature/context-support removal and explicitly forbids count-depth thinning; measurement-depth perturbation uses count-depth thinning while holding the information universe fixed.

### IA-5 — held-donor alignment leakage was not explicitly prohibited

The stability protocol allowed alignment but did not explicitly require the alignment transform to be fitted without held-donor evidence.

Repair: alignment must fit on `INNER_TRAIN_ONLY`, freeze before held-donor evaluation, and held donors may not influence the transformation.

## RED→GREEN evidence for the addendum

RED run `37504021676` at test head `d632f1b905ba198e589ce599b0abbb7e3f92eeaa` produced exactly:

`10 failed, 30 passed`

The failures corresponded to the five addendum items: Stage-A binding, schema closure, CI coverage, uncertainty-operator separation and held-donor alignment isolation.

After the bounded repairs, GREEN run `37504545106` at head `b90eb8104d464693cdf0367bf08a4dd88e2fa178` produced:

`40 passed`

## Remaining authority boundary

PR #220 must remain draft until a separate reviewer attacks the whole branch for hidden scientific flexibility, representation favoritism, observation-channel shortcuts, external-asset overclaim, estimand leakage, and machine/prose mismatch.

Closing the five audit items does **not** authorize Stage A or training.

## Authority state

`TRAINING=OFF`; Stage A execution not authorized; TEST sealed; Morabito protected; no target winner; no representation winner; no estimand selected; no deciding numeric margin selected.
