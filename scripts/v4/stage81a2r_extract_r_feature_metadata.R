#!/usr/bin/env Rscript

# Feature-identity bridge for downloaded R objects. This intentionally reads
# row metadata only after object deserialization; it never materializes assays.

suppressPackageStartupMessages(library(Matrix))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: stage81a2r_extract_r_feature_metadata.R PROJECT_DIR OUTPUT_DIR")
}

project <- normalizePath(args[[1L]], mustWork = TRUE)
output_dir <- args[[2L]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
manifest_path <- file.path(output_dir, "r_feature_cache_manifest.csv")
existing_manifest <- if (file.exists(manifest_path)) {
  utils::read.csv(manifest_path, stringsAsFactors = FALSE, check.names = FALSE)
} else {
  data.frame()
}

inputs <- c(
  "data/external/v4/perturbation/GSE301119/GSE301119_CRISPRa_seurat5.rds",
  "data/external/v4/perturbation/GSE301119/GSE301119_CRISPRi_seurat5.rds",
  "data/external/v4/stage81a3_context/LIBD_spatialDLPFC/spe_filtered_final_with_clusters_and_deconvolution_results.rds",
  "data/external/v4/stage81a3_context/spatialLIBD_classic_DLPFC/Human_DLPFC_Visium_processedData_sce_scran_spatialLIBD.Rdata",
  "data/external/v4/living_human/geo/GSE226602/GSE226602_rna_lognorm_expression.rds.gz",
  "data/external/v4/living_human/geo/GSE226602/GSE226602_rna_raw_counts.rds.gz",
  "data/external/v4/living_human/geo/GSE226267/GSE226267_atac_cd4_raw_peaks.rds.gz",
  "data/external/v4/living_human/geo/GSE226267/GSE226267_atac_noncd4_raw_peaks.rds.gz"
)
nph_root <- file.path(project, "data/processed/v4/stage81a1d/sealed/nph52_organized/organized_data/Human/brain/snRNA/NPH")
if (dir.exists(nph_root)) {
  nph_inputs <- sort(list.files(nph_root, pattern = "\\.qs$", full.names = TRUE))
  nph_inputs <- substring(normalizePath(nph_inputs), nchar(project) + 2L)
  inputs <- c(inputs, nph_inputs)
}

choose_matrix_object <- function(environment) {
  names <- sort(ls(environment, all.names = TRUE))
  objects <- lapply(names, function(name) get(name, envir = environment))
  dimensions <- lapply(objects, function(object) tryCatch(dim(object), error = function(error) NULL))
  eligible <- which(vapply(dimensions, function(value) length(value) == 2L, logical(1L)))
  if (!length(eligible)) stop("RData file contains no two-dimensional object")
  sizes <- vapply(dimensions[eligible], function(value) prod(as.numeric(value)), numeric(1L))
  objects[[eligible[[which.max(sizes)]]]]
}

load_object <- function(path) {
  if (grepl("\\.qs$", path, ignore.case = TRUE)) return(qs::qread(path))
  if (grepl("GSE226(?:267|602).*\\.rds\\.gz$", path, ignore.case = TRUE)) {
    outer <- gzfile(path, open = "rb")
    inner <- gzcon(outer)
    on.exit(close(inner), add = TRUE)
    return(readRDS(inner))
  }
  if (grepl("\\.rds\\.gz$", path, ignore.case = TRUE)) return(readRDS(gzfile(path, open = "rb")))
  if (grepl("\\.rds$", path, ignore.case = TRUE)) return(readRDS(path))
  environment <- new.env(parent = emptyenv())
  load(path, envir = environment)
  choose_matrix_object(environment)
}

row_metadata <- function(object, count) {
  result <- data.frame(row.names = seq_len(count))
  if (requireNamespace("SummarizedExperiment", quietly = TRUE) &&
      methods::is(object, "SummarizedExperiment")) {
    result <- as.data.frame(SummarizedExperiment::rowData(object), stringsAsFactors = FALSE)
  } else if (requireNamespace("SeuratObject", quietly = TRUE) &&
             inherits(object, "Seurat")) {
    assay <- SeuratObject::DefaultAssay(object)
    metadata <- tryCatch(object[[assay]][[]], error = function(error) NULL)
    if (!is.null(metadata) && nrow(metadata) == count) result <- as.data.frame(metadata)
  }
  result
}

pick_field <- function(metadata, patterns, count) {
  keys <- colnames(metadata)
  match <- keys[vapply(keys, function(key) {
    any(vapply(patterns, function(pattern) grepl(pattern, key, ignore.case = TRUE), logical(1L)))
  }, logical(1L))]
  if (!length(match)) return(rep("", count))
  as.character(metadata[[match[[1L]]]])
}

manifest <- list()
for (index in seq_along(inputs)) {
  relative <- inputs[[index]]
  path <- file.path(project, relative)
  if (!file.exists(path)) next
  existing <- existing_manifest[existing_manifest$source_local_path == relative, , drop = FALSE]
  if (nrow(existing) == 1L) {
    cached <- existing$cache_path[[1L]]
    cache_path <- if (startsWith(cached, "/")) cached else file.path(project, cached)
    if (file.exists(cache_path)) {
      message(sprintf("R feature metadata %d/%d: reusing %s", index, length(inputs), basename(cache_path)))
      manifest[[length(manifest) + 1L]] <- existing
      next
    }
  }
  message(sprintf("R feature metadata %d/%d: %s", index, length(inputs), basename(path)))
  object <- load_object(path)
  feature_ids <- rownames(object)
  if (is.null(feature_ids)) stop(sprintf("Missing row identities: %s", relative))
  metadata <- row_metadata(object, length(feature_ids))
  ensembl <- pick_field(metadata, c("ensembl", "gene_id", "geneid"), length(feature_ids))
  symbol <- pick_field(metadata, c("symbol", "gene_name", "genename"), length(feature_ids))
  refseq <- pick_field(metadata, c("refseq"), length(feature_ids))
  ncbi_gene <- pick_field(metadata, c("entrez", "ncbi_gene"), length(feature_ids))
  transcript <- pick_field(metadata, c("transcript_id", "transcriptid"), length(feature_ids))
  chromosome <- pick_field(metadata, c("anno_seqnames", "chromosome", "seqname"), length(feature_ids))
  start <- pick_field(metadata, c("anno_start", "^start$"), length(feature_ids))
  end <- pick_field(metadata, c("anno_end", "^end$"), length(feature_ids))
  strand <- pick_field(metadata, c("anno_strand", "^strand$"), length(feature_ids))
  biotype <- pick_field(metadata, c("gene_biotype", "feature_biotype", "biotype"), length(feature_ids))
  ensembl[is.na(ensembl)] <- ""
  symbol[is.na(symbol)] <- ""
  ensembl_from_index <- grepl("^ENSG[0-9]+(?:\\.[0-9]+)?$", feature_ids)
  ensembl[ensembl == "" & ensembl_from_index] <- feature_ids[ensembl == "" & ensembl_from_index]
  symbol[symbol == "" & !ensembl_from_index] <- feature_ids[symbol == "" & !ensembl_from_index]
  frame <- data.frame(
    source_feature_index = seq_along(feature_ids) - 1L,
    raw_feature_id = feature_ids,
    raw_gene_symbol = symbol,
    source_ensembl_id = ensembl,
    source_feature_type = if (grepl("atac", relative, ignore.case = TRUE)) "ATAC peak" else "Gene Expression",
    source_refseq_id = refseq,
    source_ncbi_gene_id = ncbi_gene,
    source_transcript_id = transcript,
    source_chromosome = chromosome,
    source_start = start,
    source_end = end,
    source_strand = strand,
    source_biotype = biotype,
    stringsAsFactors = FALSE,
    check.names = FALSE
  )
  cache_name <- paste0(gsub("[^A-Za-z0-9._-]", "_", basename(path)), ".features.tsv.gz")
  cache_path <- file.path(output_dir, cache_name)
  temporary <- paste0(cache_path, ".tmp")
  connection <- gzfile(temporary, open = "wt")
  utils::write.table(frame, connection, sep = "\t", quote = TRUE, row.names = FALSE, na = "")
  close(connection)
  if (!file.rename(temporary, cache_path)) stop(sprintf("Could not finalize %s", cache_path))
  manifest[[length(manifest) + 1L]] <- data.frame(
    source_local_path = relative,
    cache_path = substring(normalizePath(cache_path, winslash = "/", mustWork = TRUE), nchar(project) + 2L),
    feature_count = nrow(frame),
    raw_ids_unique = !anyDuplicated(feature_ids),
    feature_metadata_fields = paste(colnames(metadata), collapse = "|"),
    expression_matrix_materialized = FALSE,
    stringsAsFactors = FALSE
  )
  rm(object, metadata, frame)
  gc(verbose = FALSE)
}

manifest_frame <- do.call(rbind, manifest)
temporary <- paste0(manifest_path, ".tmp")
utils::write.csv(manifest_frame, temporary, row.names = FALSE, na = "")
if (!file.rename(temporary, manifest_path)) stop("Could not finalize R feature cache manifest")
cat(sprintf("Wrote: %s\n", manifest_path))
