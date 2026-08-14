# Kernel Configs

Each distro has its own kernel configuration overlay applied on top of the
Asahi Linux defconfig.

| File | Distro |
|---|---|
| `common.config` | Shared options for all distros |
| `fedora.config` | Fedora-specific options |
| `ubuntu.config` | Ubuntu-specific options |
| `debian.config` | Debian-specific options |

The build script applies them in order: `common` → `distro` → device DTB.
