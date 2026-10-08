#!/usr/bin/env python3
"""Synthetic shortcut smoke for privileged-state recoverability.

Software semantics only. No biological threshold or training authority.
"""
from __future__ import annotations
import json
import numpy as np


def _fit(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float)
    x1=np.column_stack([np.ones(len(x)),x])
    return np.linalg.lstsq(x1,y,rcond=None)[0]


def _pred(x,b):
    x=np.asarray(x,float)
    return np.column_stack([np.ones(len(x)),x])@b


def _r2(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float)
    ssr=np.square(y-p).sum()
    sst=np.square(y-y.mean()).sum()
    return float(1-ssr/sst)


def run_smoke():
    rng=np.random.default_rng(202609301)
    ntr,nte=3000,1500

    # Independent latent biological and technical drivers.
    bio_tr=rng.normal(size=(ntr,3)); bio_te=rng.normal(size=(nte,3))
    tech_tr=rng.normal(size=(ntr,1)); tech_te=rng.normal(size=(nte,1))

    # Lawful RNA carries both biology and a technical footprint.
    xtr=np.column_stack([
        bio_tr + 0.15*rng.normal(size=(ntr,3)),
        tech_tr + 0.08*rng.normal(size=(ntr,1)),
        rng.normal(size=(ntr,3)),
    ])
    xte=np.column_stack([
        bio_te + 0.15*rng.normal(size=(nte,3)),
        tech_te + 0.08*rng.normal(size=(nte,1)),
        rng.normal(size=(nte,3)),
    ])

    z_bio_tr=(bio_tr[:,0]-0.7*bio_tr[:,1]+0.4*bio_tr[:,2] + 0.08*rng.normal(size=ntr))
    z_bio_te=(bio_te[:,0]-0.7*bio_te[:,1]+0.4*bio_te[:,2] + 0.08*rng.normal(size=nte))

    # Looks "recoverable" from RNA, but only because RNA carries the same technical latent.
    z_short_tr=(1.4*tech_tr[:,0] + 0.08*rng.normal(size=ntr))
    z_short_te=(1.4*tech_te[:,0] + 0.08*rng.normal(size=nte))

    # Technical-only baseline is the declared technical proxy column.
    tech_xtr=xtr[:,3:4]; tech_xte=xte[:,3:4]

    bio_rna=_r2(z_bio_te,_pred(xte,_fit(xtr,z_bio_tr)))
    bio_tech=_r2(z_bio_te,_pred(tech_xte,_fit(tech_xtr,z_bio_tr)))
    short_rna=_r2(z_short_te,_pred(xte,_fit(xtr,z_short_tr)))
    short_tech=_r2(z_short_te,_pred(tech_xte,_fit(tech_xtr,z_short_tr)))

    out={
      "schema":"V64_PRIVILEGED_RECOVERABILITY_SHORTCUT_SMOKE_V1",
      "status":"SYNTHETIC_SOFTWARE_SMOKE_ONLY",
      "biology_factor":{
        "rna_r2":bio_rna,
        "technical_baseline_r2":bio_tech,
        "rna_advantage":bio_rna-bio_tech
      },
      "technical_shortcut_factor":{
        "rna_r2":short_rna,
        "technical_baseline_r2":short_tech,
        "rna_advantage":short_rna-short_tech
      },
      "pass":bool(
        bio_rna>0.90 and bio_tech<0.05 and
        short_rna>0.90 and short_tech>0.90 and
        abs(short_rna-short_tech)<0.02
      ),
      "interpretation":"High RNA predictability alone does not distinguish biology from a shared technical driver.",
      "training_authorized":False
    }
    return out


def main():
    out=run_smoke()
    print(json.dumps(out,sort_keys=True,indent=2))
    return 0 if out["pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
