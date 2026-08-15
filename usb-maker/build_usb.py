#!/usr/bin/env python3
"""
Penguin Patcher USB image builder.

Creates a raw disk image with:
- ESP (FAT32): m1n1 Stage 2, U-Boot, GRUB, kernel, initrd
- Installer volume (FAT32/exFAT): macOS installer app and README

Requires: sfdisk, mkfs.vfat, parted, mtools (optional), root or loop privileges.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd, **kwargs):
    print(f"+ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def build_m1n1_stage2(out_dir, device_dtb, uboot, m1n1):
    """Assemble m1n1 Stage 2: m1n1 + device dtb + compressed u-boot."""
    stage2 = out_dir / "m1n1" / "boot.bin"
    stage2.parent.mkdir(parents=True, exist_ok=True)
    data = Path(m1n1).read_bytes() + Path(device_dtb).read_bytes() + Path(uboot).read_bytes()
    stage2.write_bytes(data)
    print(f"[ok] m1n1 Stage 2: {stage2} ({len(data)} bytes)")
    return stage2


def populate_esp(esp_dir, stage2, kernel, initrd, grub_efi):
    """Populate the FAT32 ESP directory."""
    (esp_dir / "m1n1").mkdir(parents=True, exist_ok=True)
    (esp_dir / "EFI" / "BOOT").mkdir(parents=True, exist_ok=True)

    shutil.copy(stage2, esp_dir / "m1n1" / "boot.bin")
    shutil.copy(kernel, esp_dir / "EFI" / "BOOT" / "Image")
    shutil.copy(initrd, esp_dir / "EFI" / "BOOT" / "initrd.img")
    shutil.copy(grub_efi, esp_dir / "EFI" / "BOOT" / "BOOTAA64.EFI")

    grub_cfg = esp_dir / "EFI" / "BOOT" / "grub.cfg"
    grub_cfg.write_text("""
set timeout=5
set default=0
menuentry \"Penguin Patcher Linux\" {
    linux /EFI/BOOT/Image console=tty0 root=/dev/ram0
    initrd /EFI/BOOT/initrd.img
    boot
}
""")
    print("[ok] ESP populated.")


def populate_installer(installer_dir, installer_app=None):
    """Populate the installer volume directory."""
    readme = installer_dir / "README.txt"
    readme.write_text("""
Penguin Patcher USB
===================
1. Open the installer app on a Mac running macOS 12.1 or later.
2. Follow prompts to install the reversible m1n1 stub.
3. Reboot with this USB drive connected and hold the power button.
4. Select \"EFI Boot\" to start Linux.

To remove the stub, boot to macOS Recovery, open Disk Utility, and delete
\"penguin-stub\" from the internal SSD.
""")
    if installer_app and Path(installer_app).exists():
        shutil.copytree(installer_app, installer_dir / Path(installer_app).name, dirs_exist_ok=True)
    print("[ok] Installer volume populated.")


def create_image(out_file, esp_dir, installer_dir, size_mb=4096):
    """Create a raw disk image with two FAT32 partitions."""
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    size_bytes = size_mb * 1024 * 1024
    esp_size_mb = 512
    installer_size_mb = size_mb - esp_size_mb - 2

    with tempfile.TemporaryDirectory(prefix="penguin-usb-") as tmp:
        img = Path(tmp) / "usb.img"
        run(["dd", "if=/dev/zero", f"of={img}", "bs=1M", f"count={size_mb}", "status=progress"])

        # Partition: ESP at 1MiB offset, installer after
        sfdisk_script = f"label: gpt\n"
        sfdisk_script += f"start=1MiB, size={esp_size_mb}MiB, type=uefi, name=EFI-ESP\n"
        sfdisk_script += f"size={installer_size_mb}MiB, type=windows-basic-data, name=PENGUIN-INST\n"
        run(["sfdisk", str(img)], input=sfdisk_script.encode())

        # Attach loop device with partition scan
        result = run(["losetup", "--show", "-Pf", str(img)], capture_output=True, text=True)
        loop = result.stdout.strip()
        try:
            # Give kernel a moment to create partition nodes
            import time
            time.sleep(1)
            part1 = f"{loop}p1"
            part2 = f"{loop}p2"

            run(["mkfs.vfat", "-F32", "-n", "ESP", part1])
            run(["mkfs.vfat", "-F32", "-n", "PENGUIN", part2])

            with tempfile.TemporaryDirectory(prefix="penguin-esp-") as esp_mnt, \
                 tempfile.TemporaryDirectory(prefix="penguin-inst-") as inst_mnt:
                run(["mount", part1, esp_mnt])
                run(["mount", part2, inst_mnt])
                try:
                    shutil.copytree(esp_dir, esp_mnt, dirs_exist_ok=True)
                    shutil.copytree(installer_dir, inst_mnt, dirs_exist_ok=True)
                finally:
                    run(["umount", esp_mnt])
                    run(["umount", inst_mnt])
        finally:
            run(["losetup", "-d", loop])

        shutil.copy(img, out_file)

    print(f"[ok] USB image: {out_file}")
    return out_file


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
    parser.add_argument("--installer-app", help="Path to Penguin Patcher.app bundle (optional)")
    parser.add_argument("--out", default="penguin-patcher-usb.img", help="Output image path")
    parser.add_argument("--size", type=int, default=4096, help="USB image size in MB")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("[warn] This script uses losetup and mount; run as root or with sudo.", file=sys.stderr)

    work = Path(tempfile.mkdtemp(prefix="penguin-usb-"))
    try:
        esp_dir = work / "esp"
        esp_dir.mkdir()
        installer_dir = work / "installer"
        installer_dir.mkdir()

        stage2 = build_m1n1_stage2(work, args.dtb, args.uboot, args.m1n1)
        populate_esp(esp_dir, stage2, args.kernel, args.initrd, args.grub)
        populate_installer(installer_dir, args.installer_app)

        create_image(Path(args.out), esp_dir, installer_dir, args.size)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
