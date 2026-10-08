#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


def run_git(args: list[str], project: Path) -> str:
    return subprocess.check_output(['git', *args], cwd=project, text=True, stderr=subprocess.DEVNULL).strip()


def git_files(project: Path) -> list[str]:
    out = run_git(['ls-files'], project)
    return [line.strip() for line in out.splitlines() if line.strip()]


def github_file_url(remote_url: str, commit: str, relpath: str) -> str:
    if remote_url.endswith('.git'):
        remote_url = remote_url[:-4]
    if remote_url.startswith('git@github.com:'):
        remote_url = 'https://github.com/' + remote_url.removeprefix('git@github.com:')
    return f'{remote_url}/blob/{commit}/{relpath}'


def classify_anchor(path: str) -> str:
    normalized = path.replace('\\', '/')
    if normalized.startswith(('results/tables/stage75', 'results/tables/stage76', 'results/tables/stage77', 'results/tables/stage78', 'results/tables/stage79')):
        return 'v3_frozen_table'
    if normalized.startswith(('results/reports/stage75', 'results/reports/stage76', 'results/reports/stage77', 'results/reports/stage78', 'results/reports/stage79')):
        return 'v3_frozen_report'
    if normalized.startswith('results/visualization/stage'):
        return 'v3_frozen_visualization'
    if normalized.startswith(('configs/v4/', 'docs/v4/', 'scripts/v4/')):
        return 'v4_launchpad'
    if normalized.startswith('archive/'):
        return 'archive_placeholder'
    if normalized.startswith(('data/', 'checkpoints/', 'runs/', 'logs/', 'outputs/')):
        return 'large_or_local_data_guarded'
    return 'tracked_project_file'


def latest_commit_by_file(project: Path, tracked: set[str]) -> dict[str, dict[str, str]]:
    raw = run_git(['log', '--name-only', '--format=@@@%H%x09%h%x09%cs%x09%s', '--'], project)
    latest: dict[str, dict[str, str]] = {}
    current = {'commit': '', 'short_commit': '', 'commit_date': '', 'subject': ''}

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('@@@'):
            parts = line[3:].split('\t', 3)
            while len(parts) < 4:
                parts.append('')
            current = {
                'commit': parts[0],
                'short_commit': parts[1],
                'commit_date': parts[2],
                'subject': parts[3],
            }
            continue
        if line in tracked and line not in latest:
            latest[line] = current.copy()
        if len(latest) == len(tracked):
            break

    return latest


def main() -> int:
    project = Path.cwd()
    head = run_git(['rev-parse', 'HEAD'], project)
    branch = run_git(['branch', '--show-current'], project)
    remote_url = run_git(['remote', 'get-url', 'origin'], project)
    origin_head = run_git(['rev-parse', 'origin/main'], project)
    remote_in_sync = head == origin_head

    files = sorted(git_files(project))
    tracked = set(files)
    latest = latest_commit_by_file(project, tracked)

    rows = []
    for relpath in files:
        commit_info = latest.get(relpath, {'commit': '', 'short_commit': '', 'commit_date': '', 'subject': ''})
        rows.append({
            'path': relpath,
            'anchor_class': classify_anchor(relpath),
            'last_commit': commit_info['commit'],
            'last_short_commit': commit_info['short_commit'],
            'last_commit_date': commit_info['commit_date'],
            'last_commit_subject': commit_info['subject'],
            'github_blob_url': github_file_url(remote_url, commit_info['commit'], relpath) if commit_info['commit'] else '',
            'path_move_policy': 'preserve_path_unless_reference_audited',
        })

    out_csv = project / 'results/tables/project_git_provenance_index_v1.csv'
    out_json = project / 'results/reports/project_git_provenance_summary_v1.json'
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = {}
    missing_latest = 0
    for row in rows:
        counts[row['anchor_class']] = counts.get(row['anchor_class'], 0) + 1
        if not row['last_commit']:
            missing_latest += 1

    summary = {
        'stage': 'project_git_provenance_index_v1',
        'purpose': 'cleanup provenance map for v4 migration; no file moves performed',
        'repository_remote': remote_url,
        'branch': branch,
        'head_commit': head,
        'origin_main_commit': origin_head,
        'head_matches_origin_main': remote_in_sync,
        'n_tracked_files': len(rows),
        'n_files_missing_latest_commit': missing_latest,
        'anchor_class_counts': dict(sorted(counts.items())),
        'outputs': {
            'csv': 'results/tables/project_git_provenance_index_v1.csv',
            'summary_json': 'results/reports/project_git_provenance_summary_v1.json',
        },
        'cleanup_boundary': {
            'raw_data_committed': False,
            'physical_moves_performed': False,
            'protected_unrelated_files_staged': False,
        },
    }
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    print(f'Wrote: {out_csv}')
    print(f'Wrote: {out_json}')
    print(json.dumps({
        'n_tracked_files': len(rows),
        'head_matches_origin_main': remote_in_sync,
        'n_files_missing_latest_commit': missing_latest,
        'anchor_class_counts': summary['anchor_class_counts'],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())