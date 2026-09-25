#!/usr/bin/env Rscript
# Entirely synthetic RDS fixtures. NEVER touches physical GSE301119 source files.
source("analysis/therapeutic_perturbation_etl/scripts/r/independently_verify_gse301119_all_effects_v1.R",local=TRUE)
stopifnot(requireNamespace("digest",quietly=TRUE))
n <- 0L
check <- function(expr) { stopifnot(isTRUE(expr)); n <<- n+1L }
expect_error <- function(fn,pattern) {
  x <- tryCatch({fn(); NULL},error=function(e)conditionMessage(e))
  stopifnot(is.character(x),length(x)==1L,grepl(pattern,x,fixed=TRUE))
  n <<- n+1L
}
g <- c("G1","G2","G3")
ids <- c("NT1||D1","NT2||D2","T1g1||D1","T1g1||D2","T2g1||D1","T2g1||D2")
counts <- matrix(c(
    2,3,5, 1,4,5,
    10,1,1, 10,3,2,
    6,2,2, 2,2,6
  ),nrow=3,ncol=6,dimnames=list(g,ids))
m <- data.frame(guide_donor=ids,
                guide_identity=c("NT1","NT2","T1g1","T1g1","T2g1","T2g1"),
                donor=c("D1","D2","D1","D2","D1","D2"),
                Gene_Targeted=c("NT","NT","T1","T1","T2","T2"),
                crispr=c("NT","NT","Perturbed","Perturbed","Perturbed","Perturbed"),
                n_cells=c(20,20,20,20,5,5),stringsAsFactors=FALSE)
raw<-list(schema="GSE301119_GUIDE_DONOR_RAW_PSEUDOBULK_V1",
          counts=counts,features=g,gd_meta=m)
check(isTRUE(assert_raw_metadata(raw)))
fit<-independent_target(raw,"T1")
check(fit$eligible)
norm<-function(x)log2(1+1e6*x/sum(x))
manual <- ((norm(c(10,1,1))-norm(c(2,3,5)))+
           (norm(c(10,3,2))-norm(c(1,4,5))))/2
check(max(abs(fit$mean-manual))<1e-12)
check(!independent_target(raw,"T2")$eligible)
ref<-list(schema="GSE301119_DONOR_AWARE_LOG2FC_V1",
          modality="CRISPRi",features=g,targets=c("T1","T2"),
          log2fc=cbind(T1=fit$mean,T2=rep(NA_real_,3)),
          gene_detected_in_perturbed=rowSums(counts[,m$crispr=="Perturbed",drop=FALSE])>0)
rownames(ref$log2fc)<-g
td<-tempdir()
rp<-file.path(td,"independent_raw.rds")
mp<-file.path(td,"produced_matrix.rds")
write_pair <- function() {saveRDS(raw,rp);saveRDS(ref,mp)}
expected <- function()list(raw=sha256_file(rp),matrix=sha256_file(mp),
                         targets=2L,eligible=1L,genes=3L)
write_pair()
receipt<-reproduce_one("CRISPRi",rp,mp,expected())
check(receipt$independent_effect_reproduction=="PASS" &&
      receipt$compared_finite_effects==3L &&
      receipt$confirmed_identical_missingness)
# A same-size or differently serialized rewrite invalidates the independent SHA.
bad<-readBin(rp,"raw",n=file.info(rp)$size)
bad[length(bad)]<-as.raw(bitwXor(as.integer(bad[length(bad)]),1L))
writeBin(bad,rp)
# Independent fixed expected root, not dynamically refreshed after mutation.
write_pair(); fixed<-expected()
bad<-readBin(rp,"raw",n=file.info(rp)$size)
bad[length(bad)]<-as.raw(bitwXor(as.integer(bad[length(bad)]),1L));writeBin(bad,rp)
expect_error(function()reproduce_one("CRISPRi",rp,mp,fixed),"STOP_RAW_PSEUDOBULK_SHA")
write_pair()
wrong<-raw;colnames(wrong$counts)[1]<-"NT1||D2"
expect_error(function()assert_raw_metadata(wrong),"STOP_RAW_MATRIX_METADATA_COLUMN_ALIGNMENT")
wrong<-raw;wrong$gd_meta$guide_donor[1]<-wrong$gd_meta$guide_donor[2]
expect_error(function()assert_raw_metadata(wrong),"STOP_RAW_MATRIX_METADATA_COLUMN_ALIGNMENT")
wrong<-raw;wrong$gd_meta$guide_donor[1]<-"NT1||D2"
wrong$counts<-counts
colnames(wrong$counts)[1]<-"NT1||D2"
expect_error(function()assert_raw_metadata(wrong),"STOP_GUIDE_DONOR_COMPOSITE_JOIN")
wrong<-raw;wrong$gd_meta$crispr[2]<-"Perturbed"
expect_error(function()assert_raw_metadata(wrong),"STOP_MISSING_DONOR_NT")
wrong<-raw;rownames(wrong$counts)[2]<-"G1"
expect_error(function()assert_raw_metadata(wrong),"STOP_RAW_GENE_ORDER_OR_DUPLICATE")
wrong<-raw;wrong$counts[1,1]<-0.5
expect_error(function()assert_raw_metadata(wrong),"STOP_NONINTEGER_OR_NONFINITE_RAW_COUNTS")
wrong<-raw;wrong$counts[,1]<-0
expect_error(function()independent_target(wrong,"T1"),"STOP_ZERO_OR_NONEXACT_LIBRARY_DEPTH")
wrong_ref<-ref
wrong_ref$log2fc[,1]<- -ref$log2fc[,1]
saveRDS(wrong_ref,mp)
expect_error(function()reproduce_one("CRISPRi",rp,mp,
             modifyList(expected(),list(matrix=sha256_file(mp)))),
             "STOP_INDEPENDENT_EFFECT_MISMATCH")
wrong_ref<-ref
wrong_ref$gene_detected_in_perturbed[1]<-FALSE
saveRDS(wrong_ref,mp)
expect_error(function()reproduce_one("CRISPRi",rp,mp,
             modifyList(expected(),list(matrix=sha256_file(mp)))),
             "STOP_ASSAY_DETECTION_MASK_MISMATCH")
cat("SYNTHETIC R RED TEAM PASS:",n,"checks, NO PHYSICAL EFFECT DATA READ\n")
