# Build Host Setup

Penguin Patcher requires an ARM64 build host to compile the Asahi Linux
kernel, m1n1, and U-Boot. The R420 is x86_64 and cannot natively build the
ARM64 bare-metal components without a cross toolchain, so we use a
Raspberry Pi 4/5 or Apple Silicon Mac running a 64-bit ARM Linux distro.

## Quick Start

```bash
# On a Debian/Ubuntu ARM64 machine
./scripts/setup-build-host.sh
./scripts/fetch-sources.sh
./scripts/build-firmware.sh j274
```

This produces:
- `penguin-build/out/j274/m1n1.bin`
- `penguin-build/out/j274/u-boot-nodtb.bin.gz`
- `penguin-build/out/j274/t8103-j274.dtb`
- `penguin-build/out/j274/Image`
- `penguin-build/out/j274/modules/`

## Notes

- The Asahi Linux kernel uses Rust; setup installs `rustc`, `rust-src`,
  `bindgen-cli`, and LLVM/libclang.
- `m1n1` requires the `aarch64-unknown-none-softfloat` Rust target.
- The `u-boot-asahi` repo uses `apple_m1_defconfig` for the Mac mini M1
  (`j274`). Other devices may need different configs or DTB selection.

## Transferring Artifacts

After building, copy the `out/j274/` directory to the x86_64 host that runs
`usb-maker/build_usb.py`:

```bash
rsync -av penguin-build/out/j274/ jmewing@192.168.12.10:penguin-patcher/build/j274/
```
