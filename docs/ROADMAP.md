# Penguin Patcher Roadmap

## Phase 0: Validation (current)
- [x] Scaffold project
- [x] Define architecture and boot flow
- [x] Research Asahi Linux bootloader install process
- [x] Create distro profiles (Fedora, Ubuntu, Debian)
- [ ] Verify m1n1 Stage 1 can chainload Stage 2 from USB
- [ ] Confirm reversibility on a test Mac

## Phase 1: USB Image
- [ ] Build real raw disk image with APFS + ESP partitions
- [ ] Integrate Asahi kernel, modules, DTBs
- [ ] Build initrd and squashfs live rootfs
- [ ] Add GRUB bootloader and config
- [ ] Embed macOS installer app in the APFS partition

## Phase 2: macOS Installer
- [ ] Port/adapt Asahi installer's machine-specific boot logic
- [ ] Implement APFS resize and stub container creation
- [ ] Implement m1n1 Stage 1 installation and blessing
- [ ] Add GUI wrapper (SwiftUI)
- [ ] Handle Gatekeeper / notarization

## Phase 3: Distros
- [ ] Fedora Asahi Remix profile
- [ ] Ubuntu ARM64 profile
- [ ] Debian ARM64 profile
- [ ] Per-device firmware and DTB selection

## Phase 4: Polish
- [ ] Live desktop with hardware support (GPU, WiFi, Bluetooth)
- [ ] Optional install-to-internal
- [ ] Recovery / remove stub tool
- [ ] CI/CD for image builds
- [ ] Documentation and release packaging
