#!/usr/bin/env bash
# Build a live squashfs rootfs for the chosen distro.
set -euo pipefail

DISTRO="${1:-fedora}"
OUT="${2:-$(pwd)/../penguin-build/out/rootfs.squashfs}"
WORK="$(mktemp -d)"

PROFILE="$(pwd)/usb-maker/profiles/$DISTRO/profile.json"
if [[ ! -f "$PROFILE" ]]; then
  echo "Unknown distro profile: $PROFILE" >&2
  exit 1
fi

echo "[make-rootfs] Building $DISTRO rootfs..."

# TODO: bootstrap distro chroot, install Asahi kernel modules + firmware,
# copy profile package list, configure live boot services.

# Placeholder: create an empty marker squashfs
mkdir -p "$WORK/live"
echo "$DISTRO placeholder rootfs" > "$WORK/live/README"
mksquashfs "$WORK" "$OUT" -noappend -quiet
rm -rf "$WORK"

echo "Rootfs written to $OUT"
