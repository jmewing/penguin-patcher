#!/usr/bin/env bash
# Build a Penguin Patcher initramfs.
# This initrd finds the USB live rootfs, mounts it via overlayfs, and switches root.
set -euo pipefail

DISTRO="${1:-debian}"
OUT="${2:-$(pwd)/../penguin-build/out/initrd.img}"
WORK="$(mktemp -d)"

mkdir -p "$WORK/bin" "$WORK/sbin" "$WORK/etc" "$WORK/proc" "$WORK/sys" "$WORK/dev" \
         "$WORK/mnt" "$WORK/run" "$WORK/lib" "$WORK/lib64" "$WORK/usr/bin"

# Copy static binaries from the host if available, else warn
for bin in busybox sh bash mount umount switch_root modprobe sleep echo mkdir \
           ls cat grep sed awk ip dhclient; do
  if command -v "$bin" > /dev/null 2>&1; then
    cp "$(command -v "$bin")" "$WORK/bin/" 2>/dev/null || true
  fi
done

# Try to install busybox if present
if command -v busybox > /dev/null 2>&1; then
  for applet in sh mount umount switch_root modprobe sleep echo mkdir ls cat grep sed awk; do
    ln -s busybox "$WORK/bin/$applet" 2>/dev/null || true
  done
fi

mkdir -p "$WORK/etc/dhcp"
cat > "$WORK/init" <<'EOF'
#!/bin/sh
# Penguin Patcher initramfs
set -e

mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mount -t tmpfs tmpfs /run
mkdir -p /run/lock

echo "Penguin Patcher initrd"

# Load modules for USB and storage
for mod in xhci_hcd usb_storage uas nvme apple_nvme squashfs overlay loop; do
  modprobe "$mod" 2>/dev/null || true
done

# Wait for USB to settle
sleep 3

# Find the live rootfs partition by label
ROOT_PART=""
for label in PENGUIN LIVEUSB ROOT; do
  ROOT_PART="$(findfs LABEL="$label" 2>/dev/null || true)"
  [ -n "$ROOT_PART" ] && break
done

if [ -z "$ROOT_PART" ]; then
  echo "ERROR: Could not find live rootfs partition"
  echo "Available block devices:"
  ls /dev/sd* /dev/nvme* /dev/mmcblk* /dev/ub* 2>/dev/null || true
  /bin/sh
  exit 1
fi

echo "Found live rootfs at $ROOT_PART"
mkdir -p /run/rootfs /run/overlay /run/work
mount -t auto "$ROOT_PART" /run/rootfs

# Look for squashfs image
ROOT_IMG=""
for path in /run/rootfs/live/rootfs.squashfs /run/rootfs/rootfs.squashfs /run/rootfs/squashfs; do
  [ -f "$path" ] && { ROOT_IMG="$path"; break; }
done

if [ -z "$ROOT_IMG" ]; then
  echo "ERROR: rootfs.squashfs not found on $ROOT_PART"
  ls -R /run/rootfs | head -30
  /bin/sh
  exit 1
fi

mount -t squashfs "$ROOT_IMG" /run/overlay -o ro,loop
mount -t tmpfs tmpfs /run/work
mkdir -p /run/work/upper /run/work/work
mkdir -p /run/newroot
mount -t overlay overlay /run/newroot \
  -o lowerdir=/run/overlay,upperdir=/run/work/upper,workdir=/run/work/work

# Move mounts into newroot
mkdir -p /run/newroot/run/penguin
mount --move /run/rootfs /run/newroot/run/penguin/usb 2>/dev/null || true
mount --move /run/overlay /run/newroot/run/penguin/overlay 2>/dev/null || true
mount --move /run/work /run/newroot/run/penguin/work 2>/dev/null || true
mount --move /run /run/newroot/run 2>/dev/null || true
mount --move /dev /run/newroot/dev 2>/dev/null || true
mount --move /proc /run/newroot/proc 2>/dev/null || true
mount --move /sys /run/newroot/sys 2>/dev/null || true

# Switch to real init
exec switch_root /run/newroot /sbin/init
EOF
chmod +x "$WORK/init"

OUT_ABS="$(realpath -m "$OUT")"

cd "$WORK"
find . | cpio -o -H newc | gzip -9 > "$OUT_ABS"
rm -rf "$WORK"

echo "Initrd written to $OUT"
