#!/bin/bash

# this script should run as root and has been tested with ubuntu 20.04
export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get -y upgrade
apt-get install -y linux-headers-$(uname -r)
apt-get install -y build-essential make zlib1g-dev librrd-dev libpcap-dev autoconf automake libarchive-dev iperf3 htop bmon vim wget pkg-config git python-dev python3-pip libtool
pip install --upgrade pip
pip install paramiko pandas sage-data-client

######################
### EDIT /etc/hosts ##
######################

cat << EOF >> /etc/hosts
$2 $3
EOF

######################
### INSTALL CONDOR ###
######################

wget -qO - https://research.cs.wisc.edu/htcondor/repo/keys/HTCondor-current-Key | sudo apt-key add -
echo "deb [arch=amd64] http://research.cs.wisc.edu/htcondor/repo/ubuntu/current $(lsb_release -cs) main" >> /etc/apt/sources.list

apt-get update && apt-get install -y htcondor

cat << EOF > /etc/condor/config.d/50-main.config
DAEMON_LIST = MASTER, COLLECTOR, NEGOTIATOR, SCHEDD

CONDOR_HOST = $3

USE_SHARED_PORT = TRUE

NETWORK_INTERFACE = $1

ENABLE_IPV6 = FALSE

# the nodes have shared filesystem
UID_DOMAIN = \$(CONDOR_HOST)
TRUST_UID_DOMAIN = TRUE
FILESYSTEM_DOMAIN = \$(FULL_HOSTNAME)

#--     Authentication settings
SEC_PASSWORD_FILE = /etc/condor/pool_password
SEC_DEFAULT_AUTHENTICATION = REQUIRED
SEC_DEFAULT_AUTHENTICATION_METHODS = FS,PASSWORD
SEC_READ_AUTHENTICATION = OPTIONAL
SEC_CLIENT_AUTHENTICATION = OPTIONAL
SEC_ENABLE_MATCH_PASSWORD_AUTHENTICATION = TRUE
DENY_WRITE = anonymous@*
DENY_ADMINISTRATOR = anonymous@*
DENY_DAEMON = anonymous@*
DENY_NEGOTIATOR = anonymous@*
DENY_CLIENT = anonymous@*

#--     Privacy settings
SEC_DEFAULT_ENCRYPTION = OPTIONAL
SEC_DEFAULT_INTEGRITY = REQUIRED
SEC_READ_INTEGRITY = OPTIONAL
SEC_CLIENT_INTEGRITY = OPTIONAL
SEC_READ_ENCRYPTION = OPTIONAL
SEC_CLIENT_ENCRYPTION = OPTIONAL

#-- With strong security, do not use IP based controls
HOSTALLOW_WRITE = *
ALLOW_NEGOTIATOR = *

EOF

condor_store_cred -f /etc/condor/pool_password -p p3g@sus

systemctl enable condor
systemctl restart condor

#######################
### INSTALL PEGASUS ###
#######################
wget -O - http://download.pegasus.isi.edu/pegasus/gpg.txt | sudo apt-key add -
echo "deb [arch=amd64] http://download.pegasus.isi.edu/pegasus/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/pegasus.list
apt-get update && apt-get install -y pegasus

##########################
### INSTALL SINGULARITY ##
##########################

apt-get update && sudo apt-get install -y build-essential \
    uuid-dev \
    libgpgme-dev \
    squashfs-tools \
    libseccomp-dev \
    wget \
    pkg-config \
    git \
    cryptsetup-bin

export VERSION=1.18 OS=linux ARCH=amd64 && \
    wget https://dl.google.com/go/go$VERSION.$OS-$ARCH.tar.gz && \
    sudo tar -C /usr/local -xzvf go$VERSION.$OS-$ARCH.tar.gz && \
    rm go$VERSION.$OS-$ARCH.tar.gz

echo 'export GOPATH=${HOME}/go' >> ~/.bashrc
echo 'export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin' >> ~/.bashrc

export GOPATH=${HOME}/go >> ~/.bashrc
export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin >> ~/.bashrc

export VERSION=3.8.7 && # adjust this as necessary \
    wget https://github.com/apptainer/singularity/releases/download/v${VERSION}/singularity-${VERSION}.tar.gz&& \
    tar -xzf singularity-${VERSION}.tar.gz && \
    rm singularity-${VERSION}.tar.gz && \
    cd singularity-${VERSION}

./mconfig && \
    make -C ./builddir && \
    make -C ./builddir install

##########################
### INSTALL DOCKER      ##
##########################
cd
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

#groupadd docker
usermod -aG docker condor

systemctl enable docker
systemctl restart docker

apt-get install -y docker-compose-plugin

############################
### INSTALL TSTAT       ####
############################

apt-get install -y libpcap-dev

cd
wget http://www.tstat.polito.it/download/tstat-3.1.1.tar.gz
tar -xzvf tstat-3.1.1.tar.gz
cd tstat-3.1.1
./autogen.sh
./configure --enable-libtstat --enable-zlib
make && make install

############################
### SETUP DEFAULT USER ####
############################
cd
usermod -a -G docker ubuntu

echo 'export GOPATH=${HOME}/go' >> /home/ubuntu/.bashrc
echo 'export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin' >> /home/ubuntu/.bashrc
