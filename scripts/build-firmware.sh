#!/usr/bin/env bash
# Build m1n1, u-boot, and the Asahi kernel for a target device.
# Run this on an ARM64 build host (e.g., Debian/Ubuntu on a Raspberry Pi).
set -euo pipefail

DEVICE="${1:-j274}"
OUT_DIR="${2:-$(pwd)/../penguin-build/out/$DEVICE}"
SRC_DIR="$(pwd)/../penguin-build/src"
JOBS="$(nproc)"

. "$HOME/.cargo/env" 2>/dev/null || true
export LIBCLANG_PATH="${LIBCLANG_PATH:-/usr/lib/llvm-19/lib}"

mkdir -p "$OUT_DIR"

echo "[build-firmware] device=$DEVICE out=$OUT_DIR"

# Build m1n1 Stage 2
if [[ ! -f "$OUT_DIR/m1n1.bin" ]]; then
  echo "[build-firmware] Building m1n1..."
  cd "$SRC_DIR/m1n1"
  make clean
  make -j"$JOBS"
  cp build/m1n1.bin "$OUT_DIR/"
fi

# Build U-Boot for the device
if [[ ! -f "$OUT_DIR/u-boot-nodtb.bin.gz" ]]; then
  echo "[build-firmware] Building U-Boot..."
  cd "$SRC_DIR/u-boot-asahi"
  make distclean
  make apple_m1_defconfig
  make -j"$JOBS"
  gzip -9 -c u-boot-nodtb.bin > "$OUT_DIR/u-boot-nodtb.bin.gz"
  cp "dts/upstream/src/arm64/apple/t8103-${DEVICE}.dtb" "$OUT_DIR/" || \
    cp "arch/arm/dts/t8103-${DEVICE}.dtb" "$OUT_DIR/"
fi

# Build Asahi kernel
if [[ ! -f "$OUT_DIR/Image" ]]; then
  echo "[build-firmware] Building Asahi kernel..."
  cd "$SRC_DIR/linux-asahi"
  cp arch/arm64/configs/asahi.config .config
  make olddefconfig
  make -j"$JOBS" Image modules dtbs
  cp arch/arm64/boot/Image "$OUT_DIR/"
  cp "arch/arm64/boot/dts/apple/t8103-${DEVICE}.dtb" "$OUT_DIR/" || true
  make modules_install INSTALL_MOD_PATH="$OUT_DIR/modules"
fi

echo "[build-firmware] Done. Artifacts in $OUT_DIR:"
ls -la "$OUT_DIR"
