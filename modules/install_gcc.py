#!/usr/bin/env python3

import subprocess
import re
import sys

PREFIX="/opt/slurmfw/gcc"

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

def get_latest_gcc():

    print("Detecting latest GCC version...")

    output = subprocess.check_output(
        "curl -s https://ftp.gnu.org/gnu/gcc/ | grep -o 'gcc-[0-9]*\\.[0-9]*\\.[0-9]*' | sort -V | tail -1",
        shell=True
    ).decode().strip()

    return output

def main():

    gcc_version = get_latest_gcc()

    if not gcc_version:
        print("Failed to detect GCC version")
        sys.exit(1)

    print("Latest GCC:", gcc_version)

    tar = f"{gcc_version}.tar.gz"
    url = f"https://ftp.gnu.org/gnu/gcc/{gcc_version}/{tar}"

    run("dnf install -y wget tar gmp-devel mpfr-devel libmpc-devel")

    run(f"cd /tmp && wget {url}")
    run(f"cd /tmp && tar -xf {tar}")

    run(f"cd /tmp/{gcc_version} && ./contrib/download_prerequisites")

    run("mkdir -p /tmp/gcc-build")

    run(f"""
cd /tmp/gcc-build &&
/tmp/{gcc_version}/configure --prefix={PREFIX} --enable-languages=c,c++ --disable-multilib
""")

    run("cd /tmp/gcc-build && make -j$(nproc)")
    run("cd /tmp/gcc-build && make install")

    print("GCC installed at", PREFIX)

if __name__ == "__main__":
    main()
