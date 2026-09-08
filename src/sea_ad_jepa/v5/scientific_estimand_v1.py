from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from numbers import Integral
from typing import Sequence


class EstimandPolicy(str,Enum):
    CELL_UNIFORM='CELL_UNIFORM'
    DONOR_UNIFORM='DONOR_UNIFORM'
    SOURCE_DONOR_UNIFORM='SOURCE_DONOR_UNIFORM'
    SOURCE_DONOR_OPERATOR_UNIFORM='SOURCE_DONOR_OPERATOR_UNIFORM'


@dataclass(frozen=True)
class GroupCount:
    source:str
    donor:str
    operator:int
    cells:int


def _validate(rows:Sequence[GroupCount])->tuple[GroupCount,...]:
    if not rows:
        raise ValueError('group counts cannot be empty')
    out=tuple(rows)
    keys=set()
    for r in out:
        if not isinstance(r.source,str) or not r.source or not isinstance(r.donor,str) or not r.donor:
            raise ValueError('source/donor must be nonempty strings')
        if isinstance(r.operator,bool) or not isinstance(r.operator,Integral) or int(r.operator)<0:
            raise ValueError('operator must be nonnegative integer')
        if isinstance(r.cells,bool) or not isinstance(r.cells,Integral) or int(r.cells)<1:
            raise ValueError('cells must be positive integer')
        key=(r.source,r.donor,int(r.operator))
        if key in keys:
            raise ValueError('duplicate source/donor/operator group')
        keys.add(key)
    return out


def group_masses(rows:Sequence[GroupCount], policy:EstimandPolicy)->tuple[float,...]:
    """Return target/proposal probability mass for each donor×operator group.

    No policy is selected by this module. A future authority must bind target
    p(cell) and proposal q(cell) separately.
    """
    rows=_validate(rows)
    policy=EstimandPolicy(policy)
    total=sum(r.cells for r in rows)
    sources=sorted({r.source for r in rows})
    source_count=len(sources)
    donors_by_source={s:sorted({r.donor for r in rows if r.source==s}) for s in sources}
    all_donors=[(s,d) for s in sources for d in donors_by_source[s]]
    donor_total={(s,d):sum(r.cells for r in rows if r.source==s and r.donor==d) for s,d in all_donors}
    donor_ops={(s,d):sum(1 for r in rows if r.source==s and r.donor==d) for s,d in all_donors}
    masses=[]
    for r in rows:
        if policy is EstimandPolicy.CELL_UNIFORM:
            mass=r.cells/total
        elif policy is EstimandPolicy.DONOR_UNIFORM:
            mass=(1/len(all_donors))*(r.cells/donor_total[(r.source,r.donor)])
        elif policy is EstimandPolicy.SOURCE_DONOR_UNIFORM:
            mass=(1/source_count)*(1/len(donors_by_source[r.source]))*(r.cells/donor_total[(r.source,r.donor)])
        else:
            mass=(1/source_count)*(1/len(donors_by_source[r.source]))*(1/donor_ops[(r.source,r.donor)])
        masses.append(float(mass))
    if abs(sum(masses)-1.0)>1e-12:
        raise RuntimeError('estimand masses do not sum to one')
    return tuple(masses)


def importance_diagnostics(
    rows:Sequence[GroupCount],
    *,
    target:EstimandPolicy,
    proposal:EstimandPolicy,
)->dict[str,float]:
    """Diagnose p/q variance without authorizing either p or q."""
    rows=_validate(rows)
    p=group_masses(rows,target)
    q=group_masses(rows,proposal)
    weights=[]
    second_moment=0.0
    for target_mass,proposal_mass in zip(p,q):
        if target_mass>0 and proposal_mass<=0:
            raise ValueError('proposal lacks support for target')
        weight=target_mass/proposal_mass
        weights.append(weight)
        second_moment += proposal_mass*weight*weight
    expected=sum(qi*w for qi,w in zip(q,weights))
    return {
        'expected_weight':expected,
        'relative_ess':(expected*expected)/second_moment,
        'minimum_weight':min(weights),
        'maximum_weight':max(weights),
        'weight_range_ratio':max(weights)/min(weights),
    }
