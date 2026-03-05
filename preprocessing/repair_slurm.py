#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import time


def command_exists(cmd):
    return shutil.which(cmd) is not None


def check_health():
    if not command_exists("sinfo"):
        return 2
    if subprocess.run("systemctl is-active --quiet munge", shell=True).returncode != 0:
        return 1
    if subprocess.run("systemctl is-active --quiet slurmctld", shell=True).returncode != 0:
        return 1
    if subprocess.run("systemctl is-active --quiet slurmd", shell=True).returncode != 0:
        return 1
    if subprocess.run("sinfo >/dev/null 2>&1", shell=True).returncode != 0:
        return 1
    return 0


if os.geteuid() != 0:
    print("Run as root")
    sys.exit(1)

print("===== SLURM REPAIR MODULE =====")

STATUS = check_health()

if STATUS == 0:
    print("Slurm is HEALTHY. No repair required.")
    sys.exit(0)

if STATUS == 2:
    print("Slurm not installed. Installing fresh.")
    subprocess.run("python3 install_slurm.py", shell=True)
    sys.exit(0)

print("Slurm broken. Repairing...")

subprocess.run("python3 remove_slurm.py", shell=True)
subprocess.run("python3 install_slurm.py", shell=True)

time.sleep(3)

if subprocess.run("sinfo >/dev/null 2>&1", shell=True).returncode == 0:
    print("Repair Successful")
else:
    print("Repair Failed")
