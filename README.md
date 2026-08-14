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

Early scaffolding. Not yet functional. See `docs/` for research and roadmap.

## License

MIT — see `LICENSE`.
