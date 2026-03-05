#!/usr/bin/env python3

import subprocess
import sys

PREFIX="/opt/slurmfw/openmp"

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

def main():

    print("Installing OpenMP runtime...")

    run("dnf install -y cmake git gcc gcc-c++")

    run("cd /tmp && git clone https://github.com/llvm/llvm-project.git")

    run("""
cd /tmp/llvm-project/openmp &&
mkdir build &&
cd build &&
cmake -DCMAKE_INSTALL_PREFIX=/opt/slurmfw/openmp ..
""")

    run("cd /tmp/llvm-project/openmp/build && make -j$(nproc)")
    run("cd /tmp/llvm-project/openmp/build && make install")

    print("OpenMP runtime installed at", PREFIX)

if __name__ == "__main__":
    main()
