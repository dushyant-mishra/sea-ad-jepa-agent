import anndata as ad
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from pathlib import Path

def main():
    ref_path = "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"
    print(f"Reading genes from {ref_path}")
    ref_adata = ad.read_h5ad(ref_path, backed="r")
    genes = list(ref_adata.var_names.astype(str))
    ref_adata.file.close()
    
    genes = genes + ["EXTRA_GENE_1", "EXTRA_GENE_2", "EXTRA_GENE_3"]
    n_genes = len(genes)
    
    n_cells = 100
    perturbations = ["control"] * 40 + ["APOE"] * 15 + ["ABCA7"] * 15 + ["SALL1"] * 15 + ["SELPLG"] * 15
    np.random.seed(42)
    np.random.shuffle(perturbations)
    
    obs = pd.DataFrame({"perturbation": perturbations})
    obs["perturbation"] = obs["perturbation"].astype("category")
    
    density = 0.1
    nnz = int(n_cells * n_genes * density)
    data = np.random.lognormal(mean=0.5, sigma=0.5, size=nnz).astype(np.float32)
    row_indices = np.random.choice(n_cells, size=nnz)
    col_indices = np.random.choice(n_genes, size=nnz)
    
    X = csr_matrix((data, (row_indices, col_indices)), shape=(n_cells, n_genes))
    var = pd.DataFrame(index=genes)
    
    adata = ad.AnnData(X=X, obs=obs, var=var)
    
    out_path = Path("data/raw/fake_k562.h5ad")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(out_path)
    print(f"Created fake perturb-seq file: {out_path} ({adata.n_obs} cells, {adata.n_vars} genes)")

if __name__ == "__main__":
    main()
