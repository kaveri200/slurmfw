#!/usr/bin/env python3

import shutil

def main():

    print("Removing Python...")

    shutil.rmtree("/opt/slurmfw/python", ignore_errors=True)

    print("Python removed.")

if __name__ == "__main__":
    main()
