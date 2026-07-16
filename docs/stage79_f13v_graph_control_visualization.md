# Stage79 F13V Graph Control Visualization

F13V is a self-contained Cytoscape.js and Plotly.js explorer for the frozen Stage79 graph-control interpretation outputs. It is downstream and read-only: it displays precomputed Stage79 control graphs, empirical null distributions, donor paired differences, and diagnostics without recalculating scientific results.

The real graph retains the Stage77 edge label `Coactivity-signed candidate influence`. Control graph edges are neutral `Control-only propagated edge` records with `evidence_support=null_control`.

The explorer must not be interpreted as validating graph topology. It presents model-based control comparisons only.
