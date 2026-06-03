# SEA-AD Low-Pathology Anchor Audit

This audit asks whether SEA-AD already contains enough low-AD-pathology Microglia-PVM donors to serve as an internal v2 homeostatic reference.

Terminology: these donors are **low-pathology internal reference donors**, not pristine healthy controls. They are aged postmortem donors and may still carry aging, vascular, agonal, PMI, or systemic stress signatures.

## Thresholds

- AT8 q25 threshold: 0.0491383
- 6e10/A beta q25 threshold: 0.158095
- Sufficient Microglia-PVM cells: >= 200
- Relaxed anchor: ADNC Not AD/Low, low AT8, low 6e10, no dementia, sufficient Microglia-PVM cells
- Strict anchor: relaxed anchor plus Braak <= II and Thal <= 2

## Counts

- Total metadata/pathology donors: 89
- Relaxed low-pathology anchors: 10
- Strict low-pathology anchors: 4

## Group Summary

                       group  n_donors  Age at Death_median  PMI_median  RIN_median  microglia_pvm_n_cells_median  percent AT8 positive area_Grey matter_median  percent 6e10 positive area_Grey matter_median  braak_numeric_median  thal_numeric_median  adnc_rank_median           cognitive_status_counts                                      adnc_counts
                  all_donors        89                 90.0    6.908333       8.630                         391.0                                      0.383231                                       1.618865                   5.0                  4.0               2.5 No dementia:42; Dementia:42; NA:5 High:42; Intermediate:21; Low:12; Not AD:9; NA:5
relaxed_low_pathology_anchor        10                 82.0    5.750000       9.105                         410.5                                      0.016768                                       0.000957                   4.0                  0.0               0.0                    No dementia:10                                  Not AD:7; Low:3
 strict_low_pathology_anchor         4                 76.5    9.150000       9.300                         410.5                                      0.013843                                       0.001104                   1.0                  0.5               0.5                     No dementia:4                                  Not AD:2; Low:2
                  non_anchor        79                 91.0    6.958333       8.615                         391.0                                      0.621226                                       1.992389                   5.0                  4.0               3.0 Dementia:42; No dementia:32; NA:5  High:42; Intermediate:21; Low:9; NA:5; Not AD:2

## Recommendation

SEA-AD does not have enough low-pathology donors to serve as the only homeostatic anchor. Use SEA-AD low-pathology donors for matched internal calibration and add external healthy microglia, such as CELLxGENE/Siletti, for broad Stage A pretraining.

Recommended v2 curriculum:

1. Broad healthy/normal microglia pretraining from external public data.
2. SEA-AD low-pathology internal anchor calibration.
3. SEA-AD disease-deviation fine-tuning.
4. External observational and perturbational validation.
