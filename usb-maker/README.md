# USB Maker

Builds the Penguin Patcher USB image.

## Usage

```bash
python3 usb-maker/build_usb.py \
  --distro ubuntu \
  --device j274 \
  --kernel build/ubuntu-j274/kernel/Image \
  --initrd build/ubuntu-j274/initrd.img \
  --dtb build/ubuntu-j274/kernel/dtb \
  --uboot build/ubuntu-j274/firmware/u-boot-nodtb.bin.gz \
  --m1n1 build/ubuntu-j274/firmware/m1n1.bin \
  --grub build/ubuntu-j274/grub/BOOTAA64.EFI \
  --installer-app "installer/Penguin Patcher.app" \
  --out build/ubuntu-j274/penguin-patcher-ubuntu-j274.img
```

## Distro Profiles

Distro-specific configuration lives in `usb-maker/profiles/<distro>/profile.json`.
Add new distros by creating a new profile directory.

## Output

The final image is a raw disk image (`*.img`) with:
- APFS/HFS+ volume containing the installer app
- FAT32 ESP with m1n1, U-Boot, GRUB, and Linux

Flash with:
```bash
dd if=penguin-patcher-*.img of=/dev/rdiskN bs=1m status=progress
```
