"""Mutation self-audit of Macha #514/#515 review tests, in scratch mirrors only.

usage: python macha_514_515_mutation_audit.py <worktree> <test file rel> <target rel> <out json>
Not collected by pytest. Mirrors scripts/v5/td_unified and one test file into a
temporary directory, so no implementation file in any worktree is modified.
Each mutant is a (name, old, new) text substitution on the target module. A
mutant must make at least one test fail ("killed"); the "repair" mutant is the
suggested fix and must make every RED test pass with no other test failing.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

worktree, test_rel, target_rel, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]

V2C = [
    ("d1_check_removed", "            depth.get(cid)!=base_sum.get(cid,0) or\n", ""),
    ("roster_not_committed", '"complete_policy_sha256":_sha(policy),',
     '"complete_policy_sha256":_sha({k:v for k,v in policy.items() if k!="cell_roster"}),'),
    ("module_cache_added", "def _deny(message):", "_CACHE={}\n\ndef _deny(message):"),
    ("file_read_in_validate", "    view=_snap(student_view)\n",
     "    open(__file__,'rb').close()\n    view=_snap(student_view)\n"),
    ("snapshot_skips_type_check", '    _deny("V2C refuses non-exact JSON evidence")', "    return x"),
    ("query_count_allowed", "            if s!=expected_state or n is not None or d is not None:",
     "            if s not in (expected_state,_MS):"),
    ("repair", "    if type(student_view) is not dict or type(dict.get(student_view,\"view_kind\")) is not str or dict.get(student_view,\"view_kind\")!=_STUDENT:\n        _deny(\"V2C accepts STUDENT_BASE_RIGHTS only\")\n    view=_snap(student_view)\n",
     "    if type(student_view) is not dict or any(type(k) is not str for k in dict.keys(student_view)):\n        _deny(\"V2C accepts STUDENT_BASE_RIGHTS only\")\n    role=dict.get(student_view,\"view_kind\")\n    if type(role) is not str or role!=_STUDENT:\n        _deny(\"V2C accepts STUDENT_BASE_RIGHTS only\")\n    view=_snap(student_view)\n    if view[\"view_kind\"]!=_STUDENT:\n        _deny(\"V2C accepts STUDENT_BASE_RIGHTS only\")\n"),
]
PRODUCER = [
    ("depth_plus_one", "        depth=sum(counts.values())\n", "        depth=sum(counts.values())+0\n        depth=depth+1 if depth else depth\n"),
    ("legacy_import_added", "from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C\n",
     "from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C\n"
     "from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as _legacy\n"),
    ("query_count_accepted", "            if (addr not in rights or rights[addr] not in base_set or\n                    phys[addr]!=MS):",
     "            if (addr not in rights):"),
    ("injected_value_in_refusal", '                _reject("D1 base input contains non-base or unmeasured count")',
     '                _reject("D1 base input contains non-base or unmeasured count %d" % (count if type(count) is int else -1))'),
    ("structural_shown_as_zero", "                state,value,d=physical_state,None,None",
     "                state,value,d=(MS,0,depth) if physical_state==SU and rights[addr] in base_set else (physical_state,None,None)"),
    ("extra_observation_key_allowed", '_OBS_KEYS=frozenset(("cell_id","base_counts"))',
     '_OBS_KEYS=frozenset(("cell_id","base_counts"))\n_ANY_EXTRA=True'),
]
mutants = V2C if target_rel.endswith("student_gate_v1.py") else PRODUCER

results = {}
for name, old, new in [("baseline", "", "")] + mutants:
    with tempfile.TemporaryDirectory() as td:
        mirror = Path(td)
        shutil.copytree(worktree / "scripts" / "v5" / "td_unified", mirror / "scripts" / "v5" / "td_unified")
        (mirror / "tests" / "v5" / "td_unified").mkdir(parents=True)
        shutil.copy(worktree / test_rel, mirror / test_rel)
        target = mirror / target_rel
        text = target.read_text(encoding="utf8")
        if name != "baseline":
            if old not in text:
                results[name] = "MUTANT_DID_NOT_APPLY"
                continue
            text = text.replace(old, new, 1)
            if name == "extra_observation_key_allowed":
                text = text.replace("if type(item) is not dict or set(item)!=_OBS_KEYS",
                                    "if type(item) is not dict or not _OBS_KEYS<=set(item)", 1)
            target.write_text(text, encoding="utf8")
        done = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf",
                               test_rel], cwd=mirror, capture_output=True, text=True)
        failed = sorted({line.split("::", 1)[1].split(" ")[0] for line in done.stdout.splitlines()
                         if line.startswith("FAILED ")})
        summary = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr[-300:]
        results[name] = {"summary": summary, "failed": failed}
Path(out).write_text(json.dumps(results, indent=1), encoding="utf8")
for k, v in results.items():
    print(k, "->", v if isinstance(v, str) else v["summary"])
    if isinstance(v, dict) and k != "baseline":
        print("    killed by:", [f for f in v["failed"]][:6])
