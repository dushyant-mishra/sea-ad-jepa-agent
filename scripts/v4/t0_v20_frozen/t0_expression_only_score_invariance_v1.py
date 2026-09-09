from __future__ import annotations
import numpy as np

def residualize_matrix(X: np.ndarray, Z: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    gamma=np.linalg.lstsq(Z,X,rcond=None)[0]
    return X-Z@gamma, gamma

def coefficient(y: np.ndarray, Z: np.ndarray, s: np.ndarray) -> float:
    A=np.column_stack([Z,s])
    if np.linalg.matrix_rank(A)<A.shape[1]: raise ValueError('rank deficient full model')
    return float(np.linalg.lstsq(A,y,rcond=None)[0][-1])

def check_invariance(X: np.ndarray,y: np.ndarray,Z: np.ndarray,beta: np.ndarray,scale: np.ndarray) -> dict[str,float]:
    if X.ndim!=2 or Z.ndim!=2 or y.ndim!=1 or beta.ndim!=1 or scale.ndim!=1: raise ValueError('bad shapes')
    if X.shape[0]!=len(y) or X.shape[0]!=Z.shape[0] or X.shape[1]!=len(beta) or X.shape[1]!=len(scale): raise ValueError('shape mismatch')
    if np.any(~np.isfinite(scale)) or np.any(scale<=0): raise ValueError('invalid scale')
    Xr,gamma=residualize_matrix(X,Z)
    sr=(Xr/scale)@beta
    sraw=(X/scale)@beta
    b_res=coefficient(y,Z,sr); b_raw=coefficient(y,Z,sraw)
    return {'coef_residual_score':b_res,'coef_raw_expression_score':b_raw,'abs_difference':abs(b_res-b_raw)}

def centered_cell_scores(raw_cells: np.ndarray, z_row: np.ndarray, gamma: np.ndarray, beta: np.ndarray, scale: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    if raw_cells.ndim!=2: raise ValueError('raw_cells must be 2D')
    offset=z_row@gamma
    raw=(raw_cells/scale)@beta
    adjusted=((raw_cells-offset)/scale)@beta
    return raw-raw.mean(), adjusted-adjusted.mean()
