FROM nvidia/opengl:1.2-glvnd-runtime-ubuntu20.04

USER root

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive
~
# Setup demo environment variables
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=C.UTF-8 \
    OMPI_MCA_btl_vader_single_copy_mechanism=none

# install prerequistes from Lncmi debian repo
RUN apt update \
    && apt-get -y upgrade \
    && apt-get -y install lsb-release \
    && apt-get -y install debian-keyring \
    && cp /usr/share/keyrings/debian-maintainers.gpg /etc/apt/trusted.gpg.d \
    && echo "deb http://euler.GRENOBLE.LNCMI.LOCAL/~trophime/debian/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/lncmi.list \
    && apt update \
    && apt-get -y install python-is-python3 python3-pandas \
    && apt-get -y install python3-magnetgeo python3-magnetgmsh

# Clean up
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

