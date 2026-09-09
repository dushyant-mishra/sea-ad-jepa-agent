"""Coverage-first full-population scheduling primitives for prospective V5.

N with-replacement presentations do not guarantee that all N reader-fit cells
are seen. This candidate defines a deterministic multiset: every canonical cell
appears at least once, and small donor x operator groups receive only the minimum
additional presentations required by a separately frozen group-coverage floor.

Scientific target mass remains donor-uniform through exact p/q correction, where
q is realized schedule multiplicity divided by total presentations. No production
numerical values are defaulted and this module grants no training authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from numbers import Integral
from typing import Mapping, Sequence

_DOMAIN=b"SEA_AD_JEPA_V5_FULL_POPULATION_COVERAGE_V1\0"

def _positive_int(value:object,name:str)->int:
    if isinstance(value,bool) or not isinstance(value,Integral) or int(value)<1:
        raise ValueError(f"{name} must be an explicit positive integer")
    return int(value)

def _cell_key(value:object)->int:
    out=_positive_int(value,"stable_cell_key")
    if out>=1<<64: raise ValueError("stable_cell_key must fit uint64")
    return out

def _nonempty(value:object,name:str)->str:
    if not isinstance(value,str) or not value: raise ValueError(f"{name} must be a nonempty string")
    return value

@dataclass(frozen=True)
class CoverageCell:
    stable_cell_key:int
    donor_id:str
    group_id:str
    source:str
    def validate(self)->None:
        _cell_key(self.stable_cell_key); _nonempty(self.donor_id,"donor_id")
        _nonempty(self.group_id,"group_id"); _nonempty(self.source,"source")

@dataclass(frozen=True)
class CoveragePresentation:
    stable_cell_key:int
    multiplicity:int
    target_probability:Fraction
    proposal_probability:Fraction
    importance_weight:Fraction

@dataclass(frozen=True)
class CoverageSchedule:
    presentations:tuple[CoveragePresentation,...]
    total_presentations:int
    unique_cells:int
    donors:int
    groups:int
    min_group_presentations:int
    max_cell_multiplicity:int
    all_cells_covered:bool

def _rank(seed:int,group_id:str,cell_key:int)->bytes:
    seed=_positive_int(seed,"authority_seed")
    if seed>=1<<64: raise ValueError("authority_seed must fit uint64")
    group=_nonempty(group_id,"group_id").encode("utf-8"); key=_cell_key(cell_key)
    return hashlib.sha256(_DOMAIN+seed.to_bytes(8,"little")+len(group).to_bytes(4,"little")+group+key.to_bytes(8,"little")).digest()

def build_coverage_first_schedule(cells:Sequence[CoverageCell],*,min_presentations_per_group:int,max_presentations_per_cell:int,authority_seed:int)->CoverageSchedule:
    """Build full coverage plus deterministic rare-group top-up.

    Every cell starts at multiplicity one. Small donor x operator groups are
    topped up by round-robin over a fixed hash rank. The realized proposal is
    q_i=m_i/H and the donor-uniform target is p_i=1/(D*n_donor), so each
    occurrence uses exact p_i/q_i and repeats cannot redefine biological mass.
    """
    floor=_positive_int(min_presentations_per_group,"min_presentations_per_group")
    cap=_positive_int(max_presentations_per_cell,"max_presentations_per_cell")
    seed=_positive_int(authority_seed,"authority_seed")
    if not cells: raise ValueError("cells cannot be empty")
    by_key={}; by_donor={}; by_group={}; group_donor={}
    for raw in cells:
        if not isinstance(raw,CoverageCell): raise ValueError("cells must contain CoverageCell records")
        raw.validate(); key=int(raw.stable_cell_key)
        if key in by_key: raise ValueError("stable_cell_key must be unique")
        by_key[key]=raw; by_donor.setdefault(raw.donor_id,[]).append(key); by_group.setdefault(raw.group_id,[]).append(key)
        previous=group_donor.setdefault(raw.group_id,raw.donor_id)
        if previous!=raw.donor_id: raise ValueError("group_id must identify one donor x operator group")
    multiplicity={key:1 for key in by_key}
    for group_id in sorted(by_group):
        keys=by_group[group_id]; required=max(0,floor-len(keys))
        if not required: continue
        ranked=sorted(keys,key=lambda key:(_rank(seed,group_id,key),key))
        for extra in range(required): multiplicity[ranked[extra%len(ranked)]]+=1
    max_mult=max(multiplicity.values())
    if max_mult>cap:
        raise ValueError(f"coverage floor requires per-cell multiplicity above the frozen cap: {max_mult} > {cap}")
    total=sum(multiplicity.values()); donor_count=len(by_donor); out=[]
    for key in sorted(by_key):
        donor=by_key[key].donor_id
        p=Fraction(1,donor_count*len(by_donor[donor])); q=Fraction(multiplicity[key],total)
        out.append(CoveragePresentation(key,multiplicity[key],p,q,p/q))
    if sum((x.target_probability for x in out),Fraction())!=Fraction(1,1): raise RuntimeError("target probabilities do not sum to one")
    if sum((x.proposal_probability for x in out),Fraction())!=Fraction(1,1): raise RuntimeError("proposal probabilities do not sum to one")
    p_by_donor={d:Fraction() for d in by_donor}
    for x in out: p_by_donor[by_key[x.stable_cell_key].donor_id]+=x.target_probability
    if set(p_by_donor.values())!={Fraction(1,donor_count)}: raise RuntimeError("donor-uniform target mass invariant failed")
    for group_id,keys in by_group.items():
        if sum(multiplicity[k] for k in keys)<floor: raise RuntimeError(f"group floor not achieved for {group_id}")
    return CoverageSchedule(tuple(out),total,len(by_key),donor_count,len(by_group),floor,max_mult,all(multiplicity[k]>=1 for k in by_key))

def expanded_presentation_keys(schedule:CoverageSchedule)->tuple[int,...]:
    keys=[]
    for item in schedule.presentations: keys.extend([item.stable_cell_key]*item.multiplicity)
    if len(keys)!=schedule.total_presentations: raise RuntimeError("expanded schedule length mismatch")
    return tuple(keys)

def exact_target_mass_by_donor(schedule:CoverageSchedule,cells:Sequence[CoverageCell])->Mapping[str,Fraction]:
    donor_by_key={int(c.stable_cell_key):c.donor_id for c in cells}; out={}
    for item in schedule.presentations:
        donor=donor_by_key[item.stable_cell_key]; out[donor]=out.get(donor,Fraction())+item.target_probability
    return out
