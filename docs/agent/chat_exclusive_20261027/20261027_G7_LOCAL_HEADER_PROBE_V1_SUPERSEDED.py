"""Read-only, bounded source-admissibility probe for local G7 candidates.

Inspects ZIP directory/header metadata only. Never opens .pt files or unpickles.
This is NOT a quality-control assessment or independent data attestation.
"""
import csv, io, json, zipfile
from pathlib import Path

ROOT = Path('/mnt/data')
EXPR = ROOT / 'expression.zip'
CAL = ROOT / 'FOUNDATION_CALIBRATION_BUNDLE_20260824.zip'


def header(z, path):
    with z.open(path) as fh:
        return next(csv.reader(io.TextIOWrapper(fh, encoding='utf-8-sig', newline='')))


with zipfile.ZipFile(EXPR) as z:
    names=z.namelist()
    sample = 'expression/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv'
    audit = 'expression/expression/FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json'
    audits = json.loads(z.read(audit))
    operator_paths = sorted(p for p in names if p.endswith('.meta.csv') and 'sample_operator_metadata/' in p)
    operators = [header(z, p) for p in operator_paths]
    freeze_header = header(z, sample)
    expr_output = dict(
        expression_matrix_claim=audits.get('normalization'),
        expression_rows_claim=audits.get('cells'),
        address_count_claim=audits.get('addresses'),
        shard_count_claim=len(audits.get('shards',[])),
        sampled_operator_metadata_file_count=len(operators),
        metadata_headers_all_equal=len({tuple(x) for x in operators}) == 1,
        sampled_operator_metadata_columns=operators[0] if operators else [],
        sample_freeze_columns=freeze_header,
        expression_read_before_freeze_is_selection_field='expression_read_before_freeze' in freeze_header,
    )
with zipfile.ZipFile(CAL) as z:
    names=z.namelist()
    status_paths=[x for x in names if x.endswith('/BUNDLE_STATUS.json')]
    s=json.loads(z.read(status_paths[0])) if len(status_paths)==1 else {}
    cal_output=dict(
        status_schema=s.get('schema'),
        expression_cells_claim=s.get('expression_cells'),
        metadata_cells_claim=s.get('metadata_cells'),
        operator_count_claim=s.get('operators'),
        dev_sealed_expression_included=s.get('dev_sealed_expression_included'),
        pathology_fields_included=s.get('pathology_fields_included'),
        files_with_raw_or_count_in_name=[x for x in names if not x.endswith('/') and any(y in Path(x).name.lower() for y in ('raw_count', 'raw_read', 'read_level'))],
    )
required=[
    'authenticated physical source operator and address per deciding row',
    'independent raw count/read evidence or verifiable raw molecular observations',
    'measured-zero versus structural-unmeasured/collision status grounded in raw assay',
    'evidence-right/cell-source ownership provenance from authenticated producer',
    'query-excluded raw depth and normalization lineage for that deciding row',
    'the actual G7 V3 decision-row digest and consumer linkage',
]
report={
    'schema':'JEPA_G7_LOCAL_ARCHIVE_ADMISSIBILITY_PROBE_20261027',
    'scope':'Non-executing read of bounded metadata in two existing local ZIP attachments only; no 41K-part extraction, no checkpoint read, no user identity values emitted',
    'expression_zip':expr_output,
    'calibration_zip':cal_output,
    'assessment':'INSUFFICIENT_TO_AUTHORIZE_AUTHENTIC_G7_E3',
    'observed_limitations':[
        'Expression audit states log1p(raw_count*10000/full_source_library); not authenticated direct raw-molecule provenance.',
        'Sample/operator metadata present stable_key, cell_id, donor_id, source_library; lack read-level/raw-count/evidence-right fields.',
        'Sample-freeze manifest provides source/operator/sample selection and support labels, not per-query raw count and G7 deciding-row digest.',
        'These two archives do not establish an authenticated physical producer, even if numeric transformations could be algebraically inverted approximately.',
        'Archive content names/headers cannot prove full external source absence; historical custody and large 41K parts are not re-audited here.',
    ],
    'required_before_G7':required,
    'authorization':'TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED',
}
(ROOT/'g7_local_input_admissibility_20261027.json').write_text(json.dumps(report,indent=2)+'\n')
print('G7_LOCAL_METADATA_PROBE_PASS')
print(json.dumps(dict(expression=expr_output,calibration=cal_output,assessment=report['assessment']), indent=2))
