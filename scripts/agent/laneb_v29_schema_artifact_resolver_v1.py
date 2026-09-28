"""Lane B V29: resolve committed artifacts for each closure root BY SCHEMA ROLE.

Filename is not identity. This resolver never matches on a path or a file name.
For every authority dataclass under ``src/sea_ad_jepa/v5`` it extracts the exact
``schema`` string literal that the class stamps into its own ``canonical_digest``
payload, then searches committed JSON blobs at the given git revision for that
schema value. A candidate artifact is one whose ``schema`` field equals the
class's own schema literal.

A resolved candidate is a CANDIDATE, never a validated root. Producing zero
candidates is reported as NO_COMMITTED_ARTIFACT_FOUND, which is a failure to
find, never "0 defects".
"""
from __future__ import annotations

import ast
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
V5 = ROOT / "src" / "sea_ad_jepa" / "v5"


def _class_schema_map():
    """class name -> {schema, module} for every v5 class stamping a schema."""
    out = {}
    for path in sorted(V5.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        module = "sea_ad_jepa.v5." + path.stem
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            schema = None
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Dict):
                    continue
                for key, val in zip(sub.keys, sub.values):
                    is_schema_key = isinstance(key, ast.Constant) and key.value == "schema"
                    if is_schema_key and isinstance(val, ast.Constant):
                        schema = val.value
            fields = []
            for sub in node.body:
                if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                    fields.append(sub.target.id)
            out[node.name] = {
                "schema": schema,
                "module": module,
                "source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "fields": fields,
            }
    return out


def _git(args, rev_cwd=ROOT):
    proc = subprocess.run(
        ["git"] + args,
        cwd=str(rev_cwd),
        capture_output=True,
        text=True,
    )
    return proc.stdout


def _committed_json_paths(rev):
    raw = _git(["ls-tree", "-r", "--name-only", rev])
    return [p for p in raw.splitlines() if p.endswith(".json")]


def _load_blob(rev, path):
    proc = subprocess.run(
        ["git", "show", rev + ":" + path],
        cwd=str(ROOT),
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except Exception:
        return None


def build_index(rev):
    """schema string -> [ {path, blob_sha256_fields...} ] over all committed JSON."""
    paths = _committed_json_paths(rev)
    index = {}
    scanned = 0
    for path in paths:
        obj = _load_blob(rev, path)
        scanned += 1
        if not isinstance(obj, dict):
            continue
        schema = obj.get("schema")
        if not isinstance(schema, str):
            continue
        index.setdefault(schema, []).append({"path": path, "payload": obj})
    return index, scanned


def main():
    rev = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
    classes = _class_schema_map()
    index, scanned = build_index(rev)

    report = {
        "schema": "JEPA_LANEB_V29_SCHEMA_ARTIFACT_INDEX_V1",
        "revision": _git(["rev-parse", rev]).strip(),
        "committed_json_blobs_scanned": scanned,
        "distinct_schema_values_found": len(index),
        "classes_with_schema_literal": sum(
            1 for v in classes.values() if v["schema"]
        ),
        "class_to_candidates": {},
        "schema_to_paths": dict(
            (k, [e["path"] for e in v]) for k, v in sorted(index.items())
        ),
    }
    for name, meta in sorted(classes.items()):
        schema = meta["schema"]
        if not schema:
            continue
        hits = index.get(schema, [])
        report["class_to_candidates"][name] = {
            "schema": schema,
            "defining_module": meta["module"],
            "defining_source_file": meta["source_file"],
            "declared_fields": meta["fields"],
            "candidate_count": len(hits),
            "candidate_paths": [h["path"] for h in hits],
            "outcome": "CANDIDATE_FOUND" if hits else "NO_COMMITTED_ARTIFACT_FOUND",
        }

    text = json.dumps(report, indent=2)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print("wrote " + str(out_path))
        print("scanned %d committed JSON blobs" % scanned)
        print("distinct schema values %d" % len(index))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
