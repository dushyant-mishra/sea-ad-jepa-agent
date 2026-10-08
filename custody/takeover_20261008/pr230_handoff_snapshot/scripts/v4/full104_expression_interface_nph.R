#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly=TRUE)
parse_authority_bool <- function(x) {
  key <- tolower(trimws(as.character(x)))
  if (length(key) != 1L || !(key %in% c("true","false"))) stop("invalid Boolean authority value")
  identical(key,"true")
}
if (length(args) >= 1L && identical(args[[1]],"--selftest")) {
  if (length(args) != 2L) stop("usage: --selftest <output.csv>")
  inputs <- c("True","TRUE"," true ","False","FALSE"," false ")
  parsed <- vapply(inputs,parse_authority_bool,logical(1))
  invalid_rejected <- tryCatch({parse_authority_bool("not-a-boolean");FALSE},error=function(e) TRUE)
  if (!identical(unname(parsed),c(TRUE,TRUE,TRUE,FALSE,FALSE,FALSE)) || !isTRUE(invalid_rejected)) stop("Boolean self-test failed")
  write.csv(data.frame(input=inputs,parsed=parsed,invalid_rejected=rep(invalid_rejected,length(inputs))),args[[2]],row.names=FALSE,quote=TRUE)
  quit(save="no",status=0L)
}
if (!(length(args) %in% c(5L,6L))) stop("usage: <project> <selection.csv> <provenance.csv.gz> <collision-authority-dir> <outdir> [validate|materialize]")
mode <- if (length(args) == 6L) args[[6]] else "materialize"
if (!(mode %in% c("validate","materialize"))) stop("invalid mode")
.libPaths(c(file.path(args[[1]], ".r-library"), .libPaths()))
suppressPackageStartupMessages(library(Matrix)); suppressPackageStartupMessages(library(qs)); suppressPackageStartupMessages(library(SingleCellExperiment))
project <- normalizePath(args[[1]], mustWork=TRUE); selection <- read.csv(args[[2]], stringsAsFactors=FALSE)
selection <- selection[selection$source == "NPH52",,drop=FALSE]; provenance <- read.csv(gzfile(args[[3]]), stringsAsFactors=FALSE)
collision <- read.csv(gzfile(file.path(args[[4]],"stage81a3r_expression_materialization_collision_ledger.csv.gz")), stringsAsFactors=FALSE)
supplemental <- read.csv(file.path(args[[4]],"stage81a3r_scalar_mapping_unregistered_collisions.csv"), stringsAsFactors=FALSE)
exact <- read.csv(file.path(project,"data/processed/v4/stage81a2r/nph52_physical_split/nph52_physical_split_exactness_manifest.csv"), stringsAsFactors=FALSE)
outdir <- args[[5]]; dir.create(outdir, recursive=TRUE, showWarnings=FALSE)
validation_rows <- list()
for (matrix_id in sort(unique(selection$matrix_id))) {
  requested <- selection[selection$matrix_id == matrix_id,,drop=FALSE]
  object_name <- sub("^NPH52::matrix::","",matrix_id)
  row <- exact[exact$source_object_id == object_name & exact$partition == "TRAIN",,drop=FALSE]
  if (nrow(row) != 1L) stop("NPH TRAIN derivative authority row is not unique")
  exact_pass <- parse_authority_bool(row$exact_lossless_subset_pass[[1]])
  if (!isTRUE(exact_pass)) stop("NPH TRAIN derivative exactness authority is not true")
  authority_path <- as.character(row$derivative_path[[1]])
  authority_prefix <- "/mnt/d/Jepa project/"
  if (!startsWith(authority_path, authority_prefix)) stop("NPH derivative authority path is outside the canonical project prefix")
  derivative_relative <- substring(authority_path, nchar(authority_prefix)+1L)
  derivative <- normalizePath(file.path(project, derivative_relative), mustWork=TRUE)
  project_key <- paste0(tolower(gsub("\\\\","/",project)),"/")
  derivative_key <- tolower(gsub("\\\\","/",derivative))
  if (!startsWith(derivative_key, project_key)) stop("resolved NPH derivative escaped the canonical project")
  validation_rows[[length(validation_rows)+1L]] <- data.frame(matrix_id=matrix_id,source_object_id=object_name,partition="TRAIN",exact_lossless_subset_pass=exact_pass,derivative_relative=derivative_relative,resolved_derivative=derivative,path_exists=file.exists(derivative),stringsAsFactors=FALSE)
  if (mode == "validate") next
  object <- qread(derivative); columns <- match(requested$canonical_cell_id,colnames(object))
  if (anyNA(columns)) stop(paste("missing selected NPH cell",object_name))
  if (!identical(as.character(colData(object)$source_donor_id[columns]),as.character(requested$donor_id))) stop("NPH donor identity mismatch")
  source_id <- paste0("NPH52::",object_name)
  mapping <- provenance[provenance$source_dataset_id == source_id,c("source_feature_index","molecular_address_index"),drop=FALSE]
  blocked <- collision$source_feature_index[collision$matrix_id == matrix_id]
  extra <- supplemental[supplemental$matrix_id == matrix_id,,drop=FALSE]
  if (nrow(extra)) blocked <- c(blocked,as.integer(unlist(strsplit(extra$source_feature_indices,"[|]"))))
  mapping <- mapping[!(mapping$source_feature_index %in% blocked),,drop=FALSE]
  if (anyDuplicated(mapping$source_feature_index) || anyDuplicated(mapping$molecular_address_index)) stop("NPH noninjective address mapping")
  counts <- assay(object,"counts"); libraries <- as.numeric(colSums(counts[,columns,drop=FALSE]))
  local <- t(counts[mapping$source_feature_index+1L,columns,drop=FALSE])
  if (length(local@x) && (any(local@x < 0) || any(abs(local@x-round(local@x)) > 1e-8))) stop("NPH payload is not nonnegative integer raw counts")
  triplet <- summary(local)
  output <- sparseMatrix(i=triplet$i,j=mapping$molecular_address_index[triplet$j]+1L,x=triplet$x,dims=c(nrow(local),41238L),giveCsparse=TRUE)
  op <- unique(requested$operator_index); if (length(op) != 1L) stop("operator mismatch")
  stem <- file.path(outdir,sprintf("op%02d",op)); writeMM(output,paste0(stem,".mtx"))
  write.csv(data.frame(selection_row=requested$selection_row,row_locator=requested$row_locator,canonical_cell_id=requested$canonical_cell_id,donor_id=requested$donor_id,derivative_column_index=columns-1L,source_library=libraries),paste0(stem,".meta.csv"),row.names=FALSE,quote=TRUE)
  rm(object,counts,local,output); gc(verbose=FALSE)
}
if (mode == "validate") {
  validation <- do.call(rbind,validation_rows)
  write.csv(validation,file.path(outdir,"NPH_AUTHORITY_PATH_VALIDATION.csv"),row.names=FALSE,quote=TRUE)
}
