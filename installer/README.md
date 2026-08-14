# macOS Installer

Installs the `m1n1` Stage 1 stub on an Apple Silicon Mac so it can boot Linux
from a Penguin Patcher USB drive.

## Usage

```bash
python3 installer/install_stub.py --usb /Volumes/PENGUIN --size 3
```

## What It Does

1. Verifies Apple Silicon hardware.
2. Detects machine model.
3. Shrinks the internal APFS container by ~3GB.
4. Creates a new `penguin-stub` APFS container.
5. Installs the machine-specific `m1n1` Stage 1 into the stub.
6. Blesses the stub so it appears in the boot picker.

## Safety

- Internal macOS stays in its own container.
- The stub container can be deleted from macOS Recovery or Disk Utility.
- Deleting the stub restores the stock boot configuration.

## Status

Placeholder. Real implementation must reuse Asahi Linux installer's
machine-specific boot firmware handling.
