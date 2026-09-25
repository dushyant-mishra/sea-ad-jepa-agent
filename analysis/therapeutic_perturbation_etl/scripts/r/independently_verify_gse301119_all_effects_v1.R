#!/usr/bin/env Rscript
# Independent DEVELOPMENT-only reproduction of all GSE301119 donor-aware log2FC
# matrices from SHA-bound raw guide x donor pseudobulk. No original producer import.
# Biological unit DONOR (n=2); NEVER population SE or validation authority.
EXPECTED <- list(
 CRISPRi=list(raw="e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549",
              matrix="7f550f436333cf6159f54ff7b3221617952fcc13ac2b9d68c4cf572d53b39e43",
              targets=206L,eligible=204L,genes=36601L),
 CRISPRa=list(raw="9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90",
              matrix="474202c0705a57bdc939ce483fe7612d9082fb57d80d94eefd8bd3d3c509ba93",
              targets=206L,eligible=198L,genes=19162L)
)
MIN_CELLS <- 10L
TOLERANCE <- 1e-9
stop_if <- function(condition, reason) if (isTRUE(condition)) stop(reason, call.=FALSE)
sha256_file <- function(path) {
  stop_if(!requireNamespace("digest",quietly=TRUE), "STOP_DIGEST_DEPENDENCY_MISSING")
  digest::digest(file=path, algo="sha256")
}
assert_raw_metadata <- function(raw) {
  stop_if(!identical(raw$schema,"GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1"),
          "STOP_RAW_PSEUDOBULK_SCHEMA")
  X <- raw$counts
  m <- raw$gd_meta
  genes <- as.character(raw$features)
  stop_if(is.null(dim(X)) || nrow(X)!=length(genes) || ncol(X)!=nrow(m),
          "STOP_RAW_MATRIX_GEOMETRY")
  stop_if(anyDuplicated(genes)>0L || !identical(rownames(X),genes),
          "STOP_RAW_GENE_ORDER_OR_DUPLICATE")
  required <- c("guide_donor","guide_identity","donor","Gene_Targeted","crispr","n_cells")
  stop_if(!all(required %in% names(m)), "STOP_MISSING_GUIDE_DONOR_COLUMNS")
  stop_if(anyDuplicated(as.character(m$guide_donor))>0L ||
          !identical(colnames(X),as.character(m$guide_donor)),
          "STOP_RAW_MATRIX_METADATA_COLUMN_ALIGNMENT")
  stop_if(!setequal(as.character(unique(m$donor)),c("D1","D2")),
          "STOP_RAW_DONOR_SET")
  stop_if(any(is.na(m$n_cells)) || any(!is.finite(m$n_cells)) ||
          any(m$n_cells<=0) || any(m$n_cells!=floor(m$n_cells)),
          "STOP_BAD_GROUP_CELL_SUPPORT")
  stop_if(any(paste0(m$guide_identity,"||",m$donor)!=m$guide_donor),
          "STOP_GUIDE_DONOR_COMPOSITE_JOIN")
  stop_if(any(is.na(m$crispr)) || !all(m$crispr %in% c("NT","Perturbed")),
          "STOP_RAW_CONTROL_ROLE")
  for (donor in c("D1","D2")) {
    stop_if(!any(m$donor==donor & m$crispr=="NT"),"STOP_MISSING_DONOR_NT")
  }
  # Matrix package is needed only to read the actual sparse RDS; dense synthetic
  # controls use base matrix. Never densify the real 36k x 2k matrix.
  vals <- if (inherits(X,"sparseMatrix")) X@x else as.vector(X)
  stop_if(any(!is.finite(vals)) || any(vals<0) ||
          any(vals!=floor(vals)) || any(vals>2^53-1),
          "STOP_NONINTEGER_OR_NONFINITE_RAW_COUNTS")
  stop_if(anyNA(genes) || any(genes==""), "STOP_BLANK_GENE_ID")
  guide_roles <- unique(data.frame(guide=as.character(m$guide_identity),
                                   role=as.character(m$crispr),
                                   target=as.character(m$Gene_Targeted)))
  stop_if(anyDuplicated(guide_roles$guide)>0L,"STOP_GUIDE_TARGET_ROLE_DRIFT")
  invisible(TRUE)
}
normalize_from_raw <- function(X, indices) {
  stop_if(length(indices)==0L,"STOP_MISSING_GROUP")
  total <- rowSums(X[,indices,drop=FALSE])
  lib <- sum(total)
  stop_if(!is.finite(lib) || lib<=0 || lib>2^53-1,
          "STOP_ZERO_OR_NONEXACT_LIBRARY_DEPTH")
  log2(1+as.numeric(total)*1e6/lib)
}
independent_target <- function(raw, target, min_cells=MIN_CELLS) {
  m <- raw$gd_meta; X <- raw$counts
  donors <- c("D1","D2")
  result <- list()
  cells <- integer(2L);names(cells)<-donors
  for (d in donors) {
    nt <- which(m$donor==d & m$crispr=="NT")
    tr <- which(m$donor==d & m$crispr=="Perturbed" & m$Gene_Targeted==target)
    stop_if(!length(nt),"STOP_MISSING_DONOR_NT")
    ctrl <- normalize_from_raw(X,nt)
    cells[d] <- if (length(tr)) as.integer(sum(m$n_cells[tr])) else 0L
    if (cells[d] < min_cells) next
    result[[d]] <- normalize_from_raw(X,tr)-ctrl
  }
  mean <- if (length(result)==2L) (result[["D1"]]+result[["D2"]])/2
          else rep(NA_real_,nrow(X))
  list(mean=mean,by_donor=result,cells=cells,eligible=length(result)==2L)
}
reproduce_one <- function(mod,raw_file,matrix_file,expected=EXPECTED[[mod]]) {
  stop_if(is.null(expected),"STOP_UNKNOWN_INTERVENTION")
  stop_if(sha256_file(raw_file)!=expected$raw,"STOP_RAW_PSEUDOBULK_SHA")
  stop_if(sha256_file(matrix_file)!=expected$matrix,"STOP_PRODUCED_MATRIX_SHA")
  raw<-readRDS(raw_file); ref<-readRDS(matrix_file)
  assert_raw_metadata(raw)
  targets<-sort(unique(as.character(raw$gd_meta$Gene_Targeted[
                  raw$gd_meta$crispr=="Perturbed"])))
  stop_if(length(targets)!=expected$targets ||
          length(raw$features)!=expected$genes,"STOP_MODALITY_CENSUS")
  stop_if(!identical(ref$schema,"GSE301119_DONOR_AWARE_LOG2FC_V1") ||
          !identical(ref$modality,mod) ||
          !identical(as.character(ref$features),as.character(raw$features)) ||
          !identical(as.character(ref$targets),targets),
          "STOP_OUTPUT_FEATURE_OR_TARGET_IDENTITY")
  X<-ref$log2fc
  stop_if(!is.matrix(X) || !identical(dim(X),c(length(raw$features),length(targets))) ||
          !identical(rownames(X),as.character(raw$features)) ||
          !identical(colnames(X),targets),"STOP_OUTPUT_MATRIX_ORDER")
  finite_count<-0L; eligible<-0L; max_delta<-0
  for (tg in targets) {
    x<-independent_target(raw,tg)
    if (x$eligible) eligible<-eligible+1L
    a<-x$mean;b<-X[,tg]
    if (!identical(unname(is.na(a)),unname(is.na(b))))
      stop("STOP_OUTPUT_MISSINGNESS_MISMATCH:",mod,":",tg,call.=FALSE)
    both<-is.finite(a)&is.finite(b)
    stop_if(any(is.infinite(b)) || any(is.nan(b)),
            "STOP_OUTPUT_NONFINITE")
    if (any(both)) {
      delta<-max(abs(a[both]-b[both]))
      max_delta<-max(max_delta,delta)
      finite_count<-finite_count+sum(both)
      if (delta>TOLERANCE)
        stop("STOP_INDEPENDENT_EFFECT_MISMATCH:",mod,":",tg,
             ":max_delta=",format(delta,digits=15),call.=FALSE)
    }
  }
  stop_if(eligible!=expected$eligible,"STOP_DECLARED_TARGET_SUPPORT_DRIFT")
  # Independently recompute modality-wide observed gene detection, not just FC.
  mask<-rowSums(raw$counts[,which(raw$gd_meta$crispr=="Perturbed"),drop=FALSE])>0
  stop_if(!identical(as.logical(ref$gene_detected_in_perturbed),as.logical(mask)),
          "STOP_ASSAY_DETECTION_MASK_MISMATCH")
  list(modality=mod,raw_sha256=expected$raw,matrix_sha256=expected$matrix,
       targets=length(targets),eligible_targets=eligible,
       compared_finite_effects=finite_count,max_abs_delta=max_delta,
       tolerance=TOLERANCE,source_feature_count=length(raw$features),
       confirmed_identical_missingness=TRUE,
       confirmed_gene_detection_mask=TRUE,
       independent_effect_reproduction="PASS")
}
main<-function() {
  args<-commandArgs(trailingOnly=TRUE)
  getarg<-function(flag) {
    k<-match(flag,args)
    if (is.na(k)||k==length(args)) stop(paste("STOP_MISSING_ARG",flag),call.=FALSE)
    args[k+1L]
  }
  rawi<-getarg("--crispri-raw"); rawa<-getarg("--crispra-raw")
  mati<-getarg("--crispri-matrix"); mata<-getarg("--crispra-matrix")
  out<-getarg("--out")
  stop_if(file.exists(out),"STOP_OUTPUT_EXISTS")
  # Verify *all four* roots before opening a single large RDS.
  for (x in list(c(rawi,EXPECTED$CRISPRi$raw),
                 c(rawa,EXPECTED$CRISPRa$raw),
                 c(mati,EXPECTED$CRISPRi$matrix),
                 c(mata,EXPECTED$CRISPRa$matrix)))
    stop_if(sha256_file(x[1])!=x[2],"STOP_PINNED_INPUT_SHA")
  i<-reproduce_one("CRISPRi",rawi,mati)
  a<-reproduce_one("CRISPRa",rawa,mata)
  payload<-list(schema="GSE301119_INDEPENDENT_FULL_MATRIX_REPRODUCTION_V1",
      source="DEVELOPMENT_ONLY_TWO_DONORS",
      independent_implementation=TRUE,n_biological_donors=2L,
      population_uncertainty_produced=FALSE,
      all_targets_all_genes_recomputed=TRUE,
      tolerance_predeclared=TOLERANCE,modalities=list(CRISPRi=i,CRISPRa=a),
      protected_outcomes_opened=FALSE,jepa_training_authorized=FALSE)
  stop_if(!requireNamespace("jsonlite",quietly=TRUE),"STOP_JSONLITE_DEPENDENCY")
  dir.create(dirname(out),recursive=TRUE,showWarnings=FALSE)
  writeLines(jsonlite::toJSON(payload,pretty=TRUE,auto_unbox=TRUE,
                             digits=16),out,useBytes=TRUE)
  cat("PASS INDEPENDENT FULL MATRIX DEVELOPMENT REPRODUCTION; NOT biological confirmation\n")
}
if (sys.nframe()==0L) main()
