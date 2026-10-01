import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/nested_modality_mask_uncertainty_anticollapse_synthetic_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("v67",P)
    assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_smoke_passes_and_is_non_authority():
    o=mod().run_smoke()
    assert o["pass"]
    assert o["governance"]["real_data_used"] is False
    assert o["governance"]["training"]=="OFF"
    assert o["governance"]["stage4"]=="NOT_AUTHORIZED"

def test_collapse_negative_controls():
    m=mod(); o=m.run_smoke()
    assert o["anti_collapse"]["rna"]["passes"]
    assert o["anti_collapse"]["multimodal"]["passes"]
    assert not o["anti_collapse"]["constant_negative"]["passes"]
    x=np.linspace(-1,1,200)[:,None]
    z=np.repeat(x,m.K_SHARED,axis=1)
    assert not m.anti_collapse(z)["passes"]

def test_mask_shortcut_and_uncertainty_rules():
    m=mod(); o=m.run_smoke()
    assert o["metrics"]["mask_only_shared_r2"]<0.03
    assert o["gates"]["missing_private_is_not_zero_filled"]
    assert o["gates"]["missing_private_uncertainty_is_higher"]
    assert o["metrics"]["uncertainty_ratio_missing_over_measured"]>3.0
    assert m.uncertainty_gate(.1,.5)
    assert not m.uncertainty_gate(.1,.1)
