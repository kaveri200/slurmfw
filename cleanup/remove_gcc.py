#!/usr/bin/env python3

import shutil

def main():

    print("Removing GCC...")

    shutil.rmtree("/opt/slurmfw/gcc", ignore_errors=True)

    print("GCC removed.")

if __name__ == "__main__":
    main()
