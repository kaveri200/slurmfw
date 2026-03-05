#!/usr/bin/env python3

import os
import sys
import time
import shutil
import subprocess
from health import check_health, HEALTHY, BROKEN, NOT_INSTALLED

SLURM_VERSION = "25.11.3"
PREFIX = "/usr/local/slurm"
ARCHIVE = f"slurm-{SLURM_VERSION}.tar.bz2"
SOURCE_DIR = f"slurm-{SLURM_VERSION}"
SLURM_URL = f"https://download.schedmd.com/slurm/{ARCHIVE}"


def run(cmd, check=True):
    print(f"[RUN] {cmd}")
    subprocess.run(cmd, shell=True, check=check)


def detect_os():
    with open("/etc/os-release") as f:
        for line in f:
            if line.startswith("ID="):
                return line.strip().split("=")[1].replace('"', "")
    return "unknown"


def install_dependencies():
    print("Installing dependencies...")
    os_id = detect_os()

    if os_id in ["fedora", "rhel", "centos"]:
        run("dnf install -y @development-tools")

        packages = [
            "munge", "munge-libs", "munge-devel",
            "openssl-devel", "pam-devel",
            "hwloc-devel", "libbpf-devel",
            "libcap-devel", "numactl-devel",
            "json-c-devel", "readline-devel",
            "perl", "tar", "wget", "curl",
            "dbus-devel","systemd-devel"
        ]

        run("dnf install -y " + " ".join(packages))

    elif os_id in ["ubuntu", "debian"]:
        run("apt update -y")

        packages = [
            "build-essential",
            "munge", "libmunge-dev",
            "libssl-dev", "libpam0g-dev",
            "libhwloc-dev", "libcap-dev",
            "libnuma-dev", "libjson-c-dev",
            "libreadline-dev",
            "wget", "curl", "tar",
            
        ]

        run("apt install -y " + " ".join(packages))

    else:
        print("Unsupported OS")
        sys.exit(1)

import os
import shutil
import subprocess
import sys


def configure_munge():
    print("Configuring Munge...")

    # 1️⃣ Ensure munge user exists
    if subprocess.run(
        "id munge",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode != 0:
        print("Creating munge user...")
        subprocess.run(
            "useradd -r -s /sbin/nologin munge",
            shell=True,
            check=True
        )

    # 2️⃣ Create required directories
    subprocess.run("mkdir -p /etc/munge", shell=True, check=True)
    subprocess.run("mkdir -p /var/log/munge", shell=True, check=True)
    subprocess.run("mkdir -p /run/munge", shell=True, check=True)
    subprocess.run("mkdir -p /var/lib/munge", shell=True, check=True)
    subprocess.run("chown -R munge:munge /var/lib/munge", shell=True, check=True)
    subprocess.run("chmod 0700 /var/lib/munge", shell=True, check=True)
    # 3️⃣ Set ownership
    subprocess.run("chown -R munge:munge /etc/munge", shell=True, check=True)
    subprocess.run("chown -R munge:munge /var/log/munge", shell=True, check=True)
    subprocess.run("chown -R munge:munge /run/munge", shell=True, check=True)

    # 4️⃣ Set permissions
    subprocess.run("chmod 0700 /etc/munge", shell=True, check=True)

    key_path = "/etc/munge/munge.key"

    # 5️⃣ Create munge key if missing
    if not os.path.exists(key_path):
        print("Creating munge key...")

        if shutil.which("mungekey"):
            subprocess.run("mungekey --create", shell=True, check=True)

        elif shutil.which("create-munge-key"):
            subprocess.run("create-munge-key", shell=True, check=True)

        else:
            print("ERROR: No munge key creation utility found.")
            sys.exit(1)

    # 6️⃣ Ensure key ownership and permissions
    subprocess.run("chown munge:munge /etc/munge/munge.key", shell=True, check=True)
    subprocess.run("chmod 400 /etc/munge/munge.key", shell=True, check=True)

    # 7️⃣ Fix SELinux context (important on Fedora/RHEL)
    if shutil.which("restorecon"):
        subprocess.run("restorecon -Rv /etc/munge", shell=True)

    print("Munge configured successfully.")


def download_source():
    print("Downloading Slurm source...")

    if not os.path.exists(ARCHIVE):
        run(f"curl -LO {SLURM_URL}")

    if not os.path.exists(SOURCE_DIR):
        run(f"tar -xjf {ARCHIVE}")

    if not os.path.exists(SOURCE_DIR):
        print("ERROR: Source extraction failed.")
        sys.exit(1)

    print("Source ready.")

def build_slurm():
    print("Building Slurm...")

    os.chdir(SOURCE_DIR)

    result = subprocess.run(
        f"./configure "
        f"--prefix={PREFIX} "
        f"--sysconfdir=/etc/slurm "
        f"--with-munge "
        f"--with-hwloc "
        f"--with-systemdsystemunitdir=/etc/systemd/system",
        shell=True,
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("ERROR: Configure failed.")
        sys.exit(1)

    run("make -j$(nproc)")
    run("make install")

    # Verify installation
    if not os.path.exists(f"{PREFIX}/sbin/slurmd"):
        print("ERROR: Slurm install failed. slurmd not found.")
        sys.exit(1)

    print("Slurm built and installed successfully.")

    os.chdir("..")
def configure_slurm():
    print("Configuring Slurm...")

    hostname = subprocess.check_output("hostname", shell=True).decode().strip()
    cpus = subprocess.check_output("nproc", shell=True).decode().strip()

    run("mkdir -p /etc/slurm")
    run("mkdir -p /var/lib/slurm")
    run("mkdir -p /var/spool/slurm")

    run("useradd -r -s /sbin/nologin slurm", check=False)

    run("chown slurm:slurm /var/lib/slurm")
    run("chown slurm:slurm /var/spool/slurm")

    slurm_conf = f"""
ClusterName=cluster
SlurmctldHost={hostname}

SlurmUser=slurm
AuthType=auth/munge
StateSaveLocation=/var/lib/slurm
SlurmdSpoolDir=/var/spool/slurm

SlurmctldPidFile=/run/slurmctld.pid
SlurmdPidFile=/run/slurmd.pid

NodeName={hostname} CPUs={cpus} State=UNKNOWN
PartitionName=caribou_node Nodes={hostname} Default=YES MaxTime=INFINITE State=UP
"""

    with open("/etc/slurm/slurm.conf", "w") as f:
        f.write(slurm_conf)

    print("Slurm configuration created.")
def configure_cgroup():
    print("Configuring cgroup...")

    cgroup_conf = """
CgroupAutomount=yes
CgroupMountpoint=/sys/fs/cgroup
ConstrainCores=no
ConstrainRAMSpace=no
ConstrainDevices=no
"""

    with open("/etc/slurm/cgroup.conf", "w") as f:
        f.write(cgroup_conf)

    print("cgroup configuration created.")
def create_systemd_services():
    print("Creating systemd services...")

    slurmctld_service = f"""
[Unit]
Description=Slurm Controller
After=network.target munge.service
Requires=munge.service

[Service]
Type=simple
User=slurm
ExecStart={PREFIX}/sbin/slurmctld -D -f /etc/slurm/slurm.conf
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""

    slurmd_service = f"""
[Unit]
Description=Slurm Node
After=network.target munge.service slurmctld.service
Requires=munge.service

[Service]
Type=simple
User=root
ExecStart={PREFIX}/sbin/slurmd -D -f /etc/slurm/slurm.conf
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""

    with open("/etc/systemd/system/slurmctld.service", "w") as f:
        f.write(slurmctld_service)

    with open("/etc/systemd/system/slurmd.service", "w") as f:
        f.write(slurmd_service)

    run("systemctl daemon-reload")
    run("systemctl enable slurmctld")

    run("systemctl enable slurmd")
def start_services():
    print("Starting services...")

    run("systemctl enable munge", check=False)
    run("systemctl restart munge", check=False)

    # Validate munge
    result = subprocess.run(
        "systemctl is-active munge",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.stdout.strip() != "active":
        print("ERROR: Munge failed to start.")
        subprocess.run("systemctl status munge", shell=True)
        sys.exit(1)

    run("systemctl restart slurmctld")
    run("systemctl restart slurmd")
def verify_cluster():
    print("Verifying cluster...")

    for _ in range(10):
        result = subprocess.run(
            f"{PREFIX}/bin/sinfo",
            shell=True,
            capture_output=True,
            text=True
        )

        if "idle" in result.stdout:
            print("Cluster is healthy and node is IDLE.")
            return

        time.sleep(2)

    print("ERROR: Node did not reach IDLE state.")
    subprocess.run("journalctl -u slurmd -n 20", shell=True)
    sys.exit(1)


def main():
    print("===== SLURM SOURCE INSTALL MODULE =====")

    state = check_health()
    print("DEBUG: state =", state)

    if state == HEALTHY:
        print("Slurm already healthy.")
        sys.exit(0)

    if state == BROKEN:
        print("Slurm is broken. Please run cleanup first.")
        sys.exit(1)

    install_dependencies()
    configure_munge()
    download_source()
    build_slurm()
    configure_slurm()
    configure_cgroup()              # ✅ ADD THIS LINE
    create_systemd_services()
    start_services()
    verify_cluster()

    print("===== INSTALL COMPLETED SUCCESSFULLY =====")
if __name__ == "__main__":
    main()
