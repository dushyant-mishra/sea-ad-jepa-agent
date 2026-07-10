# Stage72B PI summary

Stage72B produced a conservative Morabito/GSE174367 microglia coactivity graph
candidate from public snRNA data. It found 541 bootstrap-stable
TF-target coactivity edges among predeclared rare-microglia genes and regulators.

Important caveat: the acquired snATAC peak matrix is interval-only in the
processed file, so this is not yet a validated chromatin-linked GRN. It is a
useful graph prior for the next diagnostic benchmark, not external validation.

Next recommended step: Stage73 should compare this context-specific candidate
graph against no-graph, STRING, random/degree-matched controls, and shuffled
candidate-GRN controls without tuning the graph after seeing pathology outcomes.
