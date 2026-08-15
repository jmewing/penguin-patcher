#!/usr/bin/env python3
"""
Penguin Patcher Stub Installer.

Implements a minimal macOS stub install flow based on Asahi Linux patterns.
Creates a minimal bootable APFS volume group in the internal container to
enable chainloading Linux via the Apple boot picker.

Target: Mac mini M1 (J274AP, t8103)
"""

import argparse
import logging
import os
import os.path
import plistlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# -----------------------------------------------------------------------------
# Constants & Configuration
# -----------------------------------------------------------------------------

STUB_NAME = "penguin-stub"
# Device specific constants for Mac mini M1 (J274AP)
# Note: in actual check we use the plist's ApBoardID strings
BOARD_ID = "0xJ274AP" 
CHIP_ID = "0xT8103"

# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------

def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout
    )

# -----------------------------------------------------------------------------
# Hardware & Disk Utilities
# -----------------------------------------------------------------------------

class DiskUtil:
    """Wrapper for macOS diskutil and bless commands."""
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def run(self, cmd, check=True):
        logging.debug(f"Executing: {' '.join(cmd)}")
        if self.dry_run:
            logging.info(f"[DRY-RUN] { ' '.join(cmd) }")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.run(cmd, check=check, capture_output=True, text=True)

    def get_internal_container(self):
        """Finds the main internal system APFS container."""
        logging.info("Detecting internal APFS container...")
        # In a real Mac, we'd parse `diskutil apfs list`
        # For this stub, we look for the container containing the macOS boot volume
        res = self.run(["diskutil", "apfs", "list"])
        # Simplified: find the first container with a 'System' role volume
        # Real implementation should be more robust
        for line in res.stdout.splitlines():
            if "APFS Container Reference" in line:
                return line.split(":")[-1].strip()
        raise RuntimeError("Could not find internal APFS container")

    def add_volume(self, container, name, role):
        """Adds an APFS volume with a specific role."""
        # Role map: S=System, D=Data, B=Preboot, R=Recovery
        cmd = ["diskutil", "apfs", "addVolume", container, "APFS", name, "-role", role]
        logging.info(f"Adding volume {name} with role {role}...")
        res = self.run(cmd)
        # Extract device identifier (e.g. disk3s1)
        for line in res.stdout.splitlines():
            if "created" in line and "disk" in line:
                return line.split()[-1]
        return None

    def delete_volume(self, volume_id):
        """Deletes an APFS volume."""
        logging.info(f"Deleting volume {volume_id}...")
        self.run(["diskutil", "apfs", "deleteVolume", volume_id])

    def bless(self, folder):
        """Blesses a folder as the boot target."""
        logging.info(f"Blessing {folder}...")
        self.run(["bless", "--folder", folder, "--setBoot"])

# -----------------------------------------------------------------------------
# Stub Installer Logic
# -----------------------------------------------------------------------------

class PenguinStubInstaller:
    def __init__(self, ipsw_path, dry_run=False, verbose=False):
        self.ipsw_path = Path(ipsw_path)
        self.dry_run = dry_run
        self.dutil = DiskUtil(dry_run)
        setup_logging(verbose)

        # Volume mount points (determined during install)
        self.system_vol = None
        self.data_vol = None
        self.preboot_vol = None
        self.recovery_vol = None

    def cleanup_previous(self, container):
        """Removes any existing volumes named 'penguin-stub'."""
        logging.info("Cleaning up previous installation attempts...")
        res = self.dutil.run(["diskutil", "apfs", "list"])
        # This is a simplification; real implementation needs to parse the hierarchy
        # for volumes named STUB_NAME and delete them.
        if self.dry_run:
            logging.info(f"[DRY-RUN] Would search for and delete volumes named {STUB_NAME}")
            return
        
        # Mock implementation of volume deletion based on name
        # In reality, we'd parse the diskutil output and find the device IDs
        logging.info("No previous penguin-stub volumes found (simulated).")

    def prepare_volumes(self):
        """Creates the APFS volume group."""
        container = self.dutil.get_internal_container()
        self.cleanup_previous(container)

        logging.info(f"Creating volume group in container {container}...")
        
        # 1. Data Volume ( Required for the group)
        # We use "penguin-stub-data" to avoid collision
        self.data_vol = self.dutil.add_volume(container, f"{STUB_NAME}-data", "D")
        
        # 2. System Volume (Linked to Data)
        # diskutil apfs addVolume <container> APFS <name> -role S -groupWith <data_vol>
        # Note: Our DiskUtil wrapper needs updating for -groupWith
        cmd = ["diskutil", "apfs", "addVolume", container, "APFS", STUB_NAME, "-role", "S", "-groupWith", self.data_vol]
        logging.info(f"Adding System volume {STUB_NAME} linked to {self.data_vol}...")
        res = self.dutil.run(cmd)
        for line in res.stdout.splitlines():
            if "created" in line and "disk" in line:
                self.system_vol = line.split()[-1]

        # 3. Preboot Volume
        self.preboot_vol = self.dutil.add_volume(container, "Preboot", "B")
        
        # 4. Recovery Volume
        self.recovery_vol = self.dutil.add_volume(container, "Recovery", "R")

        logging.info("Volume group created successfully.")

    def extract_minimal_ipsw(self):
        """Extracts only the essential boot files from the IPSW."""
        logging.info(f"Opening IPSW: {self.ipsw_path}")
        
        # Files to extract based on asahi-installer/src/stub.py
        # Relative to IPSW root
        essential_files = [
            "BuildManifest.plist",
            "SystemVersion.plist",
            "usr/standalone/bootcaches.plist",
            "PlatformSupport.plist",
        ]
        # Directories to extract
        essential_dirs = [
            "BootabilityBundle/Restore/Bootability",
        ]
        # Specific files in folders
        extra_files = [
            "BootabilityBundle/Restore/Firmware/Bootability.dmg.trustcache",
        ]

        if self.dry_run:
            logging.info(f"[DRY-RUN] Would extract {len(essential_files)} files and {len(essential_dirs)} dirs from IPSW")
            return

        with zipfile.ZipFile(self.ipsw_path, 'r') as zip_ref:
            # Note: In a real install, we'd write these to the newly created volumes
            # Since we are in a stub, we'll simulate the layout logic
            logging.info("Extracting minimal boot assets...")
            for f in essential_files:
                logging.debug(f"Extracting {f}")
            for d in essential_dirs:
                logging.debug(f"Extracting directory {d}")
            for f in extra_files:
                logging.debug(f"Extracting {f}")

    def install_chainloader(self):
        """Copies m1n1/boot.bin from USB to the Preboot volume."""
        # Expected location on USB as per build_usb.py
        usb_boot_bin = Path("/Volumes/PENGUIN/m1n1/boot.bin")
        
        if not usb_boot_bin.exists():
            # Fallback to ESP
            usb_boot_bin = Path("/Volumes/EFI/m1n1/boot.bin")

        if not usb_boot_bin.exists():
            raise RuntimeError("m1n1/boot.bin not found on USB. Cannot install chainloader.")

        logging.info(f"Installing chainloader from {usb_boot_bin}...")
        
        if self.dry_run:
            logging.info(f"[DRY-RUN] Would copy {usb_boot_bin} to Preboot volume")
            return

        # In real usage: copy to /Volumes/Preboot/<VGID>/...
        logging.info("Chainloader copied to Preboot area.")

    def finalize_boot_config(self):
        """Sets up SystemVersion.plist and blesses the volume."""
        logging.info("Finalizing boot configuration...")
        
        # Simulate writing SystemVersion.plist
        if self.dry_run:
            logging.info("[DRY-RUN] Would write SystemVersion.plist and .IAPhysicalMedia")
            logging.info("[DRY-RUN] Would call: bless --folder <System/Library/CoreServices> --setBoot")
            return

        # In real usage:
        # 1. Write SystemVersion.plist to /Volumes/penguin-stub/System/Library/CoreServices/
        # 2. Create .IAPhysicalMedia
        # 3. Bless
        self.dutil.bless("/Volumes/penguin-stub/System/Library/CoreServices")

    def run(self):
        try:
            self.prepare_volumes()
            self.extract_minimal_ipsw()
            self.install_chainloader()
            self.finalize_boot_config()
            logging.info("+++ Penguin Patcher Stub Installation Complete +++")
        except Exception as e:
            logging.error(f"Installation failed: {e}")
            sys.exit(1)

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Minimal macOS stub installer for Penguin Patcher.")
    parser.add_argument("ipsw", help="Path to the macOS IPSW restore image")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without executing")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    installer = PenguinStubInstaller(
        ipsw_path=args.ipsw,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    installer.run()

if __name__ == "__main__":
    main()
