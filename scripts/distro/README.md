# Distro Build Scripts

These scripts create the initramfs and live rootfs for Penguin Patcher.

## Files

- `make-initrd.sh` — minimal initramfs
- `make-rootfs.sh` — distro-specific squashfs rootfs

## Status

Both are placeholders. The initrd needs real init logic to:
1. Detect the USB device.
2. Mount the squashfs rootfs.
3. Set up overlay persistence in RAM.
4. Switch to the real init.

The rootfs needs real distro bootstrapping using the profile configs in
`usb-maker/profiles/`.
