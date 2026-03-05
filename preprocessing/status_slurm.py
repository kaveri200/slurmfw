#!/usr/bin/env python3

import subprocess
import shutil
import os


def command_exists(cmd):
    return shutil.which(cmd) is not None


print("===== SLURM STATUS MODULE =====")

binary_exists = command_exists("sinfo")

service_exists = subprocess.run(
    "systemctl list-unit-files | grep slurm",
    shell=True,
    stdout=subprocess.DEVNULL
).returncode == 0

slurmctld_active = subprocess.run(
    "systemctl is-active --quiet slurmctld",
    shell=True
).returncode == 0

slurmd_active = subprocess.run(
    "systemctl is-active --quiet slurmd",
    shell=True
).returncode == 0


# -------------------------------
# Determine State
# -------------------------------

if not binary_exists and not service_exists:
    print("State: NOT INSTALLED")

elif binary_exists and slurmctld_active and slurmd_active:
    print("State: HEALTHY")

else:
    print("State: BROKEN")


print("\nService Details:\n")

subprocess.run("systemctl status slurmctld --no-pager 2>/dev/null", shell=True)
print()
subprocess.run("systemctl status slurmd --no-pager 2>/dev/null", shell=True)
