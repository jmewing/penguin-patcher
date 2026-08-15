#!/usr/bin/env bash
# Build a minimal Debian ARM64 squashfs rootfs with SSH-first boot.
# Run this on an ARM64 host (Raspberry Pi or Apple Silicon Linux).
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[make-rootfs] Re-running with sudo..."
  exec sudo "$0" "$@"
fi

DISTRO="${1:-debian}"
OUT="${2:-$(pwd)/../penguin-build/out/rootfs.squashfs}"
MODULES_DIR="${3:-}"
WORK="$(mktemp -d)"
MIRROR="${MIRROR:-http://deb.debian.org/debian}"
SUITE="${SUITE:-trixie}"

mkdir -p "$WORK"

echo "[make-rootfs] Creating $DISTRO rootfs at $WORK"

# Bootstrap minimal Debian
if command -v mmdebstrap > /dev/null 2>&1; then
  mmdebstrap --variant=minbase \
    --include=openssh-server,iproute2,iputils-ping,isc-dhcp-client,curl,wget,vim-tiny,less,kmod,udev,procps,netbase \
    "$SUITE" "$WORK" "$MIRROR"
else
  debootstrap --variant=minbase \
    --include=openssh-server,iproute2,iputils-ping,isc-dhcp-client,curl,wget,vim-tiny,less,kmod,udev,procps,netbase \
    "$SUITE" "$WORK" "$MIRROR"
fi

# Install Asahi kernel modules if provided
if [ -n "$MODULES_DIR" ] && [ -d "$MODULES_DIR" ]; then
  echo "[make-rootfs] Copying kernel modules..."
  mkdir -p "$WORK/lib/modules"
  cp -a "$MODULES_DIR"/* "$WORK/lib/modules/" 2>/dev/null || true
fi

# Setup networking
mkdir -p "$WORK/etc/network/interfaces.d"
cat > "$WORK/etc/network/interfaces" <<'EOF'
auto lo
iface lo inet loopback

allow-hotplug eth0
iface eth0 inet dhcp

allow-hotplug wlan0
iface wlan0 inet dhcp
EOF

# Setup root login with key or password
mkdir -p "$WORK/root/.ssh"
if [ -f "$HOME/.ssh/id_rsa.pub" ] || [ -f "$HOME/.ssh/id_ed25519.pub" ]; then
  cat "$HOME/.ssh/"*.pub > "$WORK/root/.ssh/authorized_keys" 2>/dev/null || true
  chmod 700 "$WORK/root/.ssh"
  chmod 600 "$WORK/root/.ssh/authorized_keys"
  echo "[make-rootfs] Installed root SSH keys"
fi

# Fallback password (CHANGE THIS)
echo 'root:penguin' | sudo chroot "$WORK" chpasswd

# Enable SSH on boot
sudo chroot "$WORK" systemctl enable ssh 2>/dev/null || true
sudo chroot "$WORK" update-rc.d ssh enable 2>/dev/null || true
mkdir -p "$WORK/etc/ssh"
cat > "$WORK/etc/ssh/sshd_config" <<'EOF'
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
EOF

# Hostname
sudo chroot "$WORK" bash -c "echo 'penguin-live' > /etc/hostname"

# Add a motd
cat > "$WORK/etc/motd" <<'EOF'
Penguin Patcher live environment.
Run 'ip a' to find this host's address, then SSH in as root.
EOF

# Create live directory structure for squashfs placement
mkdir -p "$WORK/live"

# Build squashfs
mksquashfs "$WORK" "$OUT" -noappend -quiet -e boot
rm -rf "$WORK"

echo "Rootfs written to $OUT"
