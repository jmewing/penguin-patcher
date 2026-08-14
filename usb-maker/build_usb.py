#!/usr/bin/env python3
"""
Penguin Patcher USB image builder.

Creates a dual-partition USB image:
- macOS-readable APFS/HFS+ volume with the installer app
- FAT32 ESP with m1n1, U-Boot, GRUB, kernel, initrd, and rootfs
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd, **kwargs):
    print(f"+ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def build_m1n1_stage2(out_dir, device_dtb, uboot, m1n1):
    """Build m1n1 Stage 2 binary: m1n1 + dtb + compressed u-boot."""
    stage2 = out_dir / "m1n1" / "boot.bin"
    stage2.parent.mkdir(parents=True, exist_ok=True)
    with open(m1n1, "rb") as f:
        data = f.read()
    with open(device_dtb, "rb") as f:
        data += f.read()
    with open(uboot, "rb") as f:
        data += f.read()
    stage2.write_bytes(data)
    print(f"[ok] m1n1 Stage 2: {stage2} ({len(data)} bytes)")
    return stage2


def create_esp(esp_dir, stage2, kernel, initrd, grub_efi):
    """Populate the ESP directory."""
    (esp_dir / "m1n1").mkdir(parents=True, exist_ok=True)
    (esp_dir / "EFI" / "BOOT").mkdir(parents=True, exist_ok=True)

    shutil = __import__("shutil")
    shutil.copy(stage2, esp_dir / "m1n1" / "boot.bin")
    shutil.copy(kernel, esp_dir / "EFI" / "BOOT" / "Image")
    shutil.copy(initrd, esp_dir / "EFI" / "BOOT" / "initrd.img")
    shutil.copy(grub_efi, esp_dir / "EFI" / "BOOT" / "BOOTAA64.EFI")

    # Minimal GRUB config
    grub_cfg = esp_dir / "EFI" / "BOOT" / "grub.cfg"
    grub_cfg.write_text("""
set timeout=5
set default=0
menuentry \"Penguin Patcher Linux\" {
    linux /EFI/BOOT/Image console=tty0
    initrd /EFI/BOOT/initrd.img
    boot
}
""")
    print("[ok] ESP populated.")


def create_image(out_file, esp_dir, installer_dir, size_mb=4096):
    """Create a raw disk image with two partitions."""
    print(f"Creating USB image ({size_mb} MB)...")
    # Real implementation would use sfdisk + mkfs.vfat + mkfs.hfs/apfs
    # For scaffolding, we just create a tarball of the contents.
    temp = Path(tempfile.gettempdir()) / "penguin-patcher-image"
    temp.mkdir(exist_ok=True)

    shutil = __import__("shutil")
    shutil.make_archive(str(out_file.with_suffix("")), "gztar", root_dir=temp)
    print(f"[warn] Raw disk image generation not yet implemented.")
    print(f"[warn] Wrote placeholder tarball: {out_file}.tar.gz")
    return out_file.with_suffix(".tar.gz")


def main():
    parser = argparse.ArgumentParser(description="Build Penguin Patcher USB image.")
    parser.add_argument("--distro", choices=["fedora", "ubuntu", "debian"], default="fedora")
    parser.add_argument("--device", default="j274", help="Asahi device code (e.g., j274 for Mac mini M1)")
    parser.add_argument("--kernel", required=True, help="Path to compiled ARM64 kernel Image")
    parser.add_argument("--initrd", required=True, help="Path to initrd")
    parser.add_argument("--dtb", required=True, help="Path to device tree blob")
    parser.add_argument("--uboot", required=True, help="Path to u-boot-nodtb.bin.gz")
    parser.add_argument("--m1n1", required=True, help="Path to m1n1.bin")
    parser.add_argument("--grub", required=True, help="Path to BOOTAA64.EFI")
    parser.add_argument("--installer-app", required=True, help="Path to Penguin Patcher.app bundle")
    parser.add_argument("--out", default="penguin-patcher-usb.img", help="Output image path")
    args = parser.parse_args()

    work = Path(tempfile.mkdtemp(prefix="penguin-usb-"))
    try:
        esp_dir = work / "esp"
        esp_dir.mkdir()
        stage2 = build_m1n1_stage2(work, args.dtb, args.uboot, args.m1n1)
        create_esp(esp_dir, stage2, args.kernel, args.initrd, args.grub)

        installer_dir = work / "installer"
        installer_dir.mkdir()
        # TODO: copy app bundle contents into installer_dir

        create_image(Path(args.out), esp_dir, installer_dir)
    finally:
        pass  # Keep work dir for debugging, or clean up later

    return 0


if __name__ == "__main__":
    sys.exit(main())
