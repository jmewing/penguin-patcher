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


def populate_installer(installer_dir, repo_root):
    """Populate the macOS-readable installer volume directory."""
    repo_root = Path(repo_root)
    readme = installer_dir / 'README.txt'
    readme.write_text("""
Penguin Patcher USB
===================

Before you start (do these first)
---------------------------------
1. Disable Find My Mac. Activation Lock can block Recovery mode boot and disk
   changes. System Settings -> Apple ID -> iCloud -> Find My Mac -> Off.
2. Turn off FileVault if it is enabled. Encrypted disks may prevent live APFS
   resizing. System Settings -> Privacy & Security -> FileVault -> Turn Off.
3. If a firmware password or MDM profile is set, remove it. These block the
   boot picker and external boot.
4. Back up your data. The installer preserves your macOS container, but any
   disk modification carries risk.

Install the stub
----------------
1. Plug this USB into your Apple Silicon Mac running macOS 12.1 or later.
2. Open this volume in Finder and double-click "Penguin Patcher.app".
3. A Terminal window opens. Enter your password when prompted for sudo.
4. The installer resizes your internal APFS container and creates a small
   reversible boot stub named "penguin-stub".
5. Shut down, then hold the Power button until "Loading startup options" appears.
6. Choose "Penguin" from the boot picker to chainload Linux from this USB.

To remove the stub, boot to macOS Recovery, open Disk Utility, and delete
"penguin-stub" from the internal SSD.
""")
    app_src = repo_root / 'installer' / 'Penguin Patcher.app'
    script_src = repo_root / 'installer' / 'install_stub.py'
    if app_src.exists():
        shutil.copytree(app_src, installer_dir / app_src.name, dirs_exist_ok=True)
        print(f"[ok] Copied {app_src.name}")
    else:
        print(f"[warn] App bundle not found at {app_src}")
    if script_src.exists():
        shutil.copy2(script_src, installer_dir / script_src.name)
        print(f"[ok] Copied {script_src.name}")
    else:
        print(f"[warn] Installer script not found at {script_src}")
    print("[ok] Installer volume populated.")


def format_and_populate(part1, part2, esp_dir, installer_dir):
    """Format two partitions FAT32 and copy contents."""
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


def create_image(out_file, esp_dir, installer_dir, size_mb=4096):
    """Create a raw disk image with two FAT32 partitions."""
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    esp_size_mb = 512

    with tempfile.TemporaryDirectory(prefix="penguin-usb-") as tmp:
        img = Path(tmp) / "usb.img"
        run(["dd", "if=/dev/zero", f"of={img}", "bs=1M", f"count={size_mb}", "status=progress"])

        # Partition: ESP at 1MiB offset, installer fills the rest
        sfdisk_script = f"label: gpt\n"
        sfdisk_script += f"start=1MiB, size={esp_size_mb}MiB, type=uefi, name=EFI-ESP\n"
        sfdisk_script += f"type=EBD0A0A2-B9E5-4433-87C0-68B6B72699C7, name=PENGUIN-INST\n"
        run(["sfdisk", str(img)], input=sfdisk_script.encode())

        # Attach loop device with partition scan
        result = run(["losetup", "--show", "-Pf", str(img)], capture_output=True, text=True)
        loop = result.stdout.strip()
        try:
            import time
            time.sleep(1)
            format_and_populate(f"{loop}p1", f"{loop}p2", esp_dir, installer_dir)
        finally:
            run(["losetup", "-d", loop])

        shutil.copy(img, out_file)

    print(f"[ok] USB image: {out_file}")
    return out_file


def write_device(device_node, esp_dir, installer_dir, size_mb=4096):
    """Partition and populate a block device directly (e.g. /dev/sda)."""
    node = Path(device_node)
    if not node.exists() or not node.is_block_device():
        raise RuntimeError(f"{device_node} is not a block device")

    esp_size_mb = 512
    run(["sfdisk", "--wipe=always", "--wipe-partitions=always", str(node)],
        input=f"label: gpt\n"
              f"start=1MiB, size={esp_size_mb}MiB, type=uefi, name=EFI-ESP\n"
              f"type=EBD0A0A2-B9E5-4433-87C0-68B6B72699C7, name=PENGUIN-INST\n".encode())

    # Wait for partition nodes
    import time
    time.sleep(2)

    # Determine partition names (sdX1/sdX2 or sda1/sda2 style)
    if str(node).startswith("/dev/sd") or str(node).startswith("/dev/vd"):
        part1 = f"{node}1"
        part2 = f"{node}2"
    else:
        part1 = f"{node}p1"
        part2 = f"{node}p2"

    if not Path(part1).exists() or not Path(part2).exists():
        raise RuntimeError(f"Partition nodes {part1}, {part2} did not appear")

    format_and_populate(part1, part2, esp_dir, installer_dir)
    run(["sync"])
    print(f"[ok] USB device written: {device_node}")
    return device_node


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
    parser.add_argument("--installer-app", help=argparse.SUPPRESS)
    parser.add_argument("--repo-root", default=str(Path(__file__).parent.parent), help="Path to penguin-patcher repo")
    parser.add_argument("--out", default="penguin-patcher-usb.img", help="Output image path")
    parser.add_argument("--device-node", help="Block device to partition and write directly (e.g. /dev/sda)")
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
        populate_installer(installer_dir, args.repo_root)

        if args.device_node:
            write_device(args.device_node, esp_dir, installer_dir, args.size)
        else:
            create_image(Path(args.out), esp_dir, installer_dir, args.size)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
