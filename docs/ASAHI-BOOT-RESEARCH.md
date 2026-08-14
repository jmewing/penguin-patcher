# Asahi Linux Bootloader Research

## 1. Bootloader Installation & Placement
The Asahi Linux boot process uses a multi-stage approach to bridge the gap between Apple's proprietary boot ecosystem and the Linux/UEFI ecosystem.

### Boot Chain
`Apple iBoot2` $\to$ `m1n1 Stage 1` $\to$ `m1n1 Stage 2` $\to$ `U-Boot` $\to$ `GRUB/UEFI Loader` $\to$ `Linux Kernel`

### File Locations
- **m1n1 Stage 1:** Installed as a "fuOS" (custom kernel) within a small "stub macOS" APFS container. It is signed by a machine-specific key and is largely immutable once installed.
- **m1n1 Stage 2:** Located on the **EFI System Partition (ESP)** at `/m1n1/boot.bin`.
  - This file is a concatenation of: `m1n1.bin` + `Device Trees (.dtb)` + `compressed U-Boot (u-boot-nodtb.bin.gz)`.
- **U-Boot:** Embedded within the m1n1 Stage 2 binary.
- **UEFI Loader (e.g., GRUB):** Located on the ESP at `/EFI/BOOT/BOOTAA64.EFI`.

## 2. Disk Space Requirements
- **Stub macOS Container:** Approximately **2.5 GB**. This contains the minimal Apple-required components (iBoot2, firmware, XNU kernel, RecoveryOS) to make the platform recognize the installation as a valid OS.
- **EFI System Partition (ESP):** Approximately **512 MB** (FAT32).

## 3. macOS Coexistence
The internal macOS installation **remains intact**. Asahi Linux is installed into its own separate APFS container and ESP. This allows the native Apple boot picker to see both macOS and Asahi Linux as independent operating systems.

## 4. Reversibility
The installation is **highly reversible**.
- **Removal:** Since Asahi resides in its own container and ESP, these partitions can be deleted from macOS Disk Utility.
- **Restoring Stock Boot:** Removing the Asahi container removes the entry from the boot picker. Because the original macOS installation was not modified (it lives in its own container), the system returns to a stock state.

## 5. USB Boot Capabilities
**Partial/Conditional.**
- **Native Apple Boot:** The native Apple Silicon boot tooling does **not** support external boot of arbitrary kernels.
- **m1n1 Stage 1 Requirement:** To boot from USB, the machine must already have `m1n1 Stage 1` installed on the internal NVMe.
- **USB Chainloading:** Once `m1n1 Stage 1` is present, it can chainload `m1n1 Stage 2` from internal storage, which then launches `U-Boot`. `U-Boot` then provides the ability to boot from external USB storage using the `bootcmd_usb0` command.
- **USB-Only (No Internal Install):** The "UEFI-only setup mode" of the installer installs a minimal m1n1 Stage 1 and Stage 2/U-Boot to allow booting any OS from USB via standard UEFI protocol, provided the USB has a FAT32 ESP with `/EFI/BOOT/BOOTAA64.EFI`.

## 6. USB Live Boot Requirements
For a USB drive to be bootable via the Asahi bootloader:
- **Partitioning:** Must have a FAT32 EFI System Partition (ESP).
- **Files:**
  - `/EFI/BOOT/BOOTAA64.EFI`: A UEFI-compliant bootloader (like GRUB or the Linux EFI stub).
  - **Kernel & Initramfs:** Located on the USB (either in the ESP or a separate partition).
  - **Device Tree:** Required for the kernel to boot.

## 7. Installer Structure & Key Scripts
- **Repository:** `AsahiLinux/asahi-installer`
- **Key Components:**
  - `build.sh`: Produces the installer tree.
  - `bootstrap.sh` (and variants): Launch scripts used to execute the installer from macOS or Recovery mode.
  - `asahi_firmware`: Python module for handling Apple firmware blobs.
- **Process:** The installer streams required components from Apple's IPSW files to create the "stub macOS" container and ESP without requiring a full IPSW download.

---

## Verdict: Reversible "Boot from USB" Feasibility

**Is it feasible?** Yes, but with a major caveat: **It is not "plug-and-play" from a factory-stock Mac.**

**The "Stub" Requirement:**
Because the Apple Silicon SoC does not natively boot external EFI/Linux kernels, **some modification to the internal NVMe is always required**. You cannot simply plug in a USB and boot Linux on a stock Mac. You must first install the `m1n1 Stage 1` stub on the internal drive to act as the bridge.

**The Reversibility Verdict:**
Since the "stub" is installed into a dedicated, small APFS container (the "stub macOS"), the process is **effectively reversible**. The only "permanent" change is the creation of this small container and the registration of a new boot entry. Both are easily removable via macOS Disk Utility without affecting the primary macOS installation.

**Recommended Strategy for "USB-First" approach:**
1. Install the minimal Asahi "UEFI environment" (m1n1 Stage 1 + minimal Stage 2/U-Boot) to the internal drive.
2. Use this environment to boot full OS installers or live images from USB.
3. To revert, simply delete the Asahi container.
