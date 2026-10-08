# Stage79 F13V Graph Control Visualization

F13V is a self-contained Cytoscape.js and Plotly.js explorer for the frozen Stage79 graph-control interpretation outputs. It is downstream and read-only: it displays precomputed Stage79 control graphs, empirical null distributions, donor paired differences, and diagnostics without recalculating scientific results.

The real graph retains the Stage77 edge label `Coactivity-signed candidate influence`. Control graph edges are neutral `Control-only propagated edge` records with `evidence_support=null_control`.

The explorer must not be interpreted as validating graph topology. It presents model-based control comparisons only.


Stage79P correction: browser-smoke metadata now distinguishes static self-contained validation from an instrumented runtime browser/network test. Until an instrumented browser test is actually run, `browser_smoke_execution_status` remains `not_run_tool_unavailable`, `file_protocol_smoke_results.pass` remains null, and `runtime_network_request_count` remains null. The explorer also hides edge labels by default, uses stable graph layout, formats tiny values in scientific notation, separates effect-size quantities into a table, and renders readable control diagnostics.


Stage79Q humane explorer pass: the interface now leads with plain-language scenario, metric, and control labels; adds a question-and-verdict panel; replaces raw pipeline labels in primary controls; keeps raw IDs in audit details; and states the model-based claim boundary directly in the UI.

Stage79R guided interpretation pass: the explorer now adds an all-ten-regulator landscape, keeps only the core interpretation controls visible by default, moves seed and graph-display switches into advanced audit controls, explains perturbation magnitudes as bounded model-input changes rather than doses or percentages, replaces zero-variance or constant-control plots with readable result cards, summarizes control seeds as above/below/equal counts, hides donor charts when every donor difference is approximately zero, and adds scenario-specific modeled target-change summaries. These additions are display-only and consume frozen Stage77-79 artifacts without changing scientific thresholds, graph weights, perturbations, JEPA embeddings, or control statistics.
