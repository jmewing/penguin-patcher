#!/usr/bin/env bash
# Penguin Patcher full build orchestrator
set -euo pipefail

DISTRO="${1:-fedora}"
DEVICE="${2:-j274}"
OUT_DIR="$(pwd)/build-${DISTRO}-${DEVICE}"

mkdir -p "$OUT_DIR"

echo "[build-all] distro=$DISTRO device=$DEVICE out=$OUT_DIR"

PROFILE="usb-maker/profiles/${DISTRO}/profile.json"
if [[ ! -f "$PROFILE" ]]; then
  echo "[build-all] Unknown distro profile: $PROFILE" >&2
  exit 1
fi

echo "[build-all] Using profile: $PROFILE"

# 1. Build/patch kernel with distro-specific config
# ./kernel-builder/scripts/build-kernel.sh \
#   --distro "$DISTRO" \
#   --device "$DEVICE" \
#   --config "kernel-builder/configs/common.config" \
#   --config "kernel-builder/configs/${DISTRO}.config" \
#   --out "$OUT_DIR/kernel"

# 2. Create initrd + squashfs rootfs
# ./scripts/distro/make-initrd.sh --distro "$DISTRO" --out "$OUT_DIR/initrd.img"
# ./scripts/distro/make-rootfs.sh --distro "$DISTRO" --profile "$PROFILE" --out "$OUT_DIR/rootfs.squashfs"

# 3. Fetch/provide m1n1 + u-boot binaries for device
# ./scripts/fetch-asahi-firmware.sh --device "$DEVICE" --out "$OUT_DIR/firmware"

# 4. Build the USB image
# python3 ./usb-maker/build_usb.py \
#   --distro "$DISTRO" \
#   --device "$DEVICE" \
#   --kernel "$OUT_DIR/kernel/Image" \
#   --initrd "$OUT_DIR/initrd.img" \
#   --dtb "$OUT_DIR/kernel/dtb" \
#   --uboot "$OUT_DIR/firmware/u-boot-nodtb.bin.gz" \
#   --m1n1 "$OUT_DIR/firmware/m1n1.bin" \
#   --grub "$OUT_DIR/grub/BOOTAA64.EFI" \
#   --installer-app "./installer/Penguin Patcher.app" \
#   --out "$OUT_DIR/penguin-patcher-${DISTRO}-${DEVICE}.img"

echo "[build-all] Placeholder complete for distro=$DISTRO. Implement each step above."
