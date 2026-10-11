"""Metadata-only audit for dependence among donor resampling/partition cases."""
from __future__ import annotations

from collections import Counter


class ResamplingAuditError(ValueError):
    pass


def audit_cases(cases):
    if not isinstance(cases, list) or not cases:
        raise ResamplingAuditError("nonempty case list required")
    seen_case_ids=set()
    source=None
    normalized=[]
    for rec in cases:
        if not isinstance(rec, dict):
            raise ResamplingAuditError("case must be object")
        if set(rec) != {"case_id","source","donor_ids"}:
            raise ResamplingAuditError("case fields must be exact")
        cid=rec["case_id"]
        src=rec["source"]
        donors=rec["donor_ids"]
        if not isinstance(cid,str) or not cid:
            raise ResamplingAuditError("nonempty case_id required")
        if cid in seen_case_ids:
            raise ResamplingAuditError("duplicate case_id")
        seen_case_ids.add(cid)
        if source is None:
            source=src
        elif src != source:
            raise ResamplingAuditError("one source per audit required")
        if not isinstance(donors,list) or not donors:
            raise ResamplingAuditError("nonempty donor_ids list required")
        if any(not isinstance(d,str) or not d for d in donors):
            raise ResamplingAuditError("donor ids must be nonempty strings")
        if len(set(donors)) != len(donors):
            raise ResamplingAuditError("duplicate donor within case")
        normalized.append((cid,set(donors)))

    pairwise=[]
    pairwise_disjoint=True
    for i,(cid_a,a) in enumerate(normalized):
        for cid_b,b in normalized[i+1:]:
            overlap=sorted(a & b)
            union=a | b
            if overlap:
                pairwise_disjoint=False
            pairwise.append({
                "case_pair":[cid_a,cid_b],
                "overlap_count":len(overlap),
                "overlap_donors":overlap,
                "jaccard": len(overlap)/len(union),
            })
    memberships=Counter()
    for _,donors in normalized:
        memberships.update(donors)
    unique_donors=len(memberships)
    terminal = (
        "CASE_MEMBERSHIPS_DISJOINT__NO_BROADER_INDEPENDENCE_CLAIM"
        if pairwise_disjoint
        else "ROBUSTNESS_RESAMPLES_NOT_INDEPENDENT_REPLICATES"
    )
    return {
        "schema":"JEPA_TD_DONOR_RESAMPLING_DEPENDENCE_AUDIT_V1",
        "source":source,
        "case_count":len(normalized),
        "unique_donors":unique_donors,
        "biological_unit_n":unique_donors,
        "independent_n_from_case_rows": len(normalized) if pairwise_disjoint else None,
        "all_cases_pairwise_independent":pairwise_disjoint,
        "max_case_memberships_per_donor":max(memberships.values()),
        "pairwise":pairwise,
        "terminal":terminal,
        "authority":{
            "target_selected":False,
            "representation_selected":False,
            "training_authorized":False,
            "value_read_authorized":False,
        },
    }
