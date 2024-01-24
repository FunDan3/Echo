#! /usr/bin/bash
# This script was created thanks to neomn's answer to https://github.com/kpdemetriou/pqcrypto/issues/10

#Determine python3 version
python_version=$(./python_version.sh)

#Install broken package
pip3 install pqcrypto

#Clone source code
git clone https://github.com/kpdemetriou/pqcrypto/
cd pqcrypto

#Compile package
pip3 install poetry
python3 compile.py
poetry build

#Fix broken package
rm ~/.local/lib/python${python_version}/site-packages/pqcrypto/_kem/ -r
rm ~/.local/lib/python${python_version}/site-packages/pqcrypto/_sign/ -r
cp ./pqcrypto/_kem ~/.local/lib/python${python_version}/site-packages/pqcrypto/_kem -r
cp ./pqcrypto/_sign ~/.local/lib/python${python_version}/site-packages/pqcrypto/_sign -r

#Delete pqcrypto
cd ..
rm ./pqcrypto/ -rf
