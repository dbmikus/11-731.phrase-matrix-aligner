#!/bin/bash

# You should only run this script if you have not installed the following
# components:
#   GIZA++
#   Moses: statistical MT system

CUR_DIR=$(pwd)

# We automatically set the experiment home directory to the location of this
# bash file.
EXP_HOME=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)

EXP_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# If you want to set the experiment home directory to a different directory,
# you can uncomment the line below and set your custom home, or you can just
# alter the line above.
# EXP_HOME=${HOME}

cd ${EXP_HOME}

# Install the Moses statistical MT system.
# You need to make sure that you have the following installed on your system:
#   g++
#   Boost
# They should be available from most system software / package managers
git clone https://github.com/moses-smt/mosesdecoder.git
cd mosesdecoder/
./bjam -j8

Install GIZA++
We use GIZA++ for word alignment.
We will download the latest stable version from SVN.
svn checkout http://giza-pp.googlecode.com/svn/trunk/ giza-pp
cd giza-pp
make

# This should create the binaries:
#   ~/giza-pp/GIZA++-v2/GIZA++
#   ~/giza-pp/GIZA++-v2/snt2cooc.out
#   ~/giza-pp/mkcls-v2/mkcls
# We need to copy these to where Moses can find them
cd ${EXP_HOME}/mosesdecoder
mkdir tools
cp ${EXP_HOME}/giza-pp/GIZA++-v2/GIZA++ \
   ${EXP_HOME}/giza-pp/GIZA++-v2/snt2cooc.out \
   ${EXP_HOME}/giza-pp/mkcls-v2/mkcls \
   tools


# Prepare the training corpus
cd ${EXP_HOME}
mkdir corpus
cd corpus
wget http://www.statmt.org/wmt13/training-parallel-nc-v8.tgz
tar -zxvf training-parallel-nc-v8.tgz


# Prepare the dev corpus
cd ${EXP_HOME}/corpus/
wget http://www.statmt.org/wmt12/dev.tgz
tar -zxvf dev.tgz


# Making the working directory
cd ${EXP_HOME}
mkdir working
mkdir working/experiments

cd ${CUR_DIR}
