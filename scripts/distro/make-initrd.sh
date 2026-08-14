#!/usr/bin/env bash
# Build a minimal initramfs for Penguin Patcher.
set -euo pipefail

DISTRO="${1:-fedora}"
OUT="${2:-$(pwd)/../penguin-build/out/initrd.img}"
WORK="$(mktemp -d)"

mkdir -p "$WORK/bin" "$WORK/sbin" "$WORK/etc" "$WORK/proc" "$WORK/sys" "$WORK/dev" "$WORK/mnt" "$WORK/run"

# Minimal busybox-like initrd placeholder
cat > "$WORK/init" <<'EOF'
#!/bin/sh
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /run
exec /bin/sh
EOF
chmod +x "$WORK/init"

# TODO: add real init, distro-specific setup, overlay root, USB rootfs detection

cd "$WORK"
find . | cpio -o -H newc | gzip -9 > "$OUT"
rm -rf "$WORK"

echo "Initrd written to $OUT"
