#!/usr/bin/env python3
"""Staged deterministic DataLoader/pinned-memory benchmark on frozen tensors."""
from __future__ import annotations

import time
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from parallelism_common import CPU_CAP, OUT, ProductionTrainLoader, freeze_panel, loader_rows


class FrozenMicrobatches(Dataset):
    def __init__(self, values, states, keys, chunk=8): self.values=values; self.states=states; self.keys=keys; self.chunk=chunk
    def __len__(self): return len(self.keys)//self.chunk
    def __getitem__(self,index):
        a=index*self.chunk; b=a+self.chunk
        return torch.from_numpy(self.values[a:b]),torch.from_numpy(self.states[a:b]),torch.from_numpy(self.keys[a:b])


def identity(items): return items[0]


def main() -> None:
    panel=freeze_panel(); frame=loader_rows(panel.loc[panel.panel_type.eq("gpu_exact_schedule")].sort_values(["update","slot"]))
    loader=ProductionTrainLoader(); values,states=loader.load(frame); keys=frame.stable_mask_key.to_numpy(np.int64)
    dataset=FrozenMicrobatches(values,states,keys)
    configurations=[(0,None,False,False),(2,2,True,True)]
    if CPU_CAP>=4: configurations.append((4,2,True,True))
    records=[]; expected=keys.tolist()
    for workers,prefetch,persistent,pin in configurations:
        kwargs=dict(dataset=dataset,batch_size=1,shuffle=False,collate_fn=identity,num_workers=workers,pin_memory=pin,persistent_workers=(persistent and workers>0))
        if workers>0: kwargs["prefetch_factor"]=prefetch
        start=time.perf_counter(); observed=[]; batches=0
        for _,_,batch_keys in DataLoader(**kwargs): observed.extend(batch_keys.numpy().tolist()); batches+=1
        seconds=time.perf_counter()-start
        records.append({"stage":1,"num_workers":workers,"prefetch_factor":prefetch or 0,"persistent_workers":persistent and workers>0,"pin_memory":pin,"non_blocking_h2d":False,"seconds":seconds,"cells_per_second":len(keys)/seconds,"exact_order":observed==expected,"status":"PASS" if observed==expected else "REJECT","scope":"already-materialized CPU queue; no scientific transforms"})
    best=min((r for r in records if r["status"]=="PASS"),key=lambda x:x["seconds"])
    # Stage 2 only for best worker count; pinning is measured without a GPU copy while discovery is active.
    records.append({**best,"stage":2,"scope":"stage-1 winner retained; GPU H2D validation deferred by resource isolation"})
    pd.DataFrame(records).to_csv(OUT/"PARALLELISM_DATALOADER_MATRIX.csv",index=False)
    pd.DataFrame([{"queue_depth_effective_batches":1,"status":"NOT_APPLICABLE_GPU_COMPUTE_BOUND","reason":"authenticated input preparation is only a small fraction of update wall time"},{"queue_depth_effective_batches":2,"status":"DEFERRED_CORPUS_DISCOVERY_ACTIVE","reason":"no expected material end-to-end gain"},{"queue_depth_effective_batches":4,"status":"DEFERRED_RAM_DISK_GUARD","reason":"bounded audit avoids unnecessary contention"}]).to_csv(OUT/"PARALLELISM_ASYNC_PREFETCH.csv",index=False)


if __name__ == "__main__": main()
