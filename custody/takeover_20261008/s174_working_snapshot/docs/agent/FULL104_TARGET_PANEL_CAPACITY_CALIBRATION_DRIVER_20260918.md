# FULL104 target-panel capacity calibration driver

The canonical driver is:

`scripts/agent/run_full104_target_panel_capacity_calibration_v1.py`

It is intentionally **not** a masking-policy runner.

It verifies the authenticated FULL104 Level-4 manifest, the current 41,238-row
canonical molecular-address registry, the census V2 authority, source-stratified
donor split, target eligibility receipt, support authority, and the explicit
primary-attacker parameter authority before reading blocks.

Target identity always comes from `molecular_address_id` in the authenticated
canonical registry. Column number is never substituted for identity.

The nested target-count ladder is 128 -> 256 -> 512 -> 1024. One invocation may
evaluate only the next lawful rung. It runs only two burden-free controls:
a deterministic planted visible proxy and a deterministic within-donor shuffled
null. Real masking-policy outcomes are never read.

A first execution cannot qualify the rung. It writes the planted and shuffled
target x donor matrices and returns `REPLAY_REQUIRED_BEFORE_CAPACITY_VERDICT`.
A second execution must reproduce both matrices exactly. Only then is the
paired target-and-donor bootstrap allowed to issue a capacity receipt/verdict.

If a rung qualifies, the driver writes the target-panel sizing receipt and
refuses higher rungs. If it fails, the next rung may be evaluated in a later
invocation. This prevents execution order or convenience from silently deciding
the scientific design.

Historical 32-target masking and nonlinear results remain planning evidence only;
they are not inputs to this driver.
