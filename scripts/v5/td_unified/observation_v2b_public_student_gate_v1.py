"""Student-only V2B evidence-rights consistency gate; fixture, NO issuer.

Replaces use of #502's teacher-aware *public* validator at the student trust
boundary. It NEVER queries or mutates process-local teacher issuance state.
For any view claiming TEACHER role it returns one fixed role refusal, before
digest/policy/rows inspection. A student can no longer query which rich teacher
candidates have been issued. The old #502 method is not a safe public API.

The caller must supply an INDEPENDENT, frozen expected policy (including
complete cell roster and operator states). A caller-controlled policy is NOT a
trusted issuer; no external signature, source record, biological/authenticated
gene alias or physical provenance is inferred here. This is fixture mechanics.
"""
from __future__ import annotations

from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V2
from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B
from scripts.v5.td_unified.q_excluded_depth_v1 import (
    MEASURED_SCALAR, STRUCTURALLY_UNMEASURED, MEASURED_COLLISION_UNRESOLVED,
    WITHHELD_BY_EVIDENCE_RIGHTS, QExcludedObservationError, canonical_sha256,
)

POLICY_KEYS=frozenset({"query_address_id","base_evidence_rights","address_rights",
                       "operator_states","cell_roster"})
CELL_KEYS=frozenset({"cell_id","donor_id","source_id","operator_id"})
STATES=frozenset({MEASURED_SCALAR,STRUCTURALLY_UNMEASURED,MEASURED_COLLISION_UNRESOLVED})
RESULT_SCHEMA="JEPA_V2B_PUBLIC_STUDENT_POLICY_CONSISTENCY_FIXTURE_V1"
RESULT_STATUS="STUDENT_CONTENT_CONSISTENT_FIXTURE_ONLY"


def _bad(message):
    raise QExcludedObservationError(message)


def validate_public_student_v2b(*, student_view, expected_policy):
    """Validate only student-visible content against independently supplied policy.

    expected_policy is privately held by an upstream source/rights issuer.
    There IS NO such authenticated issuer in this repository. Supplying a
    policy from the same user/world as the student proves no custody at all.
    """
    # Exact JSON snapshots before processing any hostile values or comparisons.
    student=V2._view_snapshot(student_view)
    policy=V2._view_snapshot(expected_policy)
    if type(student) is not dict:
        _bad("public student V2B requires an exact view")
    # This guard is deliberately independent of all teacher counts, digest,
    # issuance registries and arguments. Even a correctly issued teacher gets
    # the same refusal as a guessed, malformed or never-issued teacher view.
    if student.get("view_kind") != V2._STUDENT:
        _bad("public V2B only accepts STUDENT_BASE_RIGHTS")
    if type(policy) is not dict or set(policy)!=POLICY_KEYS:
        _bad("public V2B requires a separately frozen expected policy")
    q=policy["query_address_id"]
    rights=policy["address_rights"]
    base=policy["base_evidence_rights"]
    states=policy["operator_states"]
    cells=policy["cell_roster"]
    if (type(q) is not str or not q or q!=q.strip() or
        type(rights) is not dict or not rights or
        type(base) is not list or not base or
        len(base)!=len(set(base)) or
        any(type(v) is not str or not v for v in base) or
        type(states) is not dict or not states or
        type(cells) is not list or not cells):
        _bad("public V2B expected policy is malformed")
    if any(type(a) is not str or not a or type(v) is not str or not v
           for a,v in rights.items()):
        _bad("public V2B address policy invalid")
    base_set=frozenset(base)
    if q not in rights or rights[q] in base_set:
        _bad("public V2B queried evidence not withheld by expected base")
    for op, by_addr in states.items():
        if (type(op) is not str or not op or
                type(by_addr) is not dict or set(by_addr)!=set(rights) or
                any(type(v) is not str or v not in STATES for v in by_addr.values())):
            _bad("public V2B operator state policy malformed")
    expected_cells={}
    for c in cells:
        if (type(c) is not dict or set(c)!=CELL_KEYS or
                any(type(v) is not str or not v or v!=v.strip() for v in c.values())):
            _bad("public V2B source cell roster malformed")
        if c["cell_id"] in expected_cells or c["operator_id"] not in states:
            _bad("public V2B duplicate or unknown source cell")
        expected_cells[c["cell_id"]]=c
    if set(student)!=V2._VIEW_KEYS or student.get("schema")!=B._SCHEMA:
        _bad("public V2B requires versioned bound-content student schema")
    # Check only the student-visible fields, never any teacher issuance map.
    digest=student["observable_sha256"]
    body={k:v for k,v in student.items() if k!="observable_sha256"}
    if (type(digest) is not str or len(digest)!=64 or
            any(ch not in "0123456789abcdef" for ch in digest) or
            canonical_sha256(body)!=digest):
        _bad("public V2B student observable digest mismatch")
    old=dict(body)
    old["schema"]=V2._SCHEMA
    old["observable_sha256"]=canonical_sha256(old)
    V2.validate_fixture_observation_view_v2(old)
    if student["query_address_id"]!=q:
        _bad("public V2B query differs from expected policy")
    addr_set=set(rights)
    seen=set(); per_cell={}; base_totals={}; depths={}
    for row in student["rows"]:
        cid,aid=row["cell_id"],row["address_id"]
        c=expected_cells.get(cid)
        if c is None:
            _bad("public V2B row lacks expected source cell")
        if any(row[k]!=c[k] for k in CELL_KEYS):
            _bad("public V2B row identity differs from expected source cell")
        if aid not in addr_set or row["evidence_right"]!=rights[aid]:
            _bad("public V2B address right differs from expected policy")
        key=(cid,aid)
        if key in seen:
            _bad("public V2B duplicated expected observation")
        seen.add(key)
        per_cell.setdefault(cid,set()).add(aid)
        physical=states[c["operator_id"]][aid]
        state=row["state"]
        if physical==MEASURED_SCALAR:
            should_measured=rights[aid] in base_set
            required=MEASURED_SCALAR if should_measured else WITHHELD_BY_EVIDENCE_RIGHTS
            if state!=required:
                _bad("public V2B state violates frozen operator and rights")
            if should_measured:
                d=row["base_rights_normalization_depth"]
                if cid in depths and depths[cid]!=d:
                    _bad("public V2B inconsistent base depth")
                depths[cid]=d
                base_totals[cid]=base_totals.get(cid,0)+row["count"]
        elif state!=physical:
            _bad("public V2B missing or invented scalar state")
    if set(per_cell)!=set(expected_cells):
        _bad("public V2B source cell coverage differs")
    for cid,covered in per_cell.items():
        if covered!=addr_set:
            _bad("public V2B address coverage differs")
        if cid not in depths or depths[cid]!=base_totals.get(cid,0):
            _bad("public V2B D1 does not equal measured base sum")
    # A public POLICY commitment binds only query+rights, not row/source IDs,
    # private inputs, teacher digest or QC selection. A caller can still create
    # a different policy; the actual issuer must independently pin this value.
    public_policy={
        "query_address_id":q,
        "base_evidence_rights":sorted(base_set),
        "address_rights":{a:rights[a] for a in sorted(rights)},
    }
    return {
        "schema":RESULT_SCHEMA,
        "status":RESULT_STATUS,
        "policy_commitment_sha256":canonical_sha256(public_policy),
        "source_rights_issuer_authenticated":False,
        "physical_measurement_identity_authenticated":False,
        "donor_specimen_identity_authenticated":False,
        "source_feature_alias_closure_authenticated":False,
        "depositor_qc_selection_authenticated":False,
        "teacher_issuance_authenticated":False,
        "g7_content_v2_authorized":False,
        "real_training_authorized":False,
        "authority_effect":"NONE",
    }
