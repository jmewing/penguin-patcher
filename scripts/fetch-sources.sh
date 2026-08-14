#!/usr/bin/env bash
# Fetch Asahi Linux sources into a build directory.
set -euo pipefail

BUILD_DIR="${1:-$(pwd)/../penguin-build}"
SRC_DIR="$BUILD_DIR/src"

mkdir -p "$SRC_DIR"
cd "$SRC_DIR"

if [[ ! -d linux-asahi ]]; then
  git clone --depth 1 https://github.com/AsahiLinux/linux.git linux-asahi
fi

if [[ ! -d m1n1 ]]; then
  git clone --depth 1 https://github.com/AsahiLinux/m1n1.git
fi

if [[ ! -d u-boot-asahi ]]; then
  git clone --depth 1 https://github.com/AsahiLinux/u-boot.git u-boot-asahi
fi

echo "Sources ready in $SRC_DIR"
