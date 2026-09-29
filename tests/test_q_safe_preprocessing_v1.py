import numpy as np
import pytest
from sea_ad_jepa.v5.q_safe_preprocessing_v1 import normalize_q_excluded_total, normalize_fixed_reference

def fixture():
    c=np.array([[5,10,2,0],[3,4,7,1]],dtype=np.float64)
    s=np.ones_like(c,dtype=np.uint8)
    q=1
    lib=c.sum(1)+np.array([20,30],dtype=float)
    return c,s,q,lib

def test_q_excluded_total_is_invariant_when_q_and_library_move_together():
    c,s,q,lib=fixture(); a,qa=normalize_q_excluded_total(c,s,lib,q)
    c2=c.copy(); c2[:,q]+=np.array([100,7.]); lib2=lib+np.array([100,7.])
    b,qb=normalize_q_excluded_total(c2,s,lib2,q)
    keep=[i for i in range(c.shape[1]) if i!=q]
    np.testing.assert_allclose(a[:,keep],b[:,keep],rtol=0,atol=0)
    np.testing.assert_array_equal(qa,qb)
    assert np.all(a[:,q]==0) and np.all(b[:,q]==0)

def test_fixed_reference_is_invariant_to_q_mutation():
    c,s,q,lib=fixture(); ref=np.array([100.,120.]); a,qa=normalize_fixed_reference(c,s,ref,q)
    c2=c.copy(); c2[:,q]+=1000; b,qb=normalize_fixed_reference(c2,s,ref,q)
    keep=[i for i in range(c.shape[1]) if i!=q]
    np.testing.assert_allclose(a[:,keep],b[:,keep],rtol=0,atol=0)
    np.testing.assert_array_equal(qa,qb)

def test_nonpositive_q_excluded_denominator_stops():
    c,s,q,lib=fixture(); lib=c[:,q].copy()
    with pytest.raises(ValueError): normalize_q_excluded_total(c,s,lib,q)
