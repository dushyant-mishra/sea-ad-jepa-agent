"""Read-only, digest-bound census of reader partitions by study (metadata ONLY).

This answers a narrowly unresolved question from the September 25 V26 handoff:
how are reader_fit / reader_validation / reader_oracle distributed among HVS,
NPH52 and SEA_AD? It binds the frozen reader split to an INDEPENDENT frozen
foundation registry and checks the archived context summary and fit-only counts.

No expression, per-cell raw blocks, donor pathology or any reserved outcomes.
Metadata inspection is not a release of validation/oracle expression outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import zipfile

ARCHIVE_SHA256 = '07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444'
BASE = 'FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/'
MEMBERS = {
    'reader': ('splits/reader_donor_split.csv',
               'efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511',
               ('donor_id', 'reader_partition')),
    'foundation': ('splits/foundation_split_registry.csv',
                   '35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433',
                   ('split_domain', 'cohort', 'study_id', 'canonical_person_id',
                    'split_group_id', 'split', 'assignment_method', 'freeze_seed',
                    'pathology_used_for_foundation_split')),
    'context': ('metadata/FOUNDATION_METADATA_ALL149_CONTEXT.csv',
                'ea4c28afeafac46e63545990c1d9884189647735f2049e947558eeb2de7bc1b0',
                ('partition', 'source', 'cell_count', 'donor_count')),
    'fit_metadata': ('metadata/FOUNDATION_METADATA_DONOR.csv',
                     'c9cbe47d4727aabec8a0c3fed5474c2dab4f9f2b8848357e08b0cec6ef044508',
                     ('donor_id', 'cell_count', 'original_t1_cells')),
}
PARTITIONS = ('reader_fit', 'reader_validation', 'reader_oracle')
SOURCES = ('HVS', 'NPH52', 'SEA_AD')
EXPECTED_READER_COUNTS = {'reader_fit': 104, 'reader_validation': 22, 'reader_oracle': 23}
REPORTED_VALIDATION_COUNTS = {'HVS': 10, 'NPH52': 0, 'SEA_AD': 12}
EXPECTED_CELLS_FIT = 4_553_407


def _sha_stream(f) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: f.read(8 << 20), b''):
        h.update(chunk)
    return h.hexdigest()


def _csv(raw: bytes, header: tuple[str, ...], name: str) -> list[dict[str, str]]:
    stream = io.StringIO(raw.decode('utf-8-sig'), newline='')
    reader = csv.DictReader(stream, strict=True)
    if tuple(reader.fieldnames or ()) != header:
        raise ValueError(f'{name}: exact frozen CSV header mismatch')
    rows = []
    for n, row in enumerate(reader, start=2):
        if None in row or len(row) != len(header) or any(
            not isinstance(v, str) or v != v.strip() or (not v and name != 'foundation')
            for v in row.values()
        ):
            raise ValueError(f'{name}: malformed CSV row {n}')
        rows.append(row)
    return rows


def _natural(value: str, name: str, *, positive: bool = True) -> int:
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ValueError(f'{name}: count must be an exact decimal integer')
    v = int(value)
    if v < (1 if positive else 0):
        raise ValueError(f'{name}: nonpositive count')
    return v


def derive_reader_sources(reader: list[dict], registry: list[dict]) -> tuple[dict, dict]:
    """Pure structural helper; has NO frozen SHA authority on its own."""
    if len(reader) != len({r.get('donor_id') for r in reader}):
        raise ValueError('duplicate reader donor identity')
    # The split-freeze explicitly attests pathology was never used for ANY
    # foundation, continuation, development, sealed or external assignment.
    if any(r.get('pathology_used_for_foundation_split') != 'False' for r in registry):
        raise ValueError('frozen registry contains pathology-dependent split')
    foundation = {}
    continuation = set()
    for row in registry:
        if row.get('split_domain') != 'continuation' or row.get('split') != 'train':
            continue
        study = row.get('study_id')
        person = row.get('canonical_person_id')
        if study not in SOURCES or not isinstance(person, str) or not person.startswith(study + '::'):
            raise ValueError('continuation train study/person identity invalid')
        donor = person.split('::', 1)[1]
        if not donor or donor in continuation or row.get('split_group_id') != person:
            raise ValueError('duplicate or invalid continuation donor identity')
        continuation.add(donor)
    foundation = {}
    for row in registry:
        if row.get('split_domain') != 'foundation' or row.get('split') != 'train':
            continue
        study = row.get('study_id')
        person = row.get('canonical_person_id')
        if study not in SOURCES or not isinstance(person, str) or not person.startswith(study + '::'):
            raise ValueError('foundation train study/person identity invalid')
        donor = person.split('::', 1)[1]
        if not donor or donor in foundation or row.get('split_group_id') != person:
            raise ValueError('foundation training donor duplicate or group mismatch')
        if row.get('pathology_used_for_foundation_split') != 'False':
            raise ValueError('foundation training split asserts pathology use')
        foundation[donor] = study
    counts = Counter()
    seen = set()
    for row in reader:
        donor = row.get('donor_id')
        part = row.get('reader_partition')
        if part not in PARTITIONS or donor not in foundation:
            raise ValueError('reader donor outside exact foundation train or invalid partition')
        if donor in seen:
            raise ValueError('duplicate reader donor identity')
        seen.add(donor)
        counts[(part, foundation[donor])] += 1
    if seen != set(foundation):
        raise ValueError('foundation train and reader population are not exactly identical')
    if seen & continuation:
        raise ValueError('reader population spills into continuation domain')
    result = {part: {s: counts.get((part, s), 0) for s in SOURCES} for part in PARTITIONS}
    return result, foundation


def check_context(context: list[dict], cross: dict, *, fit_cell_counts: dict) -> dict:
    """Context totals for non-fit donors remain an ARCHIVED SUMMARY, not raw proof."""
    nonzero = {(part, source): n for part, values in cross.items()
               for source, n in values.items() if n}
    if len(context) != len(nonzero):
        raise ValueError('archived 149-donor context row cardinality mismatch')
    archived_cells = {}
    for row in context:
        k = (row.get('partition'), row.get('source'))
        if k not in nonzero or k in archived_cells:
            raise ValueError('archived context unexpected/duplicate partition-source row')
        if _natural(row.get('donor_count'), 'context donor count') != nonzero[k]:
            raise ValueError('archived context donor count disagrees with independent join')
        ncell = _natural(row.get('cell_count'), 'context cell count')
        if k[0] == 'reader_fit' and ncell != fit_cell_counts[k[1]]:
            raise ValueError('fit cell counts disagree with independent fit metadata')
        archived_cells[k] = ncell
    if set(archived_cells) != set(nonzero):
        raise ValueError('archived context partition-source completeness mismatch')
    return {part: {source: archived_cells.get((part, source), 0) for source in SOURCES}
            for part in PARTITIONS}


def structural_check(reader: list[dict], registry: list[dict],
                     context: list[dict], fit_metadata: list[dict]) -> dict:
    if len(reader) != 149 or len(registry) != 215 or len(fit_metadata) != 104:
        raise ValueError('frozen population row geometry mismatch')
    cross, source_by_donor = derive_reader_sources(reader, registry)
    if {part: sum(v.values()) for part, v in cross.items()} != EXPECTED_READER_COUNTS:
        raise ValueError('frozen reader partition totals changed')
    if sum(map(sum, (v.values() for v in cross.values()))) != 149:
        raise ValueError('reader source cross-tab incomplete')
    fit_ids = {r['donor_id'] for r in reader if r['reader_partition'] == 'reader_fit'}
    fit_count = Counter()
    used = set()
    for row in fit_metadata:
        donor = row.get('donor_id')
        if donor not in fit_ids or donor in used:
            raise ValueError('fit-only donor metadata is not exact reader_fit roster')
        used.add(donor)
        fit_count[source_by_donor[donor]] += _natural(row.get('cell_count'), 'fit cell count')
        _natural(row.get('original_t1_cells'), 'historical cell count', positive=False)
    if used != fit_ids or sum(fit_count.values()) != EXPECTED_CELLS_FIT:
        raise ValueError('fit donor roster/cell total changed')
    archived_cells = check_context(context, cross, fit_cell_counts=fit_count)
    groups = Counter((r['split_domain'], r['split']) for r in registry)
    required = {
        ('foundation', 'train'): 149, ('continuation', 'train'): 17,
        ('foundation', 'development'): 19, ('continuation', 'development'): 5,
        ('foundation', 'sealed_holdout'): 19, ('continuation', 'sealed_holdout'): 5,
        ('whole_study_external_holdout', 'whole_study_external_holdout'): 1,
    }
    if groups != required:
        raise ValueError('original foundation/continuation/external split geometry changed')
    return {
        'reader_source_crosstab': cross,
        'reader_partition_totals': {p: sum(cross[p].values()) for p in PARTITIONS},
        'reported_reader_validation_source_counts_verified': cross['reader_validation'] == REPORTED_VALIDATION_COUNTS,
        'reported_reader_validation_source_counts': REPORTED_VALIDATION_COUNTS,
        'reader_oracle_NPH52_donors': cross['reader_oracle']['NPH52'],
        'fit_cell_counts_independently_derived': {s: fit_count[s] for s in SOURCES},
        'fit_cell_count_total': sum(fit_count.values()),
        'archived_context_cell_counts': archived_cells,
        'archived_nonfit_cell_count_status': 'AGGREGATED_ARCHIVED_CONTEXT_ONLY_NOT_PER_DONOR_REDERIVED',
        'foundation_split_geometry': {f'{k[0]}:{k[1]}': v for k, v in sorted(groups.items())},
        'all_reader_donors_equal_exact_foundation_domain_train': True,
        'reader_continuation_overlap_count': 0,
        'reader_protected_outcomes_opened': False,
    }


def verify_archive(path: Path) -> dict:
    """Hash and read members through the SAME descriptor. No metadata DB opened."""
    with path.open('rb') as handle:
        if _sha_stream(handle) != ARCHIVE_SHA256:
            raise ValueError('August24 archive whole-file SHA-256 mismatch')
        handle.seek(0)
        with zipfile.ZipFile(handle) as z:
            names = z.namelist()
            if len(names) != len(set(names)):
                raise ValueError('archive duplicate ZIP member')
            parsed = {}
            for key, (rel, expected, header) in MEMBERS.items():
                name = BASE + rel
                if names.count(name) != 1 or z.getinfo(name).file_size > 1_000_000:
                    raise ValueError('missing/oversized/ambiguous frozen metadata member: ' + key)
                raw = z.read(name)
                if hashlib.sha256(raw).hexdigest() != expected:
                    raise ValueError('frozen CSV byte SHA-256 mismatch: ' + key)
                parsed[key] = _csv(raw, header, key)
    result = structural_check(parsed['reader'], parsed['foundation'],
                              parsed['context'], parsed['fit_metadata'])
    return {
        'schema': 'JEPA_V26_INDEPENDENT_READER_SOURCE_CROSSTAB_V1',
        'status': 'PASS_FROZEN_READER_SOURCE_METADATA_CROSSCHECK',
        'scope': 'FROZEN_METADATA_ONLY_NO_RESERVED_OUTCOME_ACCESS',
        'archive_sha256': ARCHIVE_SHA256,
        'verified_exact_member_shas': {k: v[1] for k, v in MEMBERS.items()},
        'metadata_csv_members_opened': 4,
        'sqlite_db_opened': False,
        'expression_files_opened': False,
        'level4_blocks_opened': 0,
        'fit_sampler_authorized': False,
        'training_authorized': False,
        'reader_validation_outcomes_accessed': False,
        'reader_oracle_outcomes_accessed': False,
        'foundation_development_or_sealed_outcomes_accessed': False,
        'external_Siletti_outcomes_accessed': False,
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calibration-zip', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or not args.out.parent.is_dir():
        raise ValueError('use a NEW filename inside an existing output parent; no overwrite')
    result = verify_archive(args.calibration_zip)
    with args.out.open('x', encoding='utf8') as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')
    print(json.dumps({'status': result['status'], 'reader_source_crosstab': result['reader_source_crosstab'],
                      'archive_sha256': result['archive_sha256']}, sort_keys=True))


if __name__ == '__main__':
    main()
