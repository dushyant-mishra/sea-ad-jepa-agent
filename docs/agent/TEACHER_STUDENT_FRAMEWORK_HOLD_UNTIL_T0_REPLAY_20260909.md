# Teacher/student framework hold until T0 replay — 2026-09-09

The teacher/student framework should be designed around the real dataset authority chain, not around synthetic stand-ins.

## Current position

Do not promote teacher/student work to production until the following T0 authorities exist as replayed real-dataset artifacts:

1. raw-source population authority over 20,804 accepted rows;
2. technical-completeness authority over the real B2 closure, physical plan, B1 projection and counts payloads;
3. eligible-donor authority after the above gates open.

## What can continue now

Design-only work can continue on:

- authority DAG shape;
- manifest schemas;
- replay contracts;
- GPU execution plan;
- data loaders that consume immutable authority packages;
- teacher/student interfaces that require authority roots as inputs.

## What cannot continue now

Do not train, evaluate, or claim a production teacher/student result using:

- synthetic H5AD fixtures;
- three-row spot checks;
- unmaterialized T0 authorities;
- detached donor summaries;
- downstream eligibility assumptions.

## Required teacher/student input contract

A production teacher/student run must require explicit authority roots for:

- raw-source population authority;
- technical completeness;
- eligible donors;
- feature projection;
- donor roles;
- AT8 availability and later numeric AT8 authority when that gate opens;
- train/validation/test split identity;
- source data package root.

Missing authority roots should be a STOP, not a warning.

## Dataset-first training principle

The student is not trained against an invented framework target. It is trained only after the dataset authorities define the lawful population, lawful covariates, lawful feature projection, and lawful response-access boundary.

Until then, the correct teacher/student work is interface hardening, replay design, and GPU readiness planning, not biological inference.
