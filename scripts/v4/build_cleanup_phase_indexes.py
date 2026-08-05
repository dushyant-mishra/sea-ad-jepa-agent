#!/usr/bin/env python3
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

STAGE_RE = re.compile(r'stage[_-]?([0-9]+[a-zA-Z]*|c)', re.I)
PATH_RE = re.compile(r'(?:(?:configs|results|data|docs|scripts|web|archive)/[^\s\"\'<>),]+)')


def run_git(args: list[str], project: Path) -> str:
    return subprocess.check_output(['git', *args], cwd=project, text=True, stderr=subprocess.DEVNULL).strip()


def tracked_files(project: Path) -> list[str]:
    out = run_git(['ls-files'], project)
    return [line.strip() for line in out.splitlines() if line.strip()]


def stage_hint(path: str) -> str:
    match = STAGE_RE.search(path)
    if match:
        return 'stage' + match.group(1).lower()
    if '/v4/' in path.replace('\\', '/') or path.replace('\\', '/').startswith(('configs/v4/', 'docs/v4/', 'scripts/v4/')):
        return 'v4'
    return ''


def version_bucket(path: str) -> str:
    normalized = path.replace('\\', '/')
    if normalized.startswith(('configs/v4/', 'docs/v4/', 'scripts/v4/')) or re.search(r'stage8[0-9]|stage80|stage81|stage82|stage83|stage84|stage85', normalized, re.I):
        return 'v4'
    if re.search(r'stage_c|stage[2-7][0-9]|stage7[0-9]|stage75|stage76|stage77|stage78|stage79|v3|ACTIVE_V3|V3_', normalized, re.I):
        return 'v3'
    if re.search(r'(^|/)(v2_|.*_v2\.|.*_v2_|v2_)', normalized, re.I):
        return 'v2'
    if re.search(r'(^|/)(v1_|.*_v1\.|.*_v1_|v1_)', normalized, re.I):
        return 'v1'
    return 'unclassified'


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def text_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:
            return ''


def doc_config_role(path: str) -> str:
    normalized = path.replace('\\', '/')
    if normalized.startswith('configs/v4/'):
        return 'active_v4_config'
    if normalized.startswith('docs/v4/'):
        return 'active_v4_doc'
    if normalized.startswith('configs/agent/'):
        return 'stage_agent_config'
    if normalized.startswith('configs/train/'):
        return 'training_config'
    if normalized.startswith('configs/data/'):
        return 'data_config'
    if normalized.startswith('configs/'):
        return 'pipeline_config'
    if normalized.startswith('docs/stage'):
        return 'stage_doc'
    if normalized.startswith('docs/'):
        return 'project_doc'
    return 'other'


def path_policy(path: str) -> str:
    bucket = version_bucket(path)
    normalized = path.replace('\\', '/')
    if bucket == 'v4':
        return 'active_v4_namespace'
    if bucket == 'v3' or normalized.startswith(('results/', 'scripts/', 'configs/')):
        return 'path_stable_or_wrapper_required'
    if normalized.startswith('docs/'):
        return 'move_only_after_reference_audit'
    return 'review_before_move'


def linked_path_count(project: Path, rel: str, all_text: dict[str, str]) -> int:
    needle = rel.replace('\\', '/')
    return sum(1 for path, text in all_text.items() if path != rel and needle in text)


def extract_python_script_info(path: Path) -> tuple[list[str], list[str], list[str]]:
    text = text_or_empty(path)
    imports: set[str] = set()
    local_paths: set[str] = set(PATH_RE.findall(text.replace('\\', '/')))
    outputs: set[str] = set(re.findall(r'(?:results|outputs|runs|logs|checkpoints)/[^\s\"\'<>),]+', text.replace('\\', '/')))
    if path.suffix == '.py':
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split('.')[0])
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    normalized = node.value.replace('\\', '/')
                    if any(token in normalized for token in ('configs/', 'results/', 'data/', 'scripts/', 'docs/')):
                        local_paths.update(PATH_RE.findall(normalized))
        except SyntaxError:
            imports.add('SYNTAX_UNPARSED')
    return sorted(imports), sorted(local_paths), sorted(outputs)


def script_status(path: str) -> str:
    normalized = path.replace('\\', '/')
    bucket = version_bucket(path)
    if normalized.startswith('scripts/v4/'):
        return 'active_v4_tooling'
    if bucket == 'v3' and re.search(r'stage7[5-9]|stage75|stage76|stage77|stage78|stage79', normalized, re.I):
        return 'frozen_v3_pipeline'
    if normalized.startswith('scripts/run_'):
        return 'runner_or_entrypoint'
    if bucket in {'v1', 'v2'}:
        return 'legacy_reference'
    return 'review_before_move'


def result_role(path: str) -> str:
    normalized = path.replace('\\', '/')
    if normalized.startswith('results/visualization/'):
        return 'visualization_artifact'
    if normalized.startswith('results/tables/'):
        return 'table'
    if normalized.startswith('results/reports/'):
        return 'report'
    if normalized.startswith('results/figures/'):
        return 'figure'
    return 'result_artifact'


def main() -> int:
    project = Path.cwd()
    files = tracked_files(project)
    text_cache: dict[str, str] = {}
    for rel in files:
        if rel.startswith(('docs/', 'configs/')) and (project / rel).is_file():
            text_cache[rel] = text_or_empty(project / rel)

    doc_rows: list[dict[str, Any]] = []
    for rel in files:
        if not rel.startswith(('docs/', 'configs/')):
            continue
        p = project / rel
        text = text_or_empty(p)
        doc_rows.append({
            'path': rel,
            'version_bucket': version_bucket(rel),
            'stage_hint': stage_hint(rel),
            'role': doc_config_role(rel),
            'byte_size': p.stat().st_size if p.exists() else '',
            'referenced_by_tracked_doc_or_config_count': linked_path_count(project, rel, text_cache),
            'physical_move_recommended_now': 'false',
            'path_policy': path_policy(rel),
            'notes': 'phase3_index_only',
        })

    script_rows: list[dict[str, Any]] = []
    for rel in files:
        normalized = rel.replace('\\', '/')
        if not normalized.startswith('scripts/') or normalized.startswith('scripts/__pycache__/'):
            continue
        p = project / rel
        imports, local_paths, outputs = extract_python_script_info(p)
        script_rows.append({
            'path': rel,
            'version_bucket': version_bucket(rel),
            'stage_hint': stage_hint(rel),
            'script_status': script_status(rel),
            'suffix': p.suffix,
            'byte_size': p.stat().st_size if p.exists() else '',
            'n_imports_or_modules': len(imports),
            'imports_or_modules': '|'.join(imports[:60]),
            'n_local_path_mentions': len(local_paths),
            'local_path_mentions': '|'.join(local_paths[:80]),
            'n_output_path_mentions': len(outputs),
            'output_path_mentions': '|'.join(outputs[:80]),
            'physical_move_recommended_now': 'false',
            'path_policy': path_policy(rel),
        })

    result_rows: list[dict[str, Any]] = []
    for rel in files:
        normalized = rel.replace('\\', '/')
        if not normalized.startswith('results/'):
            continue
        p = project / rel
        bucket = version_bucket(rel)
        result_rows.append({
            'path': rel,
            'version_bucket': bucket,
            'stage_hint': stage_hint(rel),
            'artifact_role': result_role(rel),
            'byte_size': p.stat().st_size if p.exists() else '',
            'sha256': sha256_file(p) if p.exists() and p.is_file() else '',
            'freeze_status': 'frozen_path_stable' if bucket == 'v3' else 'tracked_reference_or_review',
            'physical_move_recommended_now': 'false',
            'notes': 'phase5_index_only_results_last',
        })

    outputs = {
        'doc_config_index': project / 'results/tables/project_doc_config_index_v1.csv',
        'script_inventory': project / 'results/tables/project_script_dependency_inventory_v1.csv',
        'frozen_results_index': project / 'results/tables/project_frozen_results_index_v1.csv',
        'summary': project / 'results/reports/project_cleanup_phase3_5_summary_v1.json',
    }
    for p in outputs.values():
        p.parent.mkdir(parents=True, exist_ok=True)

    def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(outputs['doc_config_index'], doc_rows)
    write_csv(outputs['script_inventory'], script_rows)
    write_csv(outputs['frozen_results_index'], result_rows)

    def counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in rows:
            value = str(row[key])
            out[value] = out.get(value, 0) + 1
        return dict(sorted(out.items()))

    summary = {
        'stage': 'project_cleanup_phase3_5_indexes_v1',
        'purpose': 'non-destructive organization indexes for v4 migration',
        'phases': {
            'phase3_docs_configs': 'indexed_only_no_moves',
            'phase4_scripts': 'dependency_inventory_only_no_moves',
            'phase5_results': 'frozen_result_hash_index_only_no_moves',
        },
        'n_doc_config_rows': len(doc_rows),
        'n_script_rows': len(script_rows),
        'n_result_rows': len(result_rows),
        'doc_config_version_counts': counts(doc_rows, 'version_bucket'),
        'script_status_counts': counts(script_rows, 'script_status'),
        'result_version_counts': counts(result_rows, 'version_bucket'),
        'outputs': {key: str(path.relative_to(project)).replace('\\', '/') for key, path in outputs.items()},
        'cleanup_boundary': {
            'physical_moves_performed': False,
            'raw_data_committed': False,
            'frozen_v3_paths_preserved': True,
            'v4_namespaces_preferred_for_new_work': True,
        },
    }
    outputs['summary'].write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    for name, path in outputs.items():
        print(f'Wrote {name}: {path}')
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())