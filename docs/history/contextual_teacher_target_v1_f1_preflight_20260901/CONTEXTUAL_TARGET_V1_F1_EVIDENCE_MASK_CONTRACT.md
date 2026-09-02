# F1 evidence-mask contract (pre-result)

Evidence levels are exactly 20, 40, 60, 80 and 100%; 60% is primary. For row `r` and scalar-measured query `q`, define eligible context `E={j: state[r,j]=MEASURED_SCALAR and j!=q}`. Reject the row/query if `q` is not scalar-measured.

Seed authority is `SHA256("CTX-F1-EVIDENCE-V1|" || F0-manifest-root || "|" || prospective-contract-SHA || "|" || query-entry-SHA)` = `c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f` using UTF-8 lowercase hex authorities. For every `j in E`, compute `SHA256(seed || "|" || canonical-row-locator || "|" || decimal-q-address || "|" || decimal-j)` in UTF-8, sort by digest bytes then integer address, and let level `p` select the first `floor(p*|E|/100)` entries. The same single ordering is reused at every level, proving 20 subset 40 subset 60 subset 80 subset 100. At 100%, all of `E` is selected. The query scalar is withheld at every level.

Selection uses no expression value or model output. A measured zero has exactly the same eligibility and hash rank as a nonzero scalar. The teacher-rich safe target uses all of `E`; the student partial path uses the selected prefix. State 0, state 2, and artificial evidence masking remain distinct. Exact row/query/level/index-list hashes are result provenance. Any nesting, query-withholding, authority-hash, or state-semantic failure is terminal.
