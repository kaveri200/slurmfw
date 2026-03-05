import os
import subprocess
import shutil

HEALTHY = 0
BROKEN = 1
NOT_INSTALLED = 2


def check_health():

    # 1️⃣ Check binary
    if not os.path.exists("/usr/local/slurm/bin/sinfo"):
        return NOT_INSTALLED

    # 2️⃣ Check config
    if not os.path.exists("/etc/slurm/slurm.conf"):
        return NOT_INSTALLED

    # 3️⃣ Check services
    services = ["munge", "slurmctld", "slurmd"]

    for service in services:
        result = subprocess.run(
            f"systemctl is-active {service}",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.stdout.strip() != "active":
            return BROKEN

    # 4️⃣ Check sinfo works
    result = subprocess.run(
        "/usr/local/slurm/bin/sinfo",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return BROKEN

    return HEALTHY
