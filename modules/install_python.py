#!/usr/bin/env python3

import subprocess
import re
import sys

PREFIX="/opt/slurmfw/python"

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

def get_latest_python():

    print("Detecting latest Python version...")

    output = subprocess.check_output(
        "curl -s https://www.python.org/ftp/python/ | grep -oE '[0-9]+\\.[0-9]+\\.[0-9]+' | sort -V | tail -1",
        shell=True
    ).decode().strip()

    return output

def main():

    version = get_latest_python()

    if not version:
        print("Could not detect Python version")
        sys.exit(1)

    print("Latest Python:", version)

    tar = f"Python-{version}.tgz"
    url = f"https://www.python.org/ftp/python/{version}/{tar}"

    run("dnf install -y wget tar openssl-devel bzip2-devel libffi-devel")

    run(f"cd /tmp && wget {url}")
    run(f"cd /tmp && tar -xf {tar}")

    run(f"""
cd /tmp/Python-{version} &&
./configure --prefix={PREFIX} --enable-optimizations
""")

    run("cd /tmp/Python-* && make -j$(nproc)")
    run("cd /tmp/Python-* && make install")

    print("Python installed at", PREFIX)

if __name__ == "__main__":
    main()
