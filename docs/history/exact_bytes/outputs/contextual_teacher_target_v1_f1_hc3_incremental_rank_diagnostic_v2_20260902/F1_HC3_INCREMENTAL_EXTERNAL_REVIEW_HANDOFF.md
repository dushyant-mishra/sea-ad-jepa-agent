# Corrected F1 HC3 Command 15A3 — external-review handoff

Terminal: `STOP_F1_HC3_INCREMENTAL_FRONTIER_HC3_NONESTIMABLE`.

The authority typo is resolved and hash-bound: mandatory base rank 7/df 97; NPH C1 changes 7->8; C2 leaves 8->8. Incremental operator ranks are HVS 6, NPH52 1, SEA-AD 4, joint 11. Equilibration gives the same ranks. NPH component 2 is correctly classified `LOCAL_NUMERICAL_DIRECTION__REDUNDANT_IN_ACTUAL_HC3_DESIGN`.

The first NPH-bearing frontier point `(0,1,0)` is full rank 8/8 with df 96 but recreates unit leverage at `NPH52::human_NPH_906`; donor deletion lowers rank by one. It therefore fails the unchanged frozen HC3 boundary. The frontier stops after six fixed-order rows and is not complete or selectable.

No design/rank triple/estimator is selected or frozen. No expression, model, checkpoint, outcome, training, or EMA was accessed. A later prospective authority must repair the donor-isolating HC3 geometry before F1 execution.
