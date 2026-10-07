#!/usr/bin/env Rscript
# Materialize only frozen NPH discovery rows into collision-safe 41,238-address shards.
args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 4L) stop("usage: <project> <freeze.csv> <collision-authority> <outdir>")
.libPaths(c(file.path(args[[1]], ".r-library"), .libPaths()))
suppressPackageStartupMessages(library(Matrix)); suppressPackageStartupMessages(library(qs)); suppressPackageStartupMessages(library(SingleCellExperiment))
project <- normalizePath(args[[1]], mustWork=TRUE); freeze_path <- normalizePath(args[[2]], mustWork=TRUE)
authority <- normalizePath(args[[3]], mustWork=TRUE); outdir <- normalizePath(args[[4]], mustWork=FALSE); dir.create(outdir, recursive=TRUE, showWarnings=FALSE)
manifest <- read.csv(freeze_path, stringsAsFactors=FALSE, colClasses=c(stable_key="character")); manifest <- manifest[manifest$source == "NPH52",,drop=FALSE]
provenance <- read.csv(gzfile(file.path(project,"results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz")), stringsAsFactors=FALSE)
collision <- read.csv(gzfile(file.path(authority,"results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz")), stringsAsFactors=FALSE)
supplemental <- read.csv(file.path(authority,"results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv"), stringsAsFactors=FALSE)
for (matrix_id in sort(unique(manifest$matrix_id))) {
  requested <- manifest[manifest$matrix_id == matrix_id,,drop=FALSE]; object_name <- sub("^NPH52::matrix::","",matrix_id)
  derivative <- file.path(project,"data/processed/v4/stage81a2r/nph52_physical_split/TRAIN",sub("[.]qs$",".TRAIN.full_features.qs",object_name))
  object <- qread(derivative); columns <- match(requested$cell_id,colnames(object)); if (anyNA(columns)) stop(paste("missing frozen cells",object_name))
  if (!identical(as.character(colData(object)$source_donor_id[columns]),as.character(requested$donor_id))) stop("NPH donor identity mismatch")
  source_id <- paste0("NPH52::",object_name); mapping <- provenance[provenance$source_dataset_id == source_id,c("source_feature_index","molecular_address_index"),drop=FALSE]
  blocked <- collision$source_feature_index[collision$matrix_id == matrix_id]
  extra <- supplemental[supplemental$matrix_id == matrix_id,,drop=FALSE]
  if (nrow(extra)) blocked <- c(blocked,as.integer(unlist(strsplit(extra$source_feature_indices,"[|]"))))
  mapping <- mapping[!(mapping$source_feature_index %in% blocked),,drop=FALSE]
  if (anyDuplicated(mapping$source_feature_index) || anyDuplicated(mapping$molecular_address_index)) stop("NPH noninjective mapping")
  source_counts <- assay(object,"counts"); libraries <- as.numeric(colSums(source_counts[,columns,drop=FALSE]))
  local <- t(source_counts[mapping$source_feature_index+1L,columns,drop=FALSE]); triplet <- summary(local)
  output <- sparseMatrix(i=triplet$i,j=mapping$molecular_address_index[triplet$j]+1L,x=triplet$x,dims=c(nrow(local),41238L),giveCsparse=TRUE)
  stem <- sprintf("op%02d",unique(requested$operator_index))
  writeMM(output,file.path(outdir,paste0(stem,".mtx")))
  write.csv(data.frame(stable_key=requested$stable_key,cell_id=requested$cell_id,donor_id=requested$donor_id,source_library=libraries),file.path(outdir,paste0(stem,".meta.csv")),row.names=FALSE,quote=TRUE)
  message(sprintf("NPH discovery shard %s cells=%d nnz=%d",object_name,nrow(output),nnzero(output)))
  rm(object,source_counts,local,output); gc(verbose=FALSE)
}
