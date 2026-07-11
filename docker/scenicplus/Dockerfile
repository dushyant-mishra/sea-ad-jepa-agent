FROM mambaorg/micromamba:latest

LABEL org.opencontainers.image.title="SCENIC+ v1.0a2 runtime"
LABEL org.opencontainers.image.description="Pinned SCENIC+ v1.0a2 container with pycisTopic, pycisTarget, pySCENIC, MACS2, MEME, MALLET, Snakemake, and JupyterLab."
LABEL org.opencontainers.image.source="https://github.com/aertslab/scenicplus"

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    gfortran \
    git \
    libcurl4-openssl-dev \
    libfftw3-dev \
    libgl1 \
    libhdf5-dev \
    libopenblas-dev \
    libsm6 \
    libxext6 \
    libxml2-dev \
    libxrender1 \
    libxslt1-dev \
    default-jdk \
    pkg-config \
    procps \
    swig \
    unzip \
    wget \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

RUN micromamba install -y -n base \
    -c conda-forge \
    -c bioconda \
    bedtools \
    cython=0.29.37 \
    datrie=0.8.2 \
    ipykernel \
    jupyterlab \
    macs2=2.2.9.1 \
    meme=5.5.9 \
    numpy=1.26.4 \
    pip=24.3.1 \
    python=3.11.8 \
    samtools \
    snakemake=8.5.5 \
    "setuptools<81" \
    setuptools-scm \
    wheel \
    && micromamba clean --all --yes

USER root

RUN ln -s /opt/conda/bin/python /usr/local/bin/python3

ARG MALLET_VERSION=2.1.0

RUN wget -q -O /tmp/mallet.zip "https://github.com/mimno/Mallet/releases/download/v${MALLET_VERSION}/mallet-${MALLET_VERSION}-bin.zip" \
    && unzip -q /tmp/mallet.zip -d /opt \
    && ln -s /opt/mallet-${MALLET_VERSION} /opt/mallet \
    && rm /tmp/mallet.zip \
    && test -x /opt/mallet/bin/mallet

ENV MALLET_HOME=/opt/mallet
ENV PATH="/opt/mallet/bin:${PATH}"

ARG CREATE_CISTARGET_DATABASES_REF=master

RUN git clone --depth 1 --branch ${CREATE_CISTARGET_DATABASES_REF} https://github.com/aertslab/create_cisTarget_databases.git /opt/create_cisTarget_databases \
    && wget -q -O /usr/local/bin/cbust https://resources.aertslab.org/cistarget/programs/cbust \
    && wget -q -O /usr/local/bin/liftOver https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/liftOver \
    && wget -q -O /usr/local/bin/bigWigAverageOverBed https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bigWigAverageOverBed \
    && chmod a+x /usr/local/bin/cbust /usr/local/bin/liftOver /usr/local/bin/bigWigAverageOverBed \
    && chmod a+x /opt/create_cisTarget_databases/*.py /opt/create_cisTarget_databases/*.sh

ENV CREATE_CISTARGET_DATABASES_DIR=/opt/create_cisTarget_databases
ENV PATH="/opt/create_cisTarget_databases:${PATH}"

USER $MAMBA_USER

ARG SCENICPLUS_REF=v1.0a2

RUN git clone --depth 1 --branch ${SCENICPLUS_REF} https://github.com/aertslab/scenicplus.git /tmp/scenicplus \
    && micromamba run -n base python -c "import setuptools, pkg_resources; print('setuptools', setuptools.__version__); print('pkg_resources OK')" \
    && micromamba run -n base python -m pip install --no-cache-dir pysam==0.22.0 \
    && micromamba run -n base python -m pip install --no-build-isolation --no-cache-dir pybedtools==0.9.1 \
    && micromamba run -n base python -m pip install --no-cache-dir packaging==24.0 hatchling==1.21.1 poetry-core==1.0.8 \
    && micromamba run -n base python -m pip install --no-cache-dir --no-deps poetry==1.1.15 \
    && micromamba run -n base python -m pip install --no-build-isolation --no-cache-dir /tmp/scenicplus \
    && rm -rf /tmp/scenicplus

RUN micromamba run -n base python - <<'PY'
import anndata
import pybedtools
import pycisTopic
import pycistarget
import pyscenic
import pysam
import scanpy
import scenicplus
import setuptools

print("setuptools:", setuptools.__version__)
print("scenicplus:", getattr(scenicplus, "__version__", "version unavailable"))
print("pybedtools:", pybedtools.__version__)
print("pysam:", pysam.__version__)
print("SCENIC+ container import test passed")
PY

RUN micromamba run -n base bedtools --version \
    && micromamba run -n base macs2 --version \
    && micromamba run -n base scenicplus --help >/dev/null \
    && ( \
         /opt/mallet/bin/mallet train-topics --help TRUE >/tmp/mallet-train-topics-help.txt 2>&1 \
         || test $? -eq 255 \
       ) \
    && grep -q -- "--num-topics" /tmp/mallet-train-topics-help.txt \
    && rm -f /tmp/mallet-train-topics-help.txt \
    && (cbust --help >/dev/null 2>&1 || test $? -eq 1) \
    && create_cistarget_motif_databases.py --help >/dev/null \
    && liftOver 2>&1 | grep -q "liftOver" \
    && bigWigAverageOverBed 2>&1 | grep -q "bigWigAverageOverBed"

WORKDIR /workspace

CMD ["/bin/bash"]
