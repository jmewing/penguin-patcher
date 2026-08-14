#!/usr/bin/env bash
# Penguin Patcher full build orchestrator (placeholder)
set -euo pipefail

DISTRO="${1:-fedora}"
DEVICE="${2:-j274}"
OUT_DIR="$(pwd)/build-${DISTRO}-${DEVICE}"

mkdir -p "$OUT_DIR"

echo "[build-all] distro=$DISTRO device=$DEVICE out=$OUT_DIR"

# 1. Build/patch kernel
# ./kernel-builder/scripts/build-kernel.sh --distro "$DISTRO" --device "$DEVICE" --out "$OUT_DIR/kernel"

# 2. Create initrd + squashfs
# ./scripts/make-initrd.sh --distro "$DISTRO" --modules "$OUT_DIR/kernel/modules" --out "$OUT_DIR/initrd.img"
# ./scripts/make-rootfs.sh --distro "$DISTRO" --out "$OUT_DIR/rootfs.squashfs"

# 3. Build m1n1 Stage 2
# python3 ./usb-maker/build_usb.py \
#   --distro "$DISTRO" \
#   --device "$DEVICE" \
#   --kernel "$OUT_DIR/kernel/Image" \
#   --initrd "$OUT_DIR/initrd.img" \
#   --dtb "$OUT_DIR/kernel/dtb" \
#   --uboot "$OUT_DIR/uboot/u-boot-nodtb.bin.gz" \
#   --m1n1 "$OUT_DIR/m1n1/m1n1.bin" \
#   --grub "$OUT_DIR/grub/BOOTAA64.EFI" \
#   --installer-app "./installer/Penguin Patcher.app" \
#   --out "$OUT_DIR/penguin-patcher-${DISTRO}-${DEVICE}.img"

echo "[build-all] Placeholder complete. Implement each step above."
