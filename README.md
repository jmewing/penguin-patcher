# Penguin Patcher

Boot Linux on Apple Silicon Macs from a single USB drive.

Penguin Patcher is an all-in-one tool that creates a bootable USB with a macOS
installer partition and a Linux live/boot partition. Run the installer from
macOS, reboot, and boot Linux from USB without erasing your internal drive.

## Why?

Apple Silicon Macs cannot boot arbitrary operating systems from USB. The firmware
only recognizes signed Apple OS images. Penguin Patcher works around this by
installing a tiny, reversible `m1n1` Stage 1 stub to the internal SSD. That
stub then chainloads Linux from the USB drive.

## How It Works

```
┌─────────────────────┐     ┌──────────────────────┐
│   macOS (internal)  │     │   Penguin Patcher    │
│                     │     │   USB Drive          │
│  ─ unchanged ─      │     │                      │
│                     │     │  ┌───────────────┐   │
│  ┌───────────────┐  │     │  │ macOS volume  │   │
│  │ m1n1 Stage 1  │  │     │  │ (installer)   │   │
│  │ stub (~2.5GB) │  │◄────┼──│ penguin-patch │   │
│  └───────┬───────┘  │     │  │   .app        │   │
│          │          │     │  └───────────────┘   │
│          │ chainload│     │  ┌───────────────┐   │
│          ▼          │     │  │ ESP (FAT32)   │   │
│  boot picker entry  │     │  │ /m1n1/         │   │
│                     │     │  │ /EFI/BOOT/    │   │
└─────────────────────┘     │  │ kernel+initrd │   │
                            │  └───────────────┘   │
                            └──────────────────────┘
```

1. **Create USB image** on another Mac or Linux machine.
2. **Flash USB** and insert it into the target Apple Silicon Mac.
3. **Run `Penguin Patcher.app`** from the macOS-readable partition.
4. The app installs the `m1n1` Stage 1 stub on the internal SSD (reversible).
5. **Reboot**, hold the power button, choose the Penguin Patcher entry.
6. Linux boots from the USB ESP.

## Features

- All-in-one USB: installer app + bootable Linux partition
- Internal macOS stays untouched except for a removable stub
- Try Linux live before installing to internal disk
- Supports multiple distributions:
  - Asahi Fedora Remix
  - Ubuntu ARM64 (with Asahi kernel)
  - Debian ARM64 (with Asahi kernel)
- Device profiles for M1 / M1 Pro / M1 Max / M1 Ultra / M2 / M3 / M4 families

## Project Structure

| Directory | Purpose |
|---|---|
| `installer/` | macOS app/CLI that installs the m1n1 stub |
| `usb-maker/` | Tool that builds the dual-partition USB image |
| `kernel-builder/` | Scripts to build/patch Asahi Linux kernel and modules |
| `docs/` | Research, architecture, and build instructions |
| `resources/` | Icons, plists, templates |
| `scripts/` | Helper scripts for CI/CD and release packaging |

## Status

Working prototype for Mac mini M1 (`j274`).

- ✅ ARM64 build host setup (Raspberry Pi)
- ✅ Asahi kernel, m1n1 Stage 2, U-Boot built for `j274`
- ✅ GRUB ARM64 EFI binary built
- ✅ SSH-first Debian rootfs with kernel modules
- ✅ Real initrd with squashfs/overlay root switch
- ✅ USB image builder creates bootable GPT image (raw file or direct `--device-node`)
- ✅ 32 GB Penguin Patcher USB built with ESP + `PENGUIN` installer partition
- ✅ Minimal macOS m1n1 Stage 1 installer (`installer/install_stub.py`) implemented
- ✅ macOS app bundle `Penguin Patcher.app` with Terminal launcher
- ✅ Verified `install_stub.py --dry-run` on a real Mac mini M1
- ✅ IPSW cache helper script (`~/cache-apple-ipsws.sh`) downloads all signed Mac IPSWs and hard-links duplicates
- ❌ Installer not yet tested with a real install + reboot on the Mac mini M1
- ❌ Apple proprietary firmware (WiFi/BT/GPU) not yet bundled

The USB boots Linux **after** the m1n1 Stage 1 stub is installed on the Mac.
The next milestone is a real install + reboot test on the Mac mini M1.

## Quick Build (ARM64 host)

```bash
# 1. Prepare an ARM64 Debian/Ubuntu build host
./scripts/setup-build-host.sh

# 2. Fetch sources
./scripts/fetch-sources.sh

# 3. Build firmware + kernel for Mac mini M1
./scripts/build-firmware.sh j274

# 4. Build live rootfs + initrd
./scripts/distro/make-initrd.sh debian ../penguin-build/out/j274/initrd.img
./scripts/distro/make-rootfs.sh debian ../penguin-build/out/j274/rootfs.squashfs \
  ../penguin-build/out/j274/modules/lib/modules

# 5. Build USB image
python3 usb-maker/build_usb.py \
  --distro debian --device j274 \
  --kernel ../penguin-build/out/j274/Image \
  --initrd ../penguin-build/out/j274/initrd.img \
  --dtb ../penguin-build/out/j274/t8103-j274.dtb \
  --uboot ../penguin-build/out/j274/u-boot-nodtb.bin.gz \
  --m1n1 ../penguin-build/out/j274/m1n1.bin \
  --grub ../penguin-build/out/j274/BOOTAA64.EFI \
  --out ../penguin-build/out/j274/penguin-patcher-debian-j274-ssh.img \
  --size 4096

# 6. Flash to USB
sudo dd if=../penguin-build/out/j274/penguin-patcher-debian-j274-ssh.img of=/dev/sdX bs=4M status=progress conv=fsync
```

## License

MIT — see `LICENSE`.
