from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
import hashlib
import json
from pathlib import Path
import zipfile
import numpy as np
from .v79_rare_biology_generator_v1 import RareWorldConfig, generate_world, SOURCES

@dataclass(frozen=True)
class ProductionConfig:
    seed_root: int
    n_donors: int = 66
    cells_per_donor: int = 20
    regimes: tuple[str, ...] = ('weak','central','strong','extreme')
    worlds: tuple[str, ...] = ('rna_only','same_nucleus','separate_nucleus','technical_twin')


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _derive_seed(root: int, world_id: str) -> int:
    payload=f'V79_RARE_WORLD_PRODUCTION_V1|{root}|{world_id}'.encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big') % (2**32)


def _npy_bytes(arr: np.ndarray) -> bytes:
    b=BytesIO(); np.save(b, np.asarray(arr), allow_pickle=False); return b.getvalue()


def _write_npz_deterministic(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(arrays):
            info=zipfile.ZipInfo(f'{name}.npy', date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o600 << 16
            zf.writestr(info, _npy_bytes(arrays[name]))


def _code_entities(cells):
    source_map={s:i for i,s in enumerate(SOURCES)}
    source_code=np.array([source_map[s] for s in cells['source']], dtype=np.int8)
    donor_code=cells['donor_id'].str[1:].astype(int).to_numpy(dtype=np.int16)
    n=len(cells)
    rna_entity_code=np.arange(n, dtype=np.int32)
    same=(cells['rna_entity_id'].to_numpy() == cells['atac_entity_id'].to_numpy())
    atac_entity_code=np.where(same, rna_entity_code, rna_entity_code+n).astype(np.int32)
    return source_code, donor_code, rna_entity_code, atac_entity_code


def realize_production(cfg: ProductionConfig, out_dir: str | Path) -> dict:
    out=Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f'production output directory must be empty: {out}')
    (out/'fit_view').mkdir(parents=True, exist_ok=True)
    (out/'controller_truth').mkdir(parents=True, exist_ok=True)
    entries=[]
    idx=0
    for world in cfg.worlds:
        for regime in cfg.regimes:
            world_id=f'RW{idx:03d}'; idx += 1
            seed=_derive_seed(cfg.seed_root, world_id)
            w=generate_world(RareWorldConfig(seed=seed, n_donors=cfg.n_donors, cells_per_donor=cfg.cells_per_donor, regime=regime, world=world))
            sc, dc, rc, ac = _code_entities(w.cells)
            fit_rel=f'fit_view/{world_id}.npz'
            truth_rel=f'controller_truth/{world_id}.npz'
            _write_npz_deterministic(out/fit_rel, {
                'rna': w.rna.astype(np.float32),
                'atac': w.atac.astype(np.float32),
                'source_code': sc,
                'donor_code': dc,
                'rna_entity_code': rc,
                'atac_entity_code': ac,
            })
            _write_npz_deterministic(out/truth_rel, {
                'R': w.cells['R'].to_numpy(dtype=np.int8),
                'pseudo_rare': w.cells['pseudo_rare'].to_numpy(dtype=np.int8),
                'donor_active': w.cells['donor_active'].to_numpy(dtype=np.int8),
                'donor_prevalence': w.cells['donor_prevalence'].to_numpy(dtype=np.float32),
                'world_code': np.full(len(w.cells), cfg.worlds.index(world), dtype=np.int8),
                'regime_code': np.full(len(w.cells), cfg.regimes.index(regime), dtype=np.int8),
            })
            entries.append({
                'world_id': world_id, 'world': world, 'regime': regime, 'seed': seed,
                'fit_relpath': fit_rel, 'truth_relpath': truth_rel,
                'fit_sha256': _sha256(out/fit_rel), 'truth_sha256': _sha256(out/truth_rel),
                'n_cells': int(len(w.cells)), 'n_donors': int(w.cells['donor_id'].nunique()),
                'n_biological_positive': int(w.cells['R'].sum()),
                'n_pseudo_rare': int(w.cells['pseudo_rare'].sum()),
            })
    mapping={
        'schema':'V79_RARE_WORLD_PRODUCTION_CONTROLLER_MAP_V1',
        'source_code':{str(i):s for i,s in enumerate(SOURCES)},
        'world_code':{str(i):w for i,w in enumerate(cfg.worlds)},
        'regime_code':{str(i):r for i,r in enumerate(cfg.regimes)},
        'worlds':[{k:v for k,v in e.items() if k in ('world_id','world','regime','seed')} for e in entries],
    }
    map_path=out/'controller_truth'/'WORLD_MAP_V1.json'
    map_path.write_text(json.dumps(mapping, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    file_hashes=[]
    for p in sorted(x for x in out.rglob('*') if x.is_file()):
        rel=p.relative_to(out).as_posix(); file_hashes.append((rel,_sha256(p)))
    digest=hashlib.sha256('\n'.join(f'{rel},{sha}' for rel,sha in file_hashes).encode()).hexdigest()
    receipt={
        'schema':'V79_RARE_WORLD_PRODUCTION_RECEIPT_V1',
        'status':'REALIZED_ONCE__BLINDED_FIT_VIEW__CONTROLLER_TRUTH_SEPARATE',
        'seed_root':cfg.seed_root,
        'n_donors':cfg.n_donors,
        'cells_per_donor':cfg.cells_per_donor,
        'regimes':list(cfg.regimes),
        'world_types':list(cfg.worlds),
        'world_count':len(entries),
        'worlds':entries,
        'controller_map_sha256':_sha256(map_path),
        'directory_digest_sha256':digest,
        'fit_truth_separation':'fit_view contains observations/source/donor/entity codes only; R/pseudo/world/regime truth are controller-only',
    }
    (out/'V79_RARE_WORLD_PRODUCTION_RECEIPT_V1.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    return receipt
