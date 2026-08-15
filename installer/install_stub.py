#!/usr/bin/env python3
"""
Penguin Patcher — minimal macOS m1n1 Stage 1 installer.

Installs a tiny, reversible boot stub on an Apple Silicon Mac's internal SSD.
The stub volume is blessed so it appears in the Apple boot picker; it
chainloads m1n1 Stage 2 from a Penguin Patcher USB drive.

This intentionally does NOT install a full macOS stub OS. It only creates a
small APFS volume, copies the already-built m1n1 Stage 2 chainloader, and
blesses it. Layout and logic are derived from the Asahi Linux installer
(vendored under vendor/asahi-installer/).

Run on macOS only. Requires root/sudo for diskutil & bless.
"""

import argparse
import logging
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

# Size constants
GIB = 1024 * 1024 * 1024
STUB_SIZE_GB = 3
FREE_THRESHOLD = 256 * 1024 * 1024  # 256 MiB


def run(cmd, check=True, capture=True, dry_run=False):
    """Run a subprocess command, optionally logging in dry-run mode."""
    cmd_str = " ".join(str(c) for c in cmd)
    logging.debug(f"run: {cmd_str}")
    if dry_run:
        print(f"[DRY-RUN] {cmd_str}")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
    kwargs = {"check": check}
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT
    return subprocess.run(cmd, **kwargs)


def load_plist(cmd):
    """Run a command that returns a plist and parse it."""
    p = run(cmd, capture=True, check=True)
    return plistlib.loads(p.stdout)


class DiskUtil:
    """Thin wrapper around /usr/sbin/diskutil with plist parsing."""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.disk_list = {}
        self.disk_parts = {}
        self.ctnr_by_store = {}
        self.ctnr_by_ref = {}

    def get(self, *args):
        return load_plist(["/usr/sbin/diskutil"] + list(args))

    def action(self, *args):
        return run(["/usr/sbin/diskutil"] + list(args), dry_run=self.dry_run)

    def get_info(self):
        self.disk_list = self.get("list", "-plist")
        self.disk_parts = {
            dsk["DeviceIdentifier"]: dsk
            for dsk in self.disk_list["AllDisksAndPartitions"]
        }
        apfs = self.get("apfs", "list", "-plist")
        for ctnr in apfs.get("Containers", []):
            self.ctnr_by_store[ctnr["DesignatedPhysicalStore"]] = ctnr
            self.ctnr_by_ref[ctnr["ContainerReference"]] = ctnr

    def find_system_disk(self):
        """Return the internal whole-disk identifier (e.g. disk0)."""
        # Prefer a whole disk whose first partition is Apple_APFS_ISC and is
        # confirmed internal via diskutil info. macOS 24.x no longer reliably
        # includes Internal/Virtual in diskutil list -plist.
        for dsk in self.disk_list["AllDisksAndPartitions"]:
            name = dsk["DeviceIdentifier"]
            if dsk.get("Content") == "Apple_APFS_Container":
                continue
            parts = dsk.get("Partitions", [])
            if not (parts and parts[0].get("Content") == "Apple_APFS_ISC"):
                continue
            try:
                info = self.get("info", "-plist", name)
                if info.get("Internal"):
                    logging.info(f"Found system disk: {name}")
                    return name
            except Exception:
                continue
        # Fallback: assume the first matching GUID disk is the internal one.
        for dsk in self.disk_list["AllDisksAndPartitions"]:
            name = dsk["DeviceIdentifier"]
            if dsk.get("Content") == "Apple_APFS_Container":
                continue
            parts = dsk.get("Partitions", [])
            if parts and parts[0].get("Content") == "Apple_APFS_ISC":
                logging.info(f"Found system disk (fallback): {name}")
                return name
        raise RuntimeError("Could not find internal system disk (Apple_APFS_ISC)")

    def _find_store_partition(self, sys_disk, store_id):
        """Locate a partition dict by its device identifier within sys_disk."""
        dsk = self.disk_parts.get(sys_disk, {})
        for part in dsk.get("Partitions", []):
            if part.get("DeviceIdentifier") == store_id:
                return part
        return {}

    def find_system_container(self, sys_disk):
        """Return the main macOS APFS container reference on the system disk."""
        # The system disk has multiple APFS containers (iSC/Preboot, main data,
        # Recovery). We want the one backed by the main Apple_APFS physical store.
        for dev_id, ctnr in self.ctnr_by_store.items():
            if not dev_id.startswith(sys_disk):
                continue
            part = self._find_store_partition(sys_disk, dev_id)
            if part.get("Content") == "Apple_APFS":
                return ctnr["ContainerReference"]
        # Fallback: scan all containers.
        apfs = self.get("apfs", "list", "-plist")
        for ctnr in apfs.get("Containers", []):
            store = ctnr.get("DesignatedPhysicalStore", "")
            if not store.startswith(sys_disk):
                continue
            part = self._find_store_partition(sys_disk, store)
            if part.get("Content") == "Apple_APFS":
                return ctnr["ContainerReference"]
        raise RuntimeError(f"Could not find main APFS container on {sys_disk}")

    def resize_container(self, container_id, free_gb):
        """Shrink the container by free_gb, leaving that space unallocated."""
        ctnr = self.get("apfs", "list", container_id, "-plist")["Containers"][0]
        store = ctnr.get("DesignatedPhysicalStore")
        if not store:
            raise RuntimeError(f"No physical store for container {container_id}")
        store_info = self.get("info", "-plist", store)
        current_size = store_info["TotalSize"]
        want_free = free_gb * GIB

        # Use diskutil resize limits to avoid over-shrinking
        limits = self.action("apfs", "resizeContainer", container_id, "limits").stdout.decode()
        min_size = None
        for line in limits.splitlines():
            if "Minimum (constrained by file/snapshot usage):" in line:
                try:
                    min_size = int(line.split("(")[-1].split(" Bytes")[0].replace(",", ""))
                except Exception:
                    pass
        if min_size is None:
            min_size = current_size - want_free * 2  # rough fallback

        safe_min = min_size + FREE_THRESHOLD
        new_size = current_size - want_free
        if new_size <= 0:
            raise RuntimeError(f"Computed new container size is invalid ({new_size} bytes)")
        if new_size < safe_min:
            avail = current_size - safe_min
            raise RuntimeError(
                f"Cannot free {free_gb} GB; only ~{avail / GIB:.1f} GB can be safely reclaimed"
            )
        new_size -= new_size % (4 * 1024 * 1024)
        logging.info(
            f"Resizing container {container_id} (store {store}) from {current_size} to {new_size} bytes"
        )
        self.action("apfs", "resizeContainer", container_id, str(new_size))
        return new_size

    def add_stub_volume(self, container_id, label="penguin-stub"):
        """Create a new APFS volume inside the container."""
        logging.info(f"Creating APFS volume '{label}' in {container_id}")
        self.action("apfs", "addVolume", container_id, "APFS", label)
        if self.dry_run:
            # In dry-run the volume does not exist; return a placeholder.
            return f"{container_id}sDRYRUN"
        apfs = self.get("apfs", "list", container_id, "-plist")
        for vol in apfs["Containers"][0]["Volumes"]:
            if vol["Name"] == label:
                return vol["DeviceIdentifier"]
        raise RuntimeError(f"Failed to locate created volume '{label}'")

    def mount_volume(self, vol_id):
        self.action("mount", vol_id)
        info = self.get("info", "-plist", vol_id)
        return info["MountPoint"]

    def unmount_volume(self, vol_id):
        self.action("unmount", vol_id)


def detect_hardware():
    arch = os.uname().machine
    if arch != "arm64":
        raise RuntimeError(f"This installer requires Apple Silicon (found {arch})")
    try:
        target = subprocess.check_output(["/usr/sbin/sysctl", "-n", "hw.target"], text=True).strip()
    except Exception:
        target = "unknown"
    try:
        model = subprocess.check_output(["/usr/sbin/sysctl", "-n", "hw.model"], text=True).strip()
    except Exception:
        model = "unknown"
    logging.info(f"Detected Apple Silicon: {model} (target: {target})")
    return model, target


def find_penguin_usb():
    """Find the mounted Penguin Patcher USB volume by label or boot.bin presence."""
    data = load_plist(["/usr/sbin/diskutil", "list", "-plist"])

    # macOS may report VolumeName/MountPoint either on the partition itself
    # or nested under a 'Volumes' array. Collect every candidate named PENGUIN.
    candidates = []
    for dsk in data["AllDisksAndPartitions"]:
        for part in dsk.get("Partitions", []):
            if part.get("VolumeName") == "PENGUIN":
                candidates.append(part["DeviceIdentifier"])
            vols = part.get("Volumes", [])
            if not isinstance(vols, list):
                vols = [vols] if vols else []
            for vol in vols:
                if vol.get("VolumeName") == "PENGUIN":
                    candidates.append(vol["DeviceIdentifier"])

    # Confirm mount point and m1n1 Stage 2 presence via diskutil info
    for dev in candidates:
        try:
            info = load_plist(["/usr/sbin/diskutil", "info", "-plist", dev])
            mp = info.get("MountPoint")
            if mp and Path(mp, "m1n1/boot.bin").exists():
                logging.info(f"Found Penguin USB at {mp} ({dev})")
                return Path(mp)
        except Exception:
            continue

    # Fallback: scan /Volumes for boot.bin
    for p in Path("/Volumes").glob("*/m1n1/boot.bin"):
        mp = p.parent.parent
        logging.info(f"Found Penguin USB at {mp} (via boot.bin)")
        return mp

    raise RuntimeError(
        "Penguin Patcher USB not found. Plug in the USB drive and ensure it is mounted."
    )


def install_stub_files(usb_path, stub_mount):
    """Populate the stub volume with the files the boot picker needs."""
    stub_mount = Path(stub_mount)
    core_services = stub_mount / "System/Library/CoreServices"
    core_services.mkdir(parents=True, exist_ok=True)

    # SystemVersion.plist — makes bless/ boot picker treat this as a real OS stub
    sv = {
        "ProductBuildVersion": "21A335",
        "ProductCopyright": "1983-2026 Apple Inc.",
        "ProductName": "macOS",
        "ProductUserVisibleVersion": "12.1 (Penguin Stub)",
        "ProductVersion": "12.1",
    }
    with open(core_services / "SystemVersion.plist", "wb") as f:
        plistlib.dump(sv, f)

    # m1n1 Stage 2 chainloader from the USB ESP
    src_boot = usb_path / "m1n1/boot.bin"
    if not src_boot.exists():
        raise RuntimeError(f"USB missing m1n1 Stage 2 at {src_boot}")
    dst_dir = stub_mount / "m1n1"
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_boot, dst_dir / "boot.bin")
    logging.info(f"Installed m1n1 Stage 2 ({src_boot.stat().st_size} bytes)")

    # .IAPhysicalMedia — marks the volume as bootable installation media
    iapm = {
        "AppName": "Penguin Patcher",
        "ProductBuildVersion": "21A335",
        "ProductVersion": "12.1",
    }
    with open(stub_mount / ".IAPhysicalMedia", "wb") as f:
        plistlib.dump(iapm, f)

    # Boot picker needs a visible icon / boot.efi-ish structure. A stub
    # SystemVersion is sufficient for bless on Apple Silicon in most cases.
    logging.info("Stub volume populated.")


def bless_volume(stub_mount, dry_run=False):
    core_services = Path(stub_mount) / "System/Library/CoreServices"
    if not core_services.exists():
        raise RuntimeError(f"Missing {core_services}; cannot bless")
    logging.info(f"Blessing stub volume at {core_services}")
    run(
        ["/usr/sbin/bless", "--folder", str(core_services), "--setBoot"],
        dry_run=dry_run,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Install Penguin Patcher m1n1 Stage 1 stub on Apple Silicon."
    )
    parser.add_argument(
        "--usb",
        help="Path to mounted Penguin Patcher USB volume (auto-detected if omitted)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=STUB_SIZE_GB,
        help="GB to free for the stub container (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print diskutil/bless commands without executing them",
    )
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    if os.geteuid() != 0 and not args.dry_run:
        print(
            "WARNING: This installer must run as root on macOS. Use: sudo python3 install_stub.py",
            file=sys.stderr,
        )

    try:
        detect_hardware()

        dutil = DiskUtil(dry_run=args.dry_run)
        dutil.get_info()

        usb_path = Path(args.usb) if args.usb else find_penguin_usb()
        if not (usb_path / "m1n1/boot.bin").exists():
            raise RuntimeError(f"m1n1/boot.bin not found on USB at {usb_path}")

        sys_disk = dutil.find_system_disk()
        container_id = dutil.find_system_container(sys_disk)

        dutil.resize_container(container_id, args.size)
        stub_vol = dutil.add_stub_volume(container_id)

        if args.dry_run:
            print("[DRY-RUN] Would mount stub volume, install files, and bless.")
            return 0

        stub_mount = dutil.mount_volume(stub_vol)
        try:
            install_stub_files(usb_path, stub_mount)
            bless_volume(stub_mount, dry_run=args.dry_run)
        finally:
            dutil.unmount_volume(stub_vol)

        print("\n[ok] Penguin stub installed.")
        print("Shutdown, then hold the Power button until 'Loading startup options' appears.")
        print('Select the "Penguin" entry to chainload Linux from the USB drive.')
        return 0

    except Exception as e:
        logging.error(f"Installation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
