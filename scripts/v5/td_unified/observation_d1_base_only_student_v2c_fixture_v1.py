"""Fixture-only D1 base redaction -> standalone V2C consistency composition.

New versioned producer, stacked on #514. The original #511 (V2B) and its
tests remain unchanged. Accepts only previously redacted base counts, never a
physical library total, private teacher value, or source-residual molecule.

The expected policy and source counts are SELF-SUPPLIED and UNAUTHENTICATED.
This does not certify alias closure, donor/specimen identity, QC selection,
physical source authenticity, independent issuer, or OS student isolation.
The student deployment must receive ONLY the separately isolated V2C verifier,
never this producer, the source tree, #502, or private source credentials.
No Stage4, real source issuance, target winner, or training authority.
"""
from __future__ import annotations

from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C

MS, SU, MCU, WITHHELD = C._MS, C._SU, C._MCU, C._W

_SCHEMA="JEPA_D1_BASE_ONLY_STUDENT_V2C_FIXTURE_PRODUCER_V1"
_CELL_KEYS=frozenset(("cell_id","donor_id","source_id","operator_id"))
_OBS_KEYS=frozenset(("cell_id","base_counts"))
_STATES=frozenset((MS,SU,MCU))


def _reject(message):
    raise C.StudentV2CRefusal(message)


def _token(value):
    return (type(value) is str and bool(value) and value==value.strip()
            and not any(ord(ch)<32 or ord(ch)==127 for ch in value))


def produce_d1_base_only_student_v2c_fixture(*, base_observations, expected_policy):
    """Only accepts already-redacted base scalar counts (omitted zero allowed).

    base_observations: list of {cell_id, base_counts:{address:raw_count}}.
    expected_policy: externally *unverified* same rights/roster schema as #514 V2C,
       with complete cell_roster, address_rights and operator_states.

    Cannot authenticate a caller's policy, the deposited source identity or
    pre-projection selection. Refuses base D1=0 with one fixed error regardless
    of any query count, because no query count may enter the input at all.
    """
    frozen=C._snap({
        "base_observations":base_observations,
        "expected_policy":expected_policy,
    })
    pol=frozen["expected_policy"]
    if type(pol) is not dict or set(pol)!=C._POLICY_KEYS:
        _reject("D1 producer requires an exact independently supplied policy")
    rights, base, states = pol["address_rights"],pol["base_evidence_rights"],pol["operator_states"]
    roster,q=pol["cell_roster"],pol["query_address_id"]
    if (not _token(q) or type(rights) is not dict or not rights or
            type(base) is not list or not base or
            any(not _token(x) for x in base) or len(set(base))!=len(base) or
            type(states) is not dict or not states or
            type(roster) is not list or not roster):
        _reject("D1 source policy is malformed")
    base_set=frozenset(base)
    for addr,right in rights.items():
        if not _token(addr) or not _token(right):
            _reject("D1 source address rights are malformed")
    if q not in rights or rights[q] in base_set:
        _reject("D1 source query must be outside base rights")
    addresses=sorted(rights)
    if not any(x in base_set for x in rights.values()):
        _reject("D1 policy has no base-right address")
    for op, amap in states.items():
        if (not _token(op) or type(amap) is not dict or
                set(amap)!=set(rights) or
                any(type(s) is not str or s not in _STATES for s in amap.values())):
            _reject("D1 source operator measurement state is malformed")
    cell_map={}
    for c in roster:
        if (type(c) is not dict or set(c)!=_CELL_KEYS or
                any(not _token(x) for x in c.values()) or
                c["cell_id"] in cell_map or c["operator_id"] not in states):
            _reject("D1 source cell roster is malformed")
        # #492 source observability law: exact operator x address must be a
        # measured scalar for a query. Structural absence or unresolved
        # collision is not a target, even if base counts are well-formed.
        if states[c["operator_id"]][q]!=MS:
            raise C.StudentV2CRefusal(
                "queried address is not measured-scalar in the selected operator")
        cell_map[c["cell_id"]]=c
    if type(frozen["base_observations"]) is not list or not frozen["base_observations"]:
        _reject("D1 base observations absent")
    measured={}
    for item in frozen["base_observations"]:
        if type(item) is not dict or set(item)!=_OBS_KEYS or not _token(item["cell_id"]):
            _reject("D1 base observation fields malformed")
        cid=item["cell_id"]
        if cid not in cell_map or cid in measured:
            _reject("D1 base observation cell missing or duplicated")
        counts=item["base_counts"]
        if type(counts) is not dict:
            _reject("D1 base counts must be an exact mapping")
        phys=states[cell_map[cid]["operator_id"]]
        for addr,count in counts.items():
            if (addr not in rights or rights[addr] not in base_set or
                    phys[addr]!=MS):
                _reject("D1 base input contains non-base or unmeasured count")
            if type(count) is not int or count<0:
                _reject("D1 base input count is not an exact nonnegative integer")
        measured[cid]=counts
    if set(measured)!=set(cell_map):
        _reject("D1 source cell roster and base observation coverage differ")
    rows=[]
    for cid in sorted(cell_map):
        cell=cell_map[cid]
        phys=states[cell["operator_id"]]
        counts=measured[cid]
        depth=sum(counts.values())
        if depth >= 2**53:
            _reject("D1 base depth exceeds canonical integer domain")
        if depth==0:
            raise C.StudentV2CRefusal("no base-visible normalization depth remains for this cell")
        for addr in addresses:
            physical_state=phys[addr]
            if physical_state==MS:
                if rights[addr] in base_set:
                    state,value,d=MS,counts.get(addr,0),depth
                else:
                    state,value,d=WITHHELD,None,None
            else:
                state,value,d=physical_state,None,None
            rows.append({
                "cell_id":cid,"donor_id":cell["donor_id"],
                "source_id":cell["source_id"],"operator_id":cell["operator_id"],
                "address_id":addr,"evidence_right":rights[addr],
                "state":state,"count":value,
                "base_rights_normalization_depth":d,
            })
    body={
        "schema":C._SCHEMA,"view_kind":C._STUDENT,
        "authority_scope":"FIXTURE_ONLY","query_address_id":q,
        "reader_partition":"reader_fit","depth_semantics":C._DEPTH,
        "rows":rows,"source_authenticated":False,
        "donor_identity_authenticated":False,
        "physical_measurement_identity_authenticated":False,
        "q_rights_issuer_authenticated":False,
        "source_feature_mapping_authenticated":False,
        "external_truth_access_authorized":False,
        "same_code_path_authorized":False,
        "real_training_authorized":False,"authority_effect":"NONE",
    }
    view={**body,"observable_sha256":C._sha(body)}
    # Standalone V2C validates the complete policy, roster, operator states,
    # exact student view digest and D1 without ever checking teacher issuance.
    # Receipt is consistency-only; neither the view nor policy is signed.
    receipt=C.validate_student_v2c(
        student_view=view, expected_policy=pol)
    if receipt["status"]!="STUDENT_ONLY_CONTENT_POLICY_CONSISTENT_NO_AUTHORITY" or receipt["authority_effect"]!="NONE":
        _reject("D1 V2C fixture gate refused constructed source view")
    return view
