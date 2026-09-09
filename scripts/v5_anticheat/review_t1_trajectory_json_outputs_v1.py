#!/usr/bin/env python3
"""External-style review of T1 trajectory JSON outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path


def main(root: Path = Path('.')) -> None:
    review = root / 'results' / 'T1_TRAJECTORY_JSON_REVIEW_V1.json'
    csv_path = root / 'results' / 'T1_TRAJECTORY_LOSS_GRADIENT_SUMMARY_V1.csv'
    data = json.loads(review.read_text(encoding='utf-8'))
    if data['schema'] != 'T1_TRAJECTORY_JSON_REVIEW_V1':
        raise RuntimeError('bad schema')
    if data['update_count'] != 205 or data['first_update'] != 1 or data['last_update'] != 205:
        raise RuntimeError('bad update coverage')
    if not data['loss']['u1_to_u205_pct_reduction'] > 0.99:
        raise RuntimeError('strong loss decrease not recorded')
    if data['gradient_component_surface']['missing_parameter_tensors_total'] != 0:
        raise RuntimeError('unexpected missing aggregate components')
    if data['gradient_component_surface']['nonfinite_parameter_tensors_total'] != 0:
        raise RuntimeError('unexpected nonfinite aggregate components')
    if 'cannot prove the 48 protected attention-routing tensors were live elementwise' not in data['gradient_component_surface']['limitation']:
        raise RuntimeError('missing aggregate-telemetry limitation')
    decision = data['authority_decision']
    if decision['historical_u10_to_u205_resume_authority'] is not False:
        raise RuntimeError('historical resume authority must be false')
    if decision['historical_u10_to_u205_biological_teacher_authority'] is not False:
        raise RuntimeError('historical biological teacher authority must be false')
    if decision['loss_decrease_is_not_biological_qualification'] is not True:
        raise RuntimeError('loss-only rejection must be true')
    rows = list(csv.DictReader(csv_path.open(encoding='utf-8')))
    if len(rows) < 8 or rows[0]['update'] != '1' or rows[-1]['update'] != '205':
        raise RuntimeError('key-update CSV malformed')
    print('PASS_T1_TRAJECTORY_JSON_OUTPUT_REVIEW_V1')


if __name__ == '__main__':
    main()
