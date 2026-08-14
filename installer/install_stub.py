#!/usr/bin/env python3
"""
Penguin Patcher macOS installer stub.

This script installs the m1n1 Stage 1 stub on the internal SSD of an
Apple Silicon Mac so that the system can chainload Linux from a Penguin
Patcher USB drive.

This is a placeholder/scaffold. The real implementation must reuse the
machine-specific logic from the Asahi Linux installer.
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def check_apple_silicon():
    """Verify we are running on Apple Silicon."""
    arch = platform.machine()
    if arch != "arm64":
        raise RuntimeError(f"This installer only runs on Apple Silicon (found {arch}).")
    print("[ok] Running on Apple Silicon.")


def get_machine_info():
    """Return machine model and other identifiers."""
    try:
        model = subprocess.check_output(
            ["/usr/sbin/system_profiler", "SPHardwareDataType", "-json"],
            text=True,
        )
        # TODO: parse JSON to extract machine_model, chip_type, etc.
    except Exception:
        pass
    try:
        model = subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "hw.target"], text=True
        ).strip()
    except Exception:
        model = "unknown"
    return {"machine_model": model}


def list_disks():
    """Show available internal APFS containers."""
    result = subprocess.run(
        ["/usr/sbin/diskutil", "list", "-plist", "internal"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Failed to list disks.")
    print(result.stdout[:500])


def resize_apfs_container(disk_id, size_gb):
    """Resize the internal APFS container to make room for the stub."""
    print(f"Resizing {disk_id} to free {size_gb} GB...")
    cmd = [
        "/usr/sbin/diskutil",
        "apfs",
        "resizeContainer",
        disk_id,
        f"{size_gb}G",
    ]
    # Real implementation needs to compute target size, not just free space.
    subprocess.run(cmd, check=True)


def create_stub_container(parent_disk, label="penguin-stub"):
    """Create a new APFS container for the m1n1 Stage 1 stub."""
    print(f"Creating APFS container '{label}'...")
    # TODO: use diskutil or asahi-installer partition logic.
    subprocess.run(
        ["/usr/sbin/diskutil", "apfs", "addVolume", parent_disk, "APFS", label],
        check=True,
    )


def install_m1n1_stage1(stub_volume, usb_esp):
    """Install machine-specific m1n1 Stage 1 into the stub container."""
    print(f"Installing m1n1 Stage 1 to {stub_volume}...")
    # TODO: call into Asahi installer's firmware/key handling.
    pass


def bless_stub(stub_volume):
    """Make the stub appear in the Apple boot picker."""
    print(f"Blessing {stub_volume}...")
    subprocess.run(
        ["/usr/sbin/bless", "--folder", str(stub_volume / "System/Library/CoreServices"), "--setBoot"],
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Install Penguin Patcher boot stub.")
    parser.add_argument("--usb", required=True, help="Path to mounted Penguin Patcher USB volume")
    parser.add_argument("--size", type=int, default=3, help="GB to free for stub container")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    args = parser.parse_args()

    check_apple_silicon()
    info = get_machine_info()
    print(f"[info] Machine model: {info['machine_model']}")
    print(f"[info] USB volume: {args.usb}")

    if args.dry_run:
        print("[dry-run] Would resize internal APFS container.")
        print("[dry-run] Would create penguin-stub container.")
        print("[dry-run] Would install m1n1 Stage 1.")
        print("[dry-run] Would bless the stub.")
        return 0

    # TODO: implement real disk selection and partitioning.
    list_disks()
    print("\n[warn] Real disk modification is not yet implemented.")
    print("[warn] Use Asahi Linux's official installer until this tool is complete.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
