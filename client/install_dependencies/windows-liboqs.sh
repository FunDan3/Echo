#! /usr/bin/bash

sudo apt install cmake gcc gcc-mingw-w64 ninja-build
git clone https://github.com/open-quantum-safe/liboqs
cd liboqs
mkdir build
cd build
cmake -GNinja -DCMAKE_TOOLCHAIN_FILE=../.CMake/toolchain_windows-amd64.cmake -DOQS_DIST_BUILD=ON -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON ..
ninja
