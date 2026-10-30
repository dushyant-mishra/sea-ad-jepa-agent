"""Standalone, stdlib-only student view verifier: fixture consistency, NO issuer.

Macha #512 found (1) public #502 teacher-membership oracle reachable as
S.B from #510, (2) #510 receipt blind to source roster/operator states,
(3) receipt blind to validated view, and (4) unhashable rights raw TypeError.

This NEW versioned module imports NO project code and NO teacher producer.
Deploying this file in an independently restricted student process WITHOUT
the old Python source tree/issuer data is a separate, still unperformed action.
Import separation alone does not enforce an OS access-control boundary.

It does NOT authenticate a self-supplied expected policy, source counts,
alias classes, donor/physical identity, depositor QC, or a cryptographic
signing identity. In particular a consistent forged view+policy can pass.
"""
from __future__ import annotations
import hashlib

class StudentV2CRefusal(ValueError):
    """All unqualified input and policy failures, including hostile types."""

_STUDENT = "STUDENT_BASE_RIGHTS"
_SCHEMA = "TD_OBSERVATION_NORMALIZATION_VIEW_V2_BOUND_CONTENT_V1_FIXTURE"
_DEPTH = "BASE_RIGHTS_INVARIANT_NORMALIZATION_DEPTH_NOT_PHYSICAL_TOTAL"
_MS = "MEASURED_SCALAR"
_SU = "STRUCTURALLY_UNMEASURED"
_MCU = "MEASURED_COLLISION_UNRESOLVED"
_W = "WITHHELD_BY_EVIDENCE_RIGHTS"
_PHYSICAL_STATES = frozenset((_MS, _SU, _MCU))
_VIEW_KEYS = frozenset((
    "schema", "view_kind", "authority_scope", "query_address_id",
    "reader_partition", "depth_semantics", "rows",
    "source_authenticated", "donor_identity_authenticated",
    "physical_measurement_identity_authenticated",
    "q_rights_issuer_authenticated", "source_feature_mapping_authenticated",
    "external_truth_access_authorized", "same_code_path_authorized",
    "real_training_authorized", "authority_effect", "observable_sha256",
))
_ROW_KEYS = frozenset(("cell_id","donor_id","source_id","operator_id",
                       "address_id","evidence_right","state","count",
                       "base_rights_normalization_depth"))
_POLICY_KEYS = frozenset(("query_address_id","base_evidence_rights",
                          "address_rights","operator_states","cell_roster"))
_CELL_KEYS = frozenset(("cell_id","donor_id","source_id","operator_id"))
_DOMAIN = b"JEPA-TD-UNIFIED-CANONICAL-V1\x00"


def _deny(message):
    raise StudentV2CRefusal(message)


def _snap(x, depth=0):
    """Strict snapshot before any potentially attacker-controlled dispatch."""
    if depth > 32: _deny("V2C evidence nesting exceeds declared limit")
    t=type(x)
    if x is None or t is bool:
        return x
    if t is int:
        if not -(2**53) < x < 2**53: _deny("V2C count outside exact integer domain")
        return x
    if t is str:
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in x):
            _deny("V2C unpaired Unicode surrogate")
        return x
    if t is list:
        return [_snap(v,depth+1) for v in x]
    if t is dict:
        result={}
        for k,v in dict.items(x):
            if type(k) is not str: _deny("V2C policy/view keys require exact strings")
            result[k]=_snap(v,depth+1)
        return result
    _deny("V2C refuses non-exact JSON evidence")


def _norm(s):
    return str.replace(str.replace(s,"\r\n","\n"),"\r","\n")


def _enc_str(s):
    out=['"']
    for ch in _norm(s):
        c=ord(ch)
        if 0xD800<=c<=0xDFFF:_deny("V2C invalid Unicode")
        if ch == '"':out.append('\\"')
        elif ch=="\\":out.append("\\\\")
        elif ch=="\n":out.append("\\n")
        elif ch=="\t":out.append("\\t")
        elif ch=="\b":out.append("\\b")
        elif ch=="\f":out.append("\\f")
        elif c<32:out.append("\\u%04x"%c)
        else:out.append(ch)
    out.append('"')
    return "".join(out)


def _enc(x):
    t=type(x)
    if x is None:return "null"
    if t is bool:return "true" if x else "false"
    if t is int:return str(x)
    if t is str:return _enc_str(x)
    if t is list:return "["+",".join(_enc(v) for v in x)+"]"
    if t is dict:
        normalized={}
        for k,v in x.items():
            nk=_norm(k)
            if nk in normalized:_deny("V2C canonical key collision")
            normalized[nk]=v
        return "{"+",".join(_enc_str(k)+":"+_enc(normalized[k])
                            for k in sorted(normalized))+"}"
    _deny("V2C canonical type unsupported")


def _sha(x):
    try:
        return hashlib.sha256(_DOMAIN+_enc(x).encode("utf8")).hexdigest()
    except (UnicodeEncodeError,RecursionError,OverflowError,ValueError) as exc:
        raise StudentV2CRefusal("V2C canonical encoding refused") from None


def _token(x):
    return (type(x) is str and bool(x) and x==x.strip() and
            not any(ord(ch)<32 or ord(ch)==127 for ch in x))


def validate_student_v2c(*, student_view, expected_policy):
    """Pure student-only consistency check, not a source-authentication service.

    Accepted receipt commits to the COMPLETE policy and exact student view.
    It contains no issuer signature and NEVER upgrades source/training flags.
    For any input with a nonstudent/missing role, one constant refusal occurs
    BEFORE copying or inspecting rich teacher candidate content.
    """
    if type(student_view) is not dict or dict.get(student_view,"view_kind")!=_STUDENT:
        _deny("V2C accepts STUDENT_BASE_RIGHTS only")
    view=_snap(student_view)
    policy=_snap(expected_policy)
    if type(view) is not dict or set(view)!=_VIEW_KEYS:
        _deny("V2C student schema fields differ")
    if (view["schema"]!=_SCHEMA or view["authority_scope"]!="FIXTURE_ONLY" or
        view["reader_partition"]!="reader_fit" or
        view["depth_semantics"]!=_DEPTH or view["authority_effect"]!="NONE"):
        _deny("V2C student may not claim external or legacy authority")
    for k in ("source_authenticated","donor_identity_authenticated",
              "physical_measurement_identity_authenticated",
              "q_rights_issuer_authenticated","source_feature_mapping_authenticated",
              "external_truth_access_authorized","same_code_path_authorized",
              "real_training_authorized"):
        if view[k] is not False:_deny("V2C unauthorized issuer claim")
    digest=view["observable_sha256"]
    body={k:v for k,v in view.items() if k!="observable_sha256"}
    if (type(digest) is not str or len(digest)!=64 or
            any(c not in "0123456789abcdef" for c in digest) or
            _sha(body)!=digest):
        _deny("V2C student observable digest mismatch")
    if type(policy) is not dict or set(policy)!=_POLICY_KEYS:
        _deny("V2C requires exact independently specified source policy")
    q=policy["query_address_id"]
    rights=policy["address_rights"]
    base=policy["base_evidence_rights"]
    states=policy["operator_states"]
    roster=policy["cell_roster"]
    if (not _token(q) or type(rights) is not dict or not rights or
        type(base) is not list or not base or
        any(not _token(x) for x in base)):
        _deny("V2C expected rights policy malformed")
    # Must validate every unhashable/hostile element BEFORE calling set().
    if len(set(base))!=len(base):_deny("V2C duplicate base evidence right")
    if any(not _token(a) or not _token(x) for a,x in rights.items()):
        _deny("V2C expected address rights malformed")
    base_set=frozenset(base)
    if q not in rights or rights[q] in base_set:
        _deny("V2C query cannot be a student base right")
    if type(states) is not dict or not states or type(roster) is not list or not roster:
        _deny("V2C source operator states or roster absent")
    for op,attrs in states.items():
        if (not _token(op) or type(attrs) is not dict or
            set(attrs)!=set(rights) or
            any(type(s) is not str or s not in _PHYSICAL_STATES for s in attrs.values())):
            _deny("V2C operator/source feature state policy malformed")
    cells={}
    for cell in roster:
        if (type(cell) is not dict or set(cell)!=_CELL_KEYS or
            any(not _token(v) for v in cell.values())):
            _deny("V2C source roster fields malformed")
        cid=cell["cell_id"]
        if cid in cells or cell["operator_id"] not in states:
            _deny("V2C duplicate source cell or unknown operator")
        cells[cid]=cell
    rows=view["rows"]
    if type(rows) is not list or not rows:
        _deny("V2C student observations absent")
    if view["query_address_id"]!=q:_deny("V2C wrong query")
    present=set()
    base_sum={}
    depth={}
    for row in rows:
        if type(row) is not dict or set(row)!=_ROW_KEYS:
            _deny("V2C student row fields differ")
        if any(not _token(row[k]) for k in
               ("cell_id","donor_id","source_id","operator_id",
                "address_id","evidence_right")):
            _deny("V2C noncanonical row identity")
        cid,addr=row["cell_id"],row["address_id"]
        cell=cells.get(cid)
        if cell is None or addr not in rights:
            _deny("V2C unknown cell or address")
        if (cid,addr) in present:
            _deny("V2C duplicate cell/address row")
        present.add((cid,addr))
        if (any(row[k]!=cell[k] for k in _CELL_KEYS) or
            row["evidence_right"]!=rights[addr]):
            _deny("V2C source identity/evidence right differs")
        physical=states[cell["operator_id"]][addr]
        d,n,s=row["base_rights_normalization_depth"],row["count"],row["state"]
        if physical==_MS and rights[addr] in base_set:
            if (s!=_MS or type(n) is not int or n<0 or
                type(d) is not int or d<=0):
                _deny("V2C base scalar/depth invalid")
            if cid in depth and depth[cid]!=d:
                _deny("V2C inconsistent per-cell D1")
            depth[cid]=d
            base_sum[cid]=base_sum.get(cid,0)+n
        else:
            expected_state=physical if physical!=_MS else _W
            if s!=expected_state or n is not None or d is not None:
                _deny("V2C nonbase or non-scalar evidence exposed")
    if len(present)!=len(cells)*len(rights):
        _deny("V2C source roster or address coverage incomplete")
    for cid,cell in cells.items():
        if (any((cid,a) not in present for a in rights) or
            states[cell["operator_id"]][q]!=_MS or
            depth.get(cid)!=base_sum.get(cid,0) or
            base_sum.get(cid,0)<=0 or base_sum[cid]>=2**53):
            _deny("V2C source query state or base D1 inconsistent")
    receipt={
        "schema":"JEPA_V2C_STANDALONE_STUDENT_CONSISTENCY_FIXTURE_RECEIPT_V1",
        "status":"STUDENT_ONLY_CONTENT_POLICY_CONSISTENT_NO_AUTHORITY",
        "validated_student_view_sha256":digest,
        "complete_policy_sha256":_sha(policy),
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
    return {**receipt,"receipt_sha256":_sha(receipt)}
