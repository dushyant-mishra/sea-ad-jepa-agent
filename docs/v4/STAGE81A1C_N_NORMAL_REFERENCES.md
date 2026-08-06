# Stage81A1C-N Normal Human-Brain References

Stage81A1C-N acquires processed normal human-brain references without training
a model, freezing genes or donors, reading SEA-AD pathology values, or creating
a physically merged atlas.

## Roles

The Siletti Human Brain Cell Atlas v1.0 study is reserved in full from v4
training and model selection. Its official CELLxGENE `All non-neuronal cells`
partition is acquired as the relevant clean normal holdout. Other partitions
from that study are not training candidates. The official microglia
supercluster is cataloged but not downloaded because it is a duplicate subset
of the acquired partition.

GSE97930 is an independent adult human-brain regional training-reference
candidate. Its three processed snDrop-seq UMI matrices cover frontal cortex,
visual cortex and cerebellar hemisphere. Their missing explicit cell-to-donor
mapping is retained as a limitation and must be resolved before any donor split.

The old 10,000-cell mixed CELLxGENE anchor is not promoted into v4. It samples
38 datasets and includes non-adult developmental stages. It is audited only to
identify exact overlap and is classified `excluded_incompatible`.

## Run

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1c_n_acquire_normal_references.py --mode all
```

Downloads are resumable through `.part` files. Promotion requires exact byte
count and format validation. SHA-256 is bound to repository-relative path,
size, modification time, format-open result and verification schema.

There is no fixed Stage81A1C-N download-volume cap. The script still preserves
the project safety reserve, avoids redundant data, and downloads processed
matrices and compact documentation only.

## Claim boundary

Normal labels and adult ontology fields establish a reference contract, not a
biological baseline truth for every donor or region. No pathology classifier,
regulatory model, perturbation model, final JEPA matrix or validation claim is
created here.
