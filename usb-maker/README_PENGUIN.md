# Welcome to Penguin Patcher!

Before you start
----------------

1. Disable Find My Mac. Activation Lock can block Recovery mode boot and disk
   changes. System Settings → Apple ID → iCloud → Find My Mac → Off.
2. Turn off FileVault if it is enabled. Encrypted disks may prevent live APFS
   resizing. System Settings → Privacy & Security → FileVault → Turn Off.
3. If a firmware password or MDM profile is set, remove it. These block the
   boot picker and external boot.
4. Back up your data. The installer preserves your macOS container, but any
   disk modification carries risk.

Install the stub
----------------

1. Plug this USB into your Apple Silicon Mac running macOS 12.1 or later.
2. Open this volume in Finder and double-click **Penguin Patcher.app**.
3. A Terminal window opens. Enter your password when prompted for sudo.
4. The installer resizes your internal APFS container and installs a small
   reversible boot stub named **penguin-stub**.
5. Shut down, then hold the Power button until "Loading startup options" appears.
6. Choose **Penguin** from the boot picker to chainload Linux from this USB.

To remove the stub, boot to macOS Recovery, open Disk Utility, and delete
**penguin-stub** from the internal SSD.
