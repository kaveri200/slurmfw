#!/usr/bin/env python3

import os
import subprocess
import shutil
import sys

from health import check_health, HEALTHY, BROKEN, NOT_INSTALLED


# -----------------------------------
# Utility
# -----------------------------------

def run(cmd):
    subprocess.run(cmd, shell=True)


# -----------------------------------
# Actual cleanup
# -----------------------------------

def perform_cleanup():

    print("Stopping Slurm services...")

    services = ["slurmctld", "slurmd", "slurmdbd"]

    for svc in services:
        run(f"systemctl stop {svc}")
        run(f"systemctl disable {svc}")

    print("Stopping Munge service...")

    run("systemctl stop munge")
    run("systemctl disable munge")

    print("Removing Slurm installation...")

    shutil.rmtree("/usr/local/slurm", ignore_errors=True)

    print("Removing configuration...")

    paths = [
        "/etc/slurm",
        "/var/spool/slurm",
        "/var/lib/slurm",
        "/var/log/slurm",
        "/run/slurm"
    ]

    for p in paths:
        shutil.rmtree(p, ignore_errors=True)

    print("Removing Munge configuration...")

    munge_paths = [
        "/etc/munge",
        "/var/log/munge",
        "/run/munge",
        "/var/lib/munge"
    ]

    for p in munge_paths:
        shutil.rmtree(p, ignore_errors=True)

    print("Removing systemd services...")

    services = [
        "/etc/systemd/system/slurmctld.service",
        "/etc/systemd/system/slurmd.service",
        "/usr/lib/systemd/system/slurmctld.service",
        "/usr/lib/systemd/system/slurmd.service"
    ]

    for s in services:
        if os.path.exists(s):
            os.remove(s)

    run("systemctl daemon-reload")

    print("Removing users...")

    run("userdel slurm")
    run("userdel munge")

    print("Slurm cleanup completed.")


# -----------------------------------
# Main
# -----------------------------------

def main():

    print("===== SLURM CLEANUP MODULE =====")

    if os.geteuid() != 0:
        print("Run with sudo.")
        sys.exit(1)

    state = check_health()

    # -----------------------------------
    # Case 1: Not installed
    # -----------------------------------

    if state == NOT_INSTALLED:
        print("Slurm is not installed. Nothing to cleanup.")
        return

    # -----------------------------------
    # Case 2: Broken
    # -----------------------------------

    if state == BROKEN:
        print("Slurm is broken. Removing it automatically...")
        perform_cleanup()
        return

    # -----------------------------------
    # Case 3: Healthy
    # -----------------------------------

    if state == HEALTHY:

        print("Slurm is currently HEALTHY.")

        choice = input(
            "Slurm is healthy. Do you still want to delete it? (yes/no): "
        ).strip().lower()

        if choice not in ["yes", "y"]:
            print("Cleanup cancelled.")
            return

        perform_cleanup()


# -----------------------------------

if __name__ == "__main__":
    main()
