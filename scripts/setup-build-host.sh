#!/usr/bin/env bash
# Prepare a Debian/Ubuntu ARM64 host to build Asahi firmware.
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
  git build-essential bison flex libssl-dev libncurses-dev libelf-dev \
  bc kmod cpio gzip xz-utils squashfs-tools parted dosfstools hfsprogs \
  python3 python3-pip device-tree-compiler wget curl \
  libgnutls28-dev libclang-dev llvm clang

if ! command -v rustc > /dev/null 2>&1; then
  curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  . "$HOME/.cargo/env"
fi

rustup target add aarch64-unknown-none-softfloat
rustup component add rust-src
cargo install bindgen-cli

echo "Build host ready."
