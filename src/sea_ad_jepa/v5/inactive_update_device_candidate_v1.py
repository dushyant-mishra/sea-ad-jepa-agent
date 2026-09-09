"""Bounded inactive update candidate using vectorized V2 keyed dropout.

It deliberately reuses the frozen reference update/checkpoint chronology.  This
is a mechanical qualification candidate, not a production trainer.
"""
from __future__ import annotations
from copy import deepcopy
import torch
from sea_ad_jepa.v4.ipb_jepa import BlockPredictor
from .inactive_update_reference import V5ReferenceModules
from .keyed_dropout_device_candidate_v1 import KeyedIPBEncoderV2DeviceCandidate


def build_device_candidate_modules(*,vocabulary_size:int,width:int,heads:int,blocks:int,ffn_width:int,dropout:float,learning_rate:float,betas:tuple[float,float],eps:float,weight_decay:float,init_seed:int,device:torch.device|str='cpu')->V5ReferenceModules:
    torch.manual_seed(int(init_seed))
    online=KeyedIPBEncoderV2DeviceCandidate(width=width,heads=heads,blocks=blocks,ffn_width=ffn_width,dropout=dropout,vocabulary_size=vocabulary_size).to(device)
    teacher=deepcopy(online).eval()
    for p in teacher.parameters(): p.requires_grad_(False)
    predictor=BlockPredictor(width=width,heads=heads).to(device)
    online.train(); predictor.train()
    optimizer=torch.optim.AdamW(list(online.parameters())+list(predictor.parameters()),lr=float(learning_rate),betas=betas,eps=float(eps),weight_decay=float(weight_decay))
    return V5ReferenceModules(online,teacher,predictor,optimizer)
