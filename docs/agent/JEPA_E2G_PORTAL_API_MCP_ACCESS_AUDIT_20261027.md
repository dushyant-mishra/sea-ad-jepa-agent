# E2G Portal API, MCP and bulk-data access audit — 2026-10-27

**Scope:** public access path discovery for draft PR #457 only. No real enhancer predictions downloaded, no Google Cloud billing project used, no target discovery or training authority.

## Source control and provenance

Verified the public E2G portal frontend:
- Repository: `kundajelab/e2g-frontend`, `main@886f02865c1b23da8ff7e6d84ddee5688d6104b1`.
- E2G bulk schema: `apps/platform/src/pages/E2GDownloadsPage/E2GDownloadsPage.tsx` blob `5be9e8b10d7b556a3e0fbe1fcfebcd7d4d4c990d`.
- Dedicated portal GraphQL query: `apps/platform/src/pages/IGVPage/DataTracks.gql` blob `b8683247f5c7b3c5882bc6299e1f21d5fb2faf97`.
- Per-variant E2G query: `packages/sections/src/variant/E2GPredictions/E2GQuery.gql` blob `b9a6c9900fb5caa7ba1b2c7e76c4c1dace39f632`.
- Reverse proxy: `nginx.app.conf` blob `92d7f01a237f3c4d7fa1a6d0825fae0704a12830` maps POST `/graphql` to a backend service on internal port 4000 and `/api/` to REST service.
- The application maps `/api` to an interactive **API page** (React route), distinct from REST requests at `/api/*`; `/downloads` maps to its E2G-specific download page.

Website: https://e2g.stanford.edu/
Source: https://github.com/kundajelab/e2g-frontend

## Access channel 1 — dedicated E2G portal GraphQL

Source code specifies `https://e2g.stanford.edu/graphql` as an expected same-origin API entrypoint. The client uses the documented query:

```graphql
query DataTracksTable {
  getDataTracks {
    id
    cellTypeId
    cellType
    study
    studyId
    dataset
    datasetUrl
    e2gPredictionsUrl
    modelType
  }
}
```

It also specifies a per-variant query `variant(variantId: String!)` returning
`enhancerGenePredictions` with `score`, `model`, `dataset`,
`cellType`, `targetGene { id symbol }`, enhancer start/end,
enhancer-to-gene distance, and associated browser track metadata.

**Evidence boundary:** this is a query-interface verified from client source, NOT
a live production endpoint success receipt. The in-chat web fetch cannot
POST to this endpoint and GET attempts were inaccessible in that client;
do not claim the server returned data. A tiny, metadata-only external
probe is proposed below.

## Access channel 2 — Open Targets MCP

Official documentation: https://platform-docs.opentargets.org/data-access/model-context-protocol
Hosted service: `https://mcp.platform.opentargets.org/mcp`
Source: https://github.com/opentargets/platform-mcp

The official Open Targets MCP defaults to its own GraphQL service
`https://api.platform.opentargets.org/api/v4/graphql`.
E2G portal `/api` page links to this MCP. **That does not establish that Open
Targets MCP exposes the E2G portal's custom `getDataTracks` or
`enhancerGenePredictions` schema.** No direct E2G MCP endpoint has been
verified. An ordinary Open Targets MCP connection is useful for
gene/disease/variant evidence, not a replacement for querying the E2G backend.

No Open Targets-specific connected ChatGPT plugin was discovered in the
current plugin search. We have **not** connected an external MCP server.

## Access channel 3 — E2G bulk data: requester-pays, NOT anonymous

The E2G page publishes **three Apache Parquet datasets** in `gs://e2g`:

| Dataset | GCS object/path | Source page count | Relevant columns |
| --- | --- | --- | --- |
| Enhancer–Gene Predictions | `gs://e2g/enhancer_gene_predictions/` | 125M rows (page label) | `score,target_gene_id,target_gene_name,target_gene_tss,enhancer_gene_distance,model,chromosome,enhancer_id,cell_type_id` |
| Enhancers | `gs://e2g/enhancers.parquet` | 59.8M rows (page label) | `id,chromosome,start,end,class` (GRCh38) |
| Cell Types | `gs://e2g/cell_types.parquet` | 1,604 rows (page label) | `id,name,dataset,dataset_url` |

**Critical:** this is a **requester-pays** bucket. Anonymous HTTPS downloads
are not supported. Using `gcloud storage cp` requires an *authorized,
user-owned Google Cloud billing project*, and may incur network/egress
charges. No transfer or new billing project is authorized by this audit.

The page documents these *example* commands, **NOT RUN**:

```bash
gcloud storage cp --billing-project=YOUR_PROJECT gs://e2g/cell_types.parquet .
gcloud storage cp -r --billing-project=YOUR_PROJECT gs://e2g/enhancer_gene_predictions/ ./enhancer_gene_predictions/
```

Never run the full recursive transfer as the first exploratory step.
First restrict to a **small, approved scope**, estimate costs, and snapshot
a bound object manifest. The `cell_types.parquet` metadata is the correct
initial filter for adult brain microglia and other relevant myeloid contexts.
The 125M figure is the current *portal page label* across model families,
not a recomputed record count and not proof of validated biology.

## Next-step programmatic probe (bounded, non-billable)

A single read-only POST for `__typename`, then a single read-only
`getDataTracks {cellTypeId cellType study dataset modelType}` metadata
query, may establish whether the custom GraphQL endpoint is currently
live. No sample raw/genomic files, browser URLs or predictions need be downloaded.
Never infer absence of a biosample from a transport error.

After a positive live response, list only microglia/macrophage/myeloid/
blood/brain-related cell-type labels, inspect study/dataset provenance
and model-family overlap. Do **not** infer independent validation from
a cell-type name alone. Unrelated blood or developmental cells remain
context-only. Require an explicit source audit before any application
to the frozen 96 Stage75 TF→gene candidates.

## Consequence for PR #457

The older compatibility file marked the rE2G atlas as a reference candidate;
that remains correct, but the portal explicitly publishes a **queryable
GraphQL interface and three bulk Parquet tables**. This changes the
accessibility strategy, **not** biological/scientific authorization.
Treat gene-only annotation overlaps as **annotation only**. A genuine
enhancer→gene prediction linked to a target is not evidence of a specific
TF→gene causal relation.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
