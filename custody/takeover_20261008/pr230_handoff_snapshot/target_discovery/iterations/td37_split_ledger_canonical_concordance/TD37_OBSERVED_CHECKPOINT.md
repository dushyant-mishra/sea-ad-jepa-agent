# TD37 observed-only checkpoint

Status: OBSERVED_RECURRENCE_COMPLETE__NULL_NOT_YET_RUN__NO_TARGET_AUTHORITY

Prospective freeze commit: `90056d8fba47d000077a08466ee2a623f202657a`
Null-detail clarification commit: `b7c147bd4a2bbe0cb457a613dd47d14f1b7f3f6e`

## Input audit
- B_COVERAGE_DISCOVERY rows: 25,000
- authoritative global rows: 25,000..49,999
- reset sample_row: 0..24,999 (never used for expression)
- all-42-operator common-scalar addresses: 17,186
- source rows: HVS 9,829; NPH52 3,911; SEA_AD 11,260
- source donors: HVS 41; NPH52 17; SEA_AD 46
- discovery annotations dropped before fitting: true

## Observed donor-half recurrence
Across four independent 512-gene hash panels, four deterministic donor splits, and both split directions (32 evaluations/source):

| source | prefix | median | min | max | all positive |
|---|---:|---:|---:|---:|---|
| HVS | 1 | 0.601981 | 0.490156 | 0.671751 | true |
| HVS | 2 | 0.570520 | 0.501281 | 0.626499 | true |
| HVS | 4 | 0.448215 | 0.363794 | 0.500472 | true |
| HVS | 8 | 0.269871 | 0.241433 | 0.301689 | true |
| HVS | 16 | 0.154522 | 0.136590 | 0.172849 | true |
| NPH52 | 1 | 0.606703 | -0.005634 | 0.702323 | false |
| NPH52 | 2 | 0.415949 | 0.008327 | 0.601999 | true |
| NPH52 | 4 | 0.274956 | 0.091758 | 0.464762 | true |
| NPH52 | 8 | 0.176511 | 0.081838 | 0.342571 | true |
| NPH52 | 16 | 0.108679 | 0.027052 | 0.214477 | true |
| SEA_AD | 1 | 0.819315 | -0.002143 | 0.851322 | false |
| SEA_AD | 2 | 0.777004 | 0.471135 | 0.830739 | true |
| SEA_AD | 4 | 0.703137 | 0.557918 | 0.732880 | true |
| SEA_AD | 8 | 0.519115 | 0.419168 | 0.574215 | true |
| SEA_AD | 16 | 0.329139 | 0.261150 | 0.374983 | true |

The leading single axis is unstable in a few NPH52/SEA_AD fits, whereas the 2+/4-component block remains positive. No axis or prefix is promoted before the full null.

## Local byte hashes
- `run_td37_observed.py`: `d39567769064224b0ab112c5d787c90640acee3ec919bb91a4e0bb88cbd93f1f`
- `TD37_INPUT_AUDIT.json`: `4989dbd7035a1c9fa72609f5dd92dfdf10f7b17200bc35906128282a535d2167`
- `TD37_PANEL_MANIFEST.csv`: `f63e4d7e0ca7f623aa5bbc00e422907c5d081bf8fa4691e18b858b70a9e77c3c`
- `TD37_OBSERVED_WITHIN_SOURCE.csv`: `0c229282cc7ab1ddf4cfa9c7f6dcdcaf6b413b46c66e60b10707cf1e1b8e150e`
- `TD37_COMPONENTS.csv`: `9c90cd7e63f9ce07a9453bbd626c8b13ebe527b9873a02e8a9334918ac2fb4c9`
- `TD37_OBSERVED_SUMMARY.csv`: `b4557caf37b52ed0c37640e7ec6de1726057a97d46ef14aa04a10ff1deef5484`

Interpretation remains prohibited until the pairing null is completed.
