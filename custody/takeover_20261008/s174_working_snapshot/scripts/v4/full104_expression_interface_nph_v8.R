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
if (!(length(args) %in% c(6L,7L))) stop("usage: <project> <package> <selection.csv> <provenance.csv.gz> <collision-authority-dir> <outdir> [validate|materialize]")
mode <- if (length(args)==7L) args[[7]] else "materialize"
if (!(mode %in% c("validate","materialize"))) stop("invalid mode")
.libPaths(c(file.path(args[[1]],".r-library"),.libPaths()))
suppressPackageStartupMessages(library(Matrix));suppressPackageStartupMessages(library(qs));suppressPackageStartupMessages(library(SingleCellExperiment));suppressPackageStartupMessages(library(digest))
project <- normalizePath(args[[1]],mustWork=TRUE);package <- normalizePath(args[[2]],mustWork=TRUE)
selection <- read.csv(args[[3]],stringsAsFactors=FALSE);selection <- selection[selection$source=="NPH52",,drop=FALSE]
provenance <- read.csv(gzfile(args[[4]]),stringsAsFactors=FALSE)
collision <- read.csv(gzfile(file.path(args[[5]],"stage81a3r_expression_materialization_collision_ledger.csv.gz")),stringsAsFactors=FALSE)
supplemental <- read.csv(file.path(args[[5]],"stage81a3r_scalar_mapping_unregistered_collisions.csv"),stringsAsFactors=FALSE)
manifest <- read.csv(file.path(package,"NPH_READER_FIT_DERIVATIVE_MANIFEST.csv"),stringsAsFactors=FALSE)
deny <- read.csv(file.path(package,"ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv"),stringsAsFactors=FALSE)
outdir <- args[[6]];dir.create(outdir,recursive=TRUE,showWarnings=FALSE);validation_rows <- list()
package_key <- paste0(tolower(gsub("\\\\","/",package)),"/")
for (matrix_id in sort(unique(selection$matrix_id))) {
  requested <- selection[selection$matrix_id==matrix_id,,drop=FALSE]
  row <- manifest[manifest$matrix_id==matrix_id,,drop=FALSE]
  if (nrow(row)!=1L || row$reader_partition[[1]]!="reader_fit" || row$foundation_split[[1]]!="foundation/train") stop("fit-only derivative manifest mismatch")
  derivative <- normalizePath(file.path(package,row$derivative_relative_path[[1]]),mustWork=TRUE)
  derivative_key <- tolower(gsub("\\\\","/",derivative));derivative_sha <- digest(derivative,algo="sha256",file=TRUE)
  if (!startsWith(derivative_key,package_key)) stop("fit-only derivative escaped package")
  if (derivative_sha!=row$derivative_sha256[[1]] || file.info(derivative)$size!=row$derivative_size_bytes[[1]]) stop("fit-only derivative authentication failed")
  denied_paths <- tolower(gsub("\\\\","/",deny$canonical_original_path))
  if (derivative_key %in% denied_paths || derivative_sha %in% tolower(deny$original_sha256)) stop("original mixed NPH asset denied")
  validation_rows[[length(validation_rows)+1L]] <- data.frame(matrix_id=matrix_id,operator_index=unique(requested$operator_index),reader_partition="reader_fit",derivative_sha256=derivative_sha,path_inside_package=TRUE,original_path_and_hash_denied=TRUE,stringsAsFactors=FALSE)
  if (mode=="validate") next
  object <- qread(derivative)
  columns <- match(requested$canonical_cell_id,colnames(object))
  if (anyNA(columns)) stop("selected NPH cell absent from fit-only derivative")
  if (!identical(as.character(colData(object)$source_donor_id[columns]),as.character(requested$donor_id))) stop("NPH donor identity mismatch")
  object_name <- sub("^NPH52::matrix::","",matrix_id);source_id <- paste0("NPH52::",object_name)
  mapping <- provenance[provenance$source_dataset_id==source_id,c("source_feature_index","molecular_address_index"),drop=FALSE]
  blocked <- collision$source_feature_index[collision$matrix_id==matrix_id]
  extra <- supplemental[supplemental$matrix_id==matrix_id,,drop=FALSE]
  if (nrow(extra)) blocked <- c(blocked,as.integer(unlist(strsplit(extra$source_feature_indices,"[|]"))))
  mapping <- mapping[!(mapping$source_feature_index %in% blocked),,drop=FALSE]
  if (anyDuplicated(mapping$source_feature_index) || anyDuplicated(mapping$molecular_address_index)) stop("NPH noninjective address mapping")
  counts <- assay(object,"counts");libraries <- as.numeric(colSums(counts[,columns,drop=FALSE]));local <- t(counts[mapping$source_feature_index+1L,columns,drop=FALSE])
  if (length(local@x) && (any(local@x<0) || any(abs(local@x-round(local@x))>1e-8))) stop("NPH payload is not nonnegative integer raw counts")
  triplet <- summary(local);output <- sparseMatrix(i=triplet$i,j=mapping$molecular_address_index[triplet$j]+1L,x=triplet$x,dims=c(nrow(local),41238L),giveCsparse=TRUE)
  op <- unique(requested$operator_index);if (length(op)!=1L) stop("operator mismatch")
  stem <- file.path(outdir,sprintf("op%02d",op));writeMM(output,paste0(stem,".mtx"))
  write.csv(data.frame(selection_row=requested$selection_row,row_locator=requested$row_locator,canonical_cell_id=requested$canonical_cell_id,donor_id=requested$donor_id,derivative_column_index=columns-1L,source_library=libraries),paste0(stem,".meta.csv"),row.names=FALSE,quote=TRUE)
  rm(object,counts,local,output);gc(verbose=FALSE)
}
if (mode=="validate") write.csv(do.call(rbind,validation_rows),file.path(outdir,"NPH_FIT_ONLY_AUTHORITY_VALIDATION.csv"),row.names=FALSE,quote=TRUE)
