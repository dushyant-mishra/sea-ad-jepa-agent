args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 6L) stop("usage: <project> <package> <selection.csv.gz> <provenance.csv.gz> <collision-authority-dir> <outdir>")
.libPaths(c(file.path(args[[1]],".r-library"),.libPaths()))
suppressPackageStartupMessages(library(Matrix))
suppressPackageStartupMessages(library(qs))
suppressPackageStartupMessages(library(SingleCellExperiment))
suppressPackageStartupMessages(library(digest))

project <- normalizePath(args[[1]],mustWork=TRUE)
package <- normalizePath(args[[2]],mustWork=TRUE)
selection <- read.csv(gzfile(args[[3]]),stringsAsFactors=FALSE)
selection <- selection[selection$source == "NPH52",,drop=FALSE]
provenance <- read.csv(gzfile(args[[4]]),stringsAsFactors=FALSE)
collision <- read.csv(gzfile(file.path(args[[5]],"stage81a3r_expression_materialization_collision_ledger.csv.gz")),stringsAsFactors=FALSE)
supplemental <- read.csv(file.path(args[[5]],"stage81a3r_scalar_mapping_unregistered_collisions.csv"),stringsAsFactors=FALSE)
manifest <- read.csv(file.path(package,"NPH_READER_FIT_DERIVATIVE_MANIFEST.csv"),stringsAsFactors=FALSE)
deny <- read.csv(file.path(package,"ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv"),stringsAsFactors=FALSE)
outdir <- args[[6]]
dir.create(outdir,recursive=TRUE,showWarnings=FALSE)
block_size <- 512L
package_key <- paste0(tolower(gsub("\\\\","/",package)),"/")

for (matrix_id in sort(unique(selection$matrix_id))) {
  requested <- selection[selection$matrix_id == matrix_id,,drop=FALSE]
  requested <- requested[order(requested$selection_row),,drop=FALSE]
  row <- manifest[manifest$matrix_id == matrix_id,,drop=FALSE]
  if (nrow(row) != 1L || row$reader_partition[[1]] != "reader_fit" || row$foundation_split[[1]] != "foundation/train") stop("fit-only derivative manifest mismatch")
  derivative <- normalizePath(file.path(package,row$derivative_relative_path[[1]]),mustWork=TRUE)
  derivative_key <- tolower(gsub("\\\\","/",derivative))
  derivative_sha <- digest(derivative,algo="sha256",file=TRUE)
  if (!startsWith(derivative_key,package_key) || derivative_sha != row$derivative_sha256[[1]] || file.info(derivative)$size != row$derivative_size_bytes[[1]]) stop("fit-only derivative authentication failed")
  if (derivative_key %in% tolower(gsub("\\\\","/",deny$canonical_original_path)) || derivative_sha %in% tolower(deny$original_sha256)) stop("original mixed NPH asset denied")
  object <- qread(derivative)
  columns <- match(requested$canonical_cell_id,colnames(object))
  if (anyNA(columns) || !identical(as.character(colData(object)$source_donor_id[columns]),as.character(requested$donor_id))) stop("NPH identity mismatch")
  object_name <- sub("^NPH52::matrix::","",matrix_id)
  source_id <- paste0("NPH52::",object_name)
  mapping <- provenance[provenance$source_dataset_id == source_id,c("source_feature_index","molecular_address_index"),drop=FALSE]
  blocked <- collision$source_feature_index[collision$matrix_id == matrix_id]
  extra <- supplemental[supplemental$matrix_id == matrix_id,,drop=FALSE]
  if (nrow(extra)) blocked <- c(blocked,as.integer(unlist(strsplit(extra$source_feature_indices,"[|]"))))
  mapping <- mapping[!(mapping$source_feature_index %in% blocked),,drop=FALSE]
  if (anyDuplicated(mapping$source_feature_index) || anyDuplicated(mapping$molecular_address_index)) stop("NPH noninjective address mapping")
  counts <- assay(object,"counts")
  libraries <- as.numeric(Matrix::colSums(counts[,columns,drop=FALSE]))
  op <- unique(requested$operator_index)
  if (length(op) != 1L) stop("operator mismatch")
  opdir <- file.path(outdir,sprintf("op%02d",op))
  dir.create(opdir,recursive=TRUE,showWarnings=FALSE)
  starts <- seq.int(1L,nrow(requested),by=block_size)
  for (block_index in seq_along(starts)) {
    begin <- starts[[block_index]]
    end <- min(nrow(requested),begin+block_size-1L)
    take <- begin:end
    local <- t(counts[mapping$source_feature_index+1L,columns[take],drop=FALSE])
    triplet <- summary(local)
    output <- sparseMatrix(i=triplet$i,j=mapping$molecular_address_index[triplet$j]+1L,x=triplet$x,dims=c(length(take),41238L),giveCsparse=TRUE)
    stem <- file.path(opdir,sprintf("block-%05d",block_index-1L))
    writeMM(output,paste0(stem,".mtx"))
    write.csv(data.frame(selection_row=requested$selection_row[take],canonical_cell_id=requested$canonical_cell_id[take],donor_id=requested$donor_id[take],expression_row=columns[take]-1L,source_library=libraries[take]),paste0(stem,".meta.csv"),row.names=FALSE,quote=TRUE)
    rm(local,triplet,output)
    gc(verbose=FALSE)
  }
  rm(object,counts)
  gc(verbose=FALSE)
  cat(sprintf("NPH op%02d cells=%d blocks=%d\n",op,nrow(requested),length(starts)))
}
