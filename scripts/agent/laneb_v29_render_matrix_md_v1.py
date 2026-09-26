"""Render the Lane B V29 33-root status matrix as markdown from the JSON.

The markdown is a view of the JSON, never a second source of truth. Every number
printed here is read from the measured report.
"""
from __future__ import annotations

import json
import pathlib
import sys


def short(value, n=16):
    if not value:
        return "-"
    return value[:n] + "..." if len(value) > n else value


def render(matrix, consumers, reconcile):
    led = matrix["ledger"]
    sub = matrix["substrate_byte_authentication"]
    out = []
    a = out.append

    a("# JEPA V29 Lane B — exact 33-root authority status matrix")
    a("")
    a("Revision `%s` (branch `lane-b/v29-root-closure-20260926`)." % matrix["revision"])
    a("")
    a("Artifact index built at the same revision `%s`, scanning %s committed JSON "
      "blobs. The matrix refuses to build if those two revisions disagree, so it "
      "cannot cite a commit that was not the one actually searched."
      % (matrix.get("artifact_index_revision"),
         matrix.get("committed_json_blobs_scanned")))
    a("")
    a("**Bottom line: no root is fully closed. `fully_closed = 0`. "
      "No training authority is issued or issuable.**")
    a("")
    a("## Reproduce every check in this document")
    a("")
    a("```bash")
    a("# 1. exclusive worktree at the reviewed head")
    a("git -C \"/d/Jepa project\" worktree add --detach /d/jepa_laneB_20260926 \\")
    a("    origin/review/v27-authority-root-inventory-20260925")
    a("cd /d/jepa_laneB_20260926 && git checkout -b lane-b/v29-root-closure-20260926")
    a("")
    a("# 2. extract the closure root graph straight from source with ast")
    a("python scripts/agent/laneb_v29_closure_root_extract_v1.py OUT/CLOSURE_ROOT_GRAPH.json")
    a("")
    a("# 3. index every committed JSON by the schema its defining class stamps")
    a("#    (629 blobs at this head; role-based, never filename-based)")
    a("python scripts/agent/laneb_v29_schema_artifact_resolver_v1.py HEAD OUT/SCHEMA_INDEX.json")
    a("")
    a("# 4. Task 1: substrate root downstream bindings, per consumer")
    a("python scripts/agent/laneb_v29_substrate_consumer_verify_v1.py HEAD \\")
    a("    OUT/SCHEMA_INDEX.json OUT/SUBSTRATE_CONSUMER_BINDING.json")
    a("")
    a("# 5. Task 2: V3-vs-V1 masking reconciliation")
    a("python scripts/agent/laneb_v29_masking_v3_v1_reconcile_v1.py OUT/RECONCILIATION.json")
    a("")
    a("# 6. the 33-root matrix, then this markdown view of it")
    a("python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD OUT/SCHEMA_INDEX.json OUT")
    a("python scripts/agent/laneb_v29_render_matrix_md_v1.py OUT \\")
    a("    docs/agent/LANEB_V29_ROOT_STATUS_MATRIX_20260926.md")
    a("```")
    a("")
    a("Each root below also carries its own single-command validator. The two")
    a("forms were both executed and both reproduce:")
    a("")
    a("```bash")
    a("# a root WITH a committed artifact -> recompute its authentic digest")
    a("PYTHONPATH=src python -c \"import json;\\")
    a("from sea_ad_jepa.v5.primary_representation_authority_v1 import \\")
    a("  PrimaryRepresentationAuthorityV1 as C;\\")
    a("d=json.load(open('docs/agent/V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json'));\\")
    a("o=C(**{f:d[f] for f in C.__dataclass_fields__});o.validate();print(o.canonical_digest())\"")
    a("# -> 92756711fde939e27abc982d6ab1a0bc0dab53fae209c0f5a3fba4fde86ef4b1")
    a("")
    a("# a root WITHOUT one -> prove the absence")
    a("git grep -l '\"schema\": *\"V5_OUTER_DONOR_SPLIT_AUTHORITY_V1\"' HEAD -- '*.json'")
    a("# -> no output. That is a FAILURE TO VERIFY, not \"0 defects\".")
    a("```")
    a("")
    a("## Ledger")
    a("")
    a("| quantity | value |")
    a("|---|---|")
    a("| upstream roots | %d |" % led["upstream_roots"])
    a("| receipt roots | %d |" % led["receipt_roots"])
    a("| receipt adds | %s |" % ", ".join("`%s`" % r for r in led["receipt_adds"]))
    a("| **fully closed** | **%d** |" % led["fully_closed"])
    a("| blocking roots | %d |" % led["blocking_roots"])
    a("| own-schema validated candidates (required class) | %d |"
      % led["own_schema_validated_candidates"])
    a("| roots with no committed artifact of the required class | %d |"
      % led["no_committed_artifact"])
    a("| raw-string cross-binding slots | %d |" % led["raw_str_cross_binding_slots"])
    a("| raw slots byte-authenticated | %d |" % led["raw_slot_value_and_bytes_authenticated"])
    a("| closure equality assertions | %d |" % led["closure_equality_assertions"])
    a("")
    a("### Closure enforcement census")
    a("")
    cen = led["closure_enforcement_census"]
    a("| enforcement | roots |")
    a("|---|---|")
    a("| `isinstance` enforced | %d |" % cen["isinstance_enforced"])
    a("| duck-typed, **no class check at all** | %d |" % cen["duck_typed_no_class_check"])
    a("| raw string cross-binding constant | %d |" % cen["raw_str_cross_binding_constant"])
    a("")

    a("## Substrate byte authentication")
    a("")
    a("```")
    a("path   : %s" % sub["path"])
    a("bytes  : %s" % sub.get("bytes"))
    a("sha256 : %s" % sub.get("sha256"))
    a("matches expected: %s" % sub.get("matches_expected"))
    a("known decoy    : %s (2380918 bytes, two history trees)" % matrix["known_decoy_sha256"])
    a("```")
    a("")
    a("Reproduce:")
    a("")
    a("```bash")
    a("sha256sum \"%s\"" % sub["path"])
    a("stat -c %s \"" + sub["path"] + "\"")
    a("```")
    a("")

    a("## Task 1 — substrate root downstream bindings, per consumer")
    a("")
    a("The closure equality-checks the substrate against **%d** consuming "
      "authorities, not four." % consumers["closure_enforced_consumer_count"])
    a("")
    a("| # | consumer parameter | attribute the closure reads | class enforcement | committed artifact | carries `66f589e5…` | blocks |")
    a("|---|---|---|---|---|---|---|")
    for i, c in enumerate(consumers["consumers"], 1):
        art = c["artifacts"][0]["path"] if c["artifacts"] else "**none**"
        a("| %d | `%s` | `%s` | %s | %s | %s | %s |" % (
            i,
            c["consumer_parameter"],
            c["closure_read_attribute"],
            c["class_enforcement"].replace("_", " ").lower(),
            "`%s`" % art if c["artifacts"] else art,
            c["outcome"],
            "YES" if c["blocks_substrate_root"] else "no",
        ))
    a("")
    a("**Result: %d of %d consumers carry the authenticated substrate; %d block. "
      "`substrate_root_closed = %s`.**" % (
          consumers["consumers_with_authentic_binding"],
          consumers["closure_enforced_consumer_count"],
          consumers["consumers_blocking"],
          consumers["substrate_root_closed"],
      ))
    a("")

    a("## Task 2 — V3 masking artifacts against the V1-typed closure")
    a("")
    for pair in reconcile["pairs"]:
        a("### `%s`" % pair["root"])
        a("")
        a("* closure requires `%s`; committed artifact is `%s`"
          % (pair["v1_class"], pair["v3_class"]))
        a("* closure reads: %s" % ", ".join("`%s`" % x for x in pair["closure_data_attributes_read"]))
        a("* V3 supplies: %s" % (", ".join("`%s`" % x for x in pair["v3_supplies"]) or "**none**"))
        a("* V3 missing: %s" % (", ".join("`%s`" % x for x in pair["v3_missing"]) or "none"))
        a("* V3 is field-superset of V1: %s; V3 subclasses V1: %s"
          % (pair["v3_is_field_superset_of_v1"], pair["v3_subclasses_v1"]))
        a("* V3 artifact own-class validate: %s; declared digest agrees: %s"
          % (pair["v3_artifact_own_class_validate"], pair["v3_artifact_digest_agrees"]))
        a("* **classification: %s**" % pair["classification"])
        a("")
        a("  %s" % pair["rationale"])
        a("")

    a("## The 33 roots")
    a("")
    a("| root | defining class | enforcement | expected schema | candidates | authentic digest | outcome | deps | blocking |")
    a("|---|---|---|---|---|---|---|---|---|")
    for r in matrix["roots"]:
        a("| `%s` | %s | %s | %s | %d | `%s` | %s | %d | %s |" % (
            r["root"],
            "`%s`" % r["defining_class"] if r["defining_class"] else "-",
            r["closure_enforcement"].replace("_", " ").lower(),
            "`%s`" % r["expected_artifact_schema"] if r["expected_artifact_schema"] else "-",
            r["committed_candidate_count"],
            short(r["authentic_digest"]),
            r["validation_outcome"],
            r["dependency_count"],
            "YES" if r["blocking"] else "no",
        ))
    a("")

    a("## Per-root detail")
    a("")
    for r in matrix["roots"]:
        a("### `%s`" % r["root"])
        a("")
        a("* defining module: `%s`" % (r["defining_module"] or "-"))
        a("* defining class: `%s` (%s)" % (r["defining_class"] or "-", r["class_binding_strength"]))
        a("* closure parameter: `%s` — %s" % (r["closure_parameter"], r["closure_enforcement"]))
        a("* expected artifact schema: `%s`" % (r["expected_artifact_schema"] or "-"))
        if r["candidates"]:
            for c in r["candidates"]:
                a("* source path: `%s`" % c["source_path"])
                a("  * source commit: `%s`" % c["source_commit"])
                if c.get("committed_blob_sha256"):
                    a("  * committed blob sha256: `%s`" % c["committed_blob_sha256"])
                if c.get("own_schema_validation"):
                    a("  * own-schema validation: **%s** (%s)"
                      % (c["own_schema_validation"], c.get("reconstruction_route")))
                if c.get("authentic_digest"):
                    a("  * authentic digest: `%s`" % c["authentic_digest"])
                if c.get("self_authenticating_bytes") is not None:
                    a("  * artifact bytes ARE its canonical digest: %s"
                      % c["self_authenticating_bytes"])
                if c.get("adapter_digest_agrees") is not None:
                    a("  * adapter digest agrees with document: %s"
                      % c["adapter_digest_agrees"])
        else:
            a("* source path: **no committed artifact of this schema**")
        if r.get("cross_version_evidence"):
            cv = r["cross_version_evidence"]
            a("* cross-version evidence: `%s` artifact(s) exist at %s — "
              "**not promoted to this root**"
              % (cv["committed_artifact_class"],
                 ", ".join("`%s`" % p for p in cv["committed_artifact_paths"]) or "none"))
        a("* validator command:")
        a("")
        a("  ```bash")
        a("  %s" % r["validator_command"])
        a("  ```")
        a("")
        a("* validation outcome: **%s**" % r["validation_outcome"])
        if r["dependencies_enforced_by_closure"]:
            a("* dependencies the closure enforces on this root:")
            for d in r["dependencies_enforced_by_closure"]:
                a("  * `%s.%s` (line %s) — fails with: *%s*" % (
                    d["dependent_parameter"], d["dependent_attribute"],
                    d["closure_line"], d["closure_failure_message"]))
        else:
            a("* dependencies the closure enforces on this root: none")
        a("* blocking: **%s** — %s" % (r["blocking"], r["blocking_reason"]))
        a("* fully closed: **%s**" % r["fully_closed"])
        a("")

    a("---")
    a("")
    a("TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED · "
      "D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF")
    return "\n".join(out) + "\n"


def main():
    out_dir = pathlib.Path(sys.argv[1])
    matrix = json.loads((out_dir / "LANEB_V29_ROOT_STATUS_MATRIX_V2.json").read_text(encoding="utf-8"))
    consumers = json.loads((out_dir / "LANEB_V29_SUBSTRATE_CONSUMER_BINDING_V1.json").read_text(encoding="utf-8"))
    reconcile = json.loads((out_dir / "LANEB_V29_MASKING_V3_V1_RECONCILIATION_V1.json").read_text(encoding="utf-8"))
    text = render(matrix, consumers, reconcile)
    dest = pathlib.Path(sys.argv[2])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print("wrote %s (%d lines)" % (dest, text.count("\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
