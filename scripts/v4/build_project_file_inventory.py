#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

VERSION_RULES = [
    # Project stage markers are checked before file-format suffixes such as _v1.
    (re.compile(r'(^|/)v4/|stage8[0-9]|stage80|stage81|stage82|stage83|stage84|stage85', re.I), 'v4'),
    (re.compile(r'(stage_c|stage[2-7][0-9]|stage7[0-9]|stage75|stage76|stage77|stage78|stage79|v3|ACTIVE_V3|V3_)', re.I), 'v3'),
    (re.compile(r'(^|/)(v2_|.*_v2\.|.*_v2_|v2_)', re.I), 'v2'),
    (re.compile(r'(^|/)(v1_|.*_v1\.|.*_v1_|v1_)', re.I), 'v1'),
]

ROLE_RULES = [
    ('configs/', 'config'),
    ('scripts/', 'script'),
    ('docs/', 'doc'),
    ('tests/', 'test'),
    ('results/tables/', 'result_table'),
    ('results/reports/', 'result_report'),
    ('results/figures/', 'result_figure'),
    ('results/visualization/', 'visualization'),
    ('web/', 'web'),
    ('docker/', 'docker'),
    ('src/', 'source'),
]

STATUS_BY_VERSION = {
    'v1': 'legacy_reference',
    'v2': 'legacy_reference',
    'v3': 'frozen_or_current_provenance',
    'v4': 'active_planning',
    'unclassified': 'needs_review',
}


def git_files(project: Path) -> list[str]:
    out = subprocess.check_output(['git', 'ls-files'], cwd=project, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def classify_version(path: str) -> str:
    normalized = path.replace('\\', '/')
    if normalized.startswith(('configs/v4/', 'docs/v4/', 'scripts/v4/')):
        return 'v4'
    for pattern, version in VERSION_RULES:
        if pattern.search(normalized):
            return version
    return 'unclassified'


def classify_stage(path: str) -> str:
    match = re.search(r'stage[_-]?([0-9]+[a-zA-Z]*|c)', path, re.I)
    if match:
        return 'stage' + match.group(1).lower()
    match = re.search(r'(^|/)(v[0-9])[_/-]', path, re.I)
    if match:
        return match.group(2).lower()
    return ''


def classify_role(path: str) -> str:
    normalized = path.replace('\\', '/')
    for prefix, role in ROLE_RULES:
        if normalized.startswith(prefix):
            return role
    return 'project_file'


def main() -> int:
    project = Path.cwd()
    rows = []
    for rel in sorted(git_files(project)):
        p = project / rel
        version = classify_version(rel)
        rows.append({
            'path': rel,
            'version_bucket': version,
            'stage_hint': classify_stage(rel),
            'role': classify_role(rel),
            'archive_status': STATUS_BY_VERSION[version],
            'byte_size': p.stat().st_size if p.exists() else '',
            'physical_move_recommended_now': 'false',
            'move_risk': 'high' if rel.startswith(('scripts/', 'results/', 'configs/')) and version == 'v3' else 'low',
            'notes': 'mapped_only_paths_preserved',
        })
    out = project / 'results/tables/project_file_inventory_v1.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    counts = {}
    for row in rows:
        counts[row['version_bucket']] = counts.get(row['version_bucket'], 0) + 1
    print(f'Wrote: {out}')
    print(counts)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
