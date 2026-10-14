# TD relational successor — opaque rare-control profile interface

Date: 2026-10-13
Status: `PROSPECTIVE_INTERFACE_FREEZE__NO_SYNTHETIC_OR_REAL_OUTCOME_READ__NO_EXECUTION_AUTHORITY`

## Purpose

Complete the fit/controller firewall for rare-program test-of-test qualification. PR #316 requires rare relational biology to defeat matched common, measurement-quality, source/operator, wrong-cell and pseudo-rare technical controls. These controls must be executable by TD while remaining semantically blinded until after fit-side outputs are frozen.

## Fit-side representation

Every external challenge fit view contains one primary opaque profile plus zero or more **opaque control profiles** over the same blinded Z/X/Y observations.

Each control profile supplies only:

- opaque `control_id`;
- focal-anchor mask;
- lawful neighbor-pool mask;
- frozen minimum focal-anchor requirement.

The fit-side executor does not receive the control's biological meaning.

Control IDs may not contain TD capability names or any of the controller role names below.

## Controller-side role mapping

After all primary and control profiles have been executed, controller truth may map opaque control IDs to the frozen roles:

1. `DONOR_MATCHED_COMMON`
2. `DEPTH_DETECTED_SUM_MATCHED`
3. `SOURCE_OPERATOR_MATCHED`
4. `WRONG_CELL`
5. `PSEUDO_RARE_TECHNICAL`

For `REL_RARE_LOCAL_ISLAND_POSITIVE`, `REL_MULTI_ISLAND_POSITIVE`, `REL_DONOR_RESTRICTED_POSITIVE`, and `REL_TECHNICAL_TWIN_NEGATIVE`, all five control roles are mandatory for a deciding qualification. Missing roles make that capability `INCOMPLETE`; they are never silently dropped.

The controller may bind multiple opaque controls to one role, but at least one must be present for every mandatory role.

## Execution rule

TD runs the primary and every opaque control profile using the same:

- observed Z/X/Y matrices;
- measurement-support masks;
- feature IDs;
- donor/source/operator identities;
- TD-owned pair-coordinate construction;
- TD-owned concordance distance;
- TD-owned matched Y-cell null construction;
- five-scale family-wise null.

Only focal/neighbor masks and their predeclared support minima may differ between the primary and a control profile.

Rare specificity is then adjudicated with the frozen `adjudicate_rare_increment` logic: a rare program can PASS only where its relational margin exceeds the strongest matched-control margin at that scale. A raw relational PASS in a technical twin is not, by itself, biological support.

## Firewall

Fit-side structures may not contain:

- control role names;
- expected statuses;
- capability IDs;
- controller rare-state truth;
- technical-twin truth labels.

All such semantics remain controller-only and are opened after fit execution.

## Authority

This interface grants no target selection, real-data execution, TD60, Stage4 or training authority.

`OPAQUE_RARE_CONTROLS_FROZEN__FIVE_ROLE_CONTROLLER_MAPPING_REQUIRED__FIT_SIDE_BLINDED__REAL_EXECUTION_OFF`
