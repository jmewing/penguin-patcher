# Kernel Builder

Builds an Apple Silicon compatible Linux kernel and modules for Penguin Patcher.

## Approach

1. Clone the Asahi Linux kernel tree.
2. Use a distro-specific config base (Fedora, Ubuntu, Debian).
3. Build:
   - `Image` (kernel binary)
   - Device Tree Blobs (DTBs) for target device
   - Kernel modules
   - Firmware files where needed
4. Package for initrd and squashfs live rootfs.

## Quick Build

```bash
./scripts/build-kernel.sh --distro ubuntu --device j274 --out ../usb-maker/build/
```

## Device Codes

| Code | Device |
|---|---|
| `j274` | Mac mini (M1, 2020) |
| `j293` | MacBook Pro 14" (M1 Pro) |
| `j294` | MacBook Pro 16" (M1 Pro/Max) |
| `j316` | MacBook Air (M1, 2020) |
| `j314` | MacBook Pro 14" (M1 Pro, late 2021) |
| `j315` | MacBook Pro 16" (M1 Max, late 2021) |
| ... | M2/M3/M4 variants |

See Asahi Linux device support matrix for the complete list.

## Dependencies

- ARM64 cross compiler (`aarch64-linux-gnu-gcc`) or native ARM64 machine
- `dtc` (device tree compiler)
- `gzip`, `cpio` for initrd
- `squashfs-tools` for live rootfs
