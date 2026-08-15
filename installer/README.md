# Penguin Patcher macOS Installer

Installs the `m1n1` Stage 1 stub on an Apple Silicon Mac so it can boot Linux
from a Penguin Patcher USB drive.

## Before you start

1. **Disable Find My Mac.** Activation Lock can block Recovery mode boot and
disk changes. System Settings → Apple ID → iCloud → Find My Mac → Off.
2. **Turn off FileVault** if it is enabled. Encrypted disks may prevent live
APFS resizing. System Settings → Privacy & Security → FileVault → Turn Off.
3. **Remove firmware passwords or MDM profiles** if present. These block the
boot picker and external boot.
4. **Back up your data.** The installer preserves your macOS container, but any
disk modification carries risk.

## Usage

Double-click `Penguin Patcher.app` on the USB drive, or run from Terminal:

```bash
sudo python3 /Volumes/PENGUIN/install_stub.py --verbose
```

For a safe preview of what it will do:

```bash
sudo python3 /Volumes/PENGUIN/install_stub.py --dry-run --verbose
```

## What it does

1. Verifies Apple Silicon hardware (`arm64`, `hw.target`).
2. Detects the machine model and the mounted Penguin Patcher USB volume.
3. Finds the internal APFS container on the system disk.
4. Shrinks the container to free ~3 GB for the stub.
5. Creates a new APFS volume named `penguin-stub`.
6. Copies the m1n1 Stage 2 `boot.bin` from the USB to the stub.
7. Creates `SystemVersion.plist` and `.IAPhysicalMedia` on the stub.
8. Blesses the stub volume so it appears in the boot picker.

## Safety

- Your internal macOS container is left intact; only free space is reclaimed.
- The `penguin-stub` volume can be deleted from macOS Recovery or Disk Utility.
- Deleting the stub restores the stock boot configuration.

## Status

Minimal chainloader installer. It intentionally does not install a full macOS
stub OS. Derived from the Asahi Linux installer logic vendored under
`vendor/asahi-installer/`.
