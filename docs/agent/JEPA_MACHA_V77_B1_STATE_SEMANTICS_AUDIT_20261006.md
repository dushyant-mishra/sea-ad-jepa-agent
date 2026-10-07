# JEPA Macha/V77 — B1 synthetic-state semantics audit

Date: 2026-10-06
Parent audit head before write: `2e01eb374de1ec7fd19dd749b005d90acfab40a6`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Finding

B1's six `state_index` values are generic synthetic categories, not biologically grounded microglial states.

Evidence from the generator:

- `state_index` is a uniform per-cell random draw into six categories;
- state assignment is not derived from donor, source, real RNA, cell ontology or known microglial programs;
- each state's 400-address module is allocated by a seeded permutation of the 41,238-address registry;
- the allocator deliberately does not use gene symbols or pathway annotations;
- adjacent synthetic state modules have a declared partial overlap, but that overlap is a modeling choice rather than measured microglial pathway overlap.

Current classification:

`B1_STATE = GENERIC_SYNTHETIC_IDENTIFIABILITY_SIGNAL__NOT_A_MICROGLIAL_STATE_MODEL`

## Biological meaning

Calling B1 a `cell-state mixture` is acceptable inside the simulator, but it must not be read as homeostatic, DAM, inflammatory, proliferative or any other real microglial state.

The synthetic state asks a narrower question: can a method recover a categorical program when a known pattern has been planted?

It does not ask whether the program resembles real microglial biology.

## Consequence for S157

The S157 BIO arm uses one B1 state only as a grouping variable and then plants a separate coherent challenge module. The exact-twin identifiability result remains valid because it depends on identical observables, not on biological realism of the state label.

But the challenge cannot validate that current V77 state architecture reproduces real class-associated RNA organization.

## Consequence for future synthetic realism

If a later lane wants a biologically realistic microglial-state world, the state programs would need independent prospective construction and controls. They should not be obtained by simply mapping current B1 labels onto named biological states after the fact.

That would be label retrofitting, not validation.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object or estimand winner.
