#! /usr/bin/bash
# This script was created thanks to neomn's answer to https://github.com/kpdemetriou/pqcrypto/issues/10

#Determine python3 version
python_version=$(./python_version.sh)

#Install requierments
sudo apt install git libssl-dev cmake gcc -y

#Install library binaries
git clone --depth=1 https://github.com/open-quantum-safe/liboqs
cmake -S liboqs -B liboqs/build -DBUILD_SHARED_LIBS=ON
cmake --build liboqs/build --parallel 16
sudo cmake --build liboqs/build --target install

#Add library path
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

#Install python wrapper
git clone --depth=1 https://github.com/open-quantum-safe/liboqs-python
cd liboqs-python
pip install .
