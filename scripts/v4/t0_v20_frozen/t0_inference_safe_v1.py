from __future__ import annotations
from t0_studentized_fl_v1 import studentized_freedman_lane,NotEstimableError

def safe_studentized_fl(y,x_reduced,predictor,permutations):
    try:
        r=studentized_freedman_lane(y,x_reduced,predictor,permutations)
    except NotEstimableError as e:
        return {'estimable':False,'reason':str(e)}
    r=dict(r); r['estimable']=True
    return r
