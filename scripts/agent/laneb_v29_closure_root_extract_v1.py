"""Lane B V29: extract the exact V5 closure-V2 authority-root graph from source.

Read-only. Parses ``src/sea_ad_jepa/v5/current_authority_closure_v2.py`` with the
``ast`` module and reports, per root:

* the closure parameter that supplies it,
* whether that parameter is isinstance-enforced, duck-typed, or a raw str,
* the defining class and module,
* every equality binding the closure enforces on the derived local.

This replaces eyeballing the source. It opens no data and computes nothing
scientific; it only describes the contract that already exists in committed code.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "src" / "sea_ad_jepa" / "v5" / "current_authority_closure_v2.py"
ROOTS_MOD = ROOT / "src" / "sea_ad_jepa" / "v5" / "current_authority_roots_v2.py"


def _load(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _root_vocabulary():
    tree = _load(ROOTS_MOD)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if isinstance(node.value, ast.Tuple):
                vals = []
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant):
                        vals.append(elt.value)
                    elif isinstance(elt, ast.Starred) and isinstance(elt.value, ast.Name):
                        vals.extend(out.get(elt.value.id, []))
                out[name] = vals
    return (
        out["CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2"],
        out["CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V2"],
    )


def _imports(tree):
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                out[alias.asname or alias.name] = "sea_ad_jepa.v5." + node.module
    return out


def _closure_fn(tree):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name == "validate_current_v5_authority_closure_v2":
                return node
    raise SystemExit("closure function not found")


def _params(fn):
    out = {}
    for arg in fn.args.kwonlyargs:
        out[arg.arg] = ast.unparse(arg.annotation) if arg.annotation else "<none>"
    return out


def _typed_enforced(fn):
    """param -> class actually passed to the isinstance loop."""
    out = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.targets[0], ast.Name) or node.targets[0].id != "typed":
            continue
        if isinstance(node.value, ast.Tuple):
            for elt in node.value.elts:
                if isinstance(elt, ast.Tuple) and len(elt.elts) == 3:
                    value, cls, _field = elt.elts
                    if isinstance(value, ast.Name) and isinstance(cls, ast.Name):
                        out[value.id] = cls.id
    return out


def _local_sources(fn):
    """local var -> {kind: _auth|_sha, param: <param name>}"""
    out = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        if not isinstance(node.targets[0], ast.Name):
            continue
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            if value.func.id in ("_auth", "_sha") and value.args:
                if isinstance(value.args[0], ast.Name):
                    out[node.targets[0].id] = {
                        "kind": value.func.id,
                        "param": value.args[0].id,
                    }
    return out


def _roots_map(fn):
    """root name -> local var."""
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.targets[0], ast.Name) or node.targets[0].id != "roots":
            continue
        if isinstance(node.value, ast.Dict):
            out = {}
            for key, val in zip(node.value.keys, node.value.values):
                if isinstance(key, ast.Constant) and isinstance(val, ast.Name):
                    out[key.value] = val.id
            return out
    raise SystemExit("roots dict not found")


def _describe_operand(node):
    if isinstance(node, ast.Name):
        return {"form": "local", "local": node.id}
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return {
            "form": "attribute",
            "object": node.value.id,
            "attribute": node.attr,
            "access": "direct",
        }
    is_getattr = (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[0], ast.Name)
        and isinstance(node.args[1], ast.Constant)
    )
    if is_getattr:
        return {
            "form": "attribute",
            "object": node.args[0].id,
            "attribute": node.args[1].value,
            "access": "getattr_default_none",
        }
    return {"form": "other", "src": ast.unparse(node)}


def _eq_calls(fn):
    out = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "_eq" or len(node.args) != 3:
            continue
        third = node.args[2]
        msg = third.value if isinstance(third, ast.Constant) else ast.unparse(third)
        out.append(
            {
                "line": node.lineno,
                "actual": _describe_operand(node.args[0]),
                "expected": _describe_operand(node.args[1]),
                "message": msg,
            }
        )
    return sorted(out, key=lambda r: r["line"])


def _attr_reads(fn, params):
    """param -> sorted list of every attribute the closure reads off it."""
    out = {p: set() for p in params}
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in out:
                out[node.value.id].add(node.attr)
        is_getattr = (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in out
            and isinstance(node.args[1], ast.Constant)
        )
        if is_getattr:
            out[node.args[0].id].add(node.args[1].value)
    return dict((k, sorted(v)) for k, v in out.items())


def build_report():
    tree = _load(CLOSURE)
    fn = _closure_fn(tree)
    upstream, receipt = _root_vocabulary()
    params = _params(fn)
    typed = _typed_enforced(fn)
    local_sources = _local_sources(fn)
    roots = _roots_map(fn)
    eqs = _eq_calls(fn)
    reads = _attr_reads(fn, params)
    imports = _imports(tree)

    rows = []
    for root in upstream:
        local = roots.get(root)
        src = local_sources.get(local, {})
        param = src.get("param")
        ann = params.get(param, "<unmapped>") if param else "<unmapped>"
        enforced_cls = typed.get(param)
        if src.get("kind") == "_sha":
            kind = "RAW_STR_CROSS_BINDING_CONSTANT"
        elif enforced_cls:
            kind = "ISINSTANCE_ENFORCED"
        else:
            kind = "DUCK_TYPED_NO_CLASS_CHECK"
        bindings = []
        for e in eqs:
            if e["expected"].get("local") == local and e["actual"]["form"] == "attribute":
                bindings.append(
                    {
                        "consumer_param": e["actual"].get("object"),
                        "consumer_attribute": e["actual"].get("attribute"),
                        "access": e["actual"].get("access"),
                        "line": e["line"],
                        "message": e["message"],
                    }
                )
        rows.append(
            {
                "root": root,
                "closure_local": local,
                "closure_parameter": param,
                "parameter_annotation": ann,
                "enforcement": kind,
                "isinstance_class": enforced_cls,
                "defining_module": imports.get(enforced_cls) if enforced_cls else None,
                "attributes_read_by_closure": reads.get(param, []) if param else [],
                "downstream_equality_bindings": bindings,
                "downstream_equality_binding_count": len(bindings),
            }
        )

    census = {
        "isinstance_enforced": sum(
            1 for r in rows if r["enforcement"] == "ISINSTANCE_ENFORCED"
        ),
        "duck_typed_no_class_check": sum(
            1 for r in rows if r["enforcement"] == "DUCK_TYPED_NO_CLASS_CHECK"
        ),
        "raw_str_cross_binding_constant": sum(
            1 for r in rows if r["enforcement"] == "RAW_STR_CROSS_BINDING_CONSTANT"
        ),
    }
    return {
        "schema": "JEPA_LANEB_V29_CLOSURE_ROOT_GRAPH_V1",
        "source_file": str(CLOSURE.relative_to(ROOT)).replace("\\", "/"),
        "upstream_root_count": len(upstream),
        "receipt_root_count": len(receipt),
        "receipt_only_roots": [r for r in receipt if r not in upstream],
        "enforcement_census": census,
        "total_equality_assertions": len(eqs),
        "roots": rows,
    }


def main():
    report = build_report()
    text = json.dumps(report, indent=2)
    if len(sys.argv) > 1:
        out = pathlib.Path(sys.argv[1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print("wrote " + str(out))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
