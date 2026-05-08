# Project Overview

## What This Project Is

`rdgen` is a Django web application for generating customized RustDesk clients.
The web UI collects RustDesk client customization options, then triggers GitHub Actions workflows to build platform-specific installers or packages.

## Main User Flow

1. User opens the generator page.
2. User selects a target platform: Windows 64-bit, Windows 32-bit, Linux, Android, or macOS.
3. User fills customization fields such as RustDesk version, server host, key, API server, app name, icon, logo, permissions, and advanced settings.
4. Django validates and serializes the form data into a custom RustDesk configuration.
5. Sensitive build inputs are placed into an encrypted zip.
6. Django dispatches the appropriate GitHub Actions workflow.
7. The waiting page polls GitHub run status.
8. The generated client is uploaded back to the Django service and exposed for download.

## Important Source Areas

- `rdgenerator/forms.py`: Django form fields, defaults, choices, and upload validation.
- `rdgenerator/views.py`: form handling, custom config generation, GitHub Actions dispatch, file download/upload endpoints.
- `rdgenerator/templates/generator.html`: main generator UI, inline CSS, inline JavaScript, save/load config behavior.
- `rdgenerator/templates/waiting.html`: build progress page.
- `rdgenerator/templates/generated.html`: successful build download page.
- `rdgenerator/templates/failure.html`: failed build page.
- `.github/workflows/`: platform-specific RustDesk build workflows.
- `rdgen/settings.py`: environment-driven Django/GitHub configuration.

## Live Site Observations

The author's live generator is available at:
`https://rdgen.crayoneater.org/`

Observed page headings:

- RustDesk Custom Client Builder
- Save/Load Configuration
- Select Platform
- General
- Custom Server
- Security
- Visual
- Permissions
- Code Changes
- Other

Observed platform options:

- Windows 64Bit
- Windows 32Bit
- Linux
- Android
- macOS

Observed RustDesk version options:

- nightly / `master`
- `1.4.6` through `1.3.3`

Platform switching on the live page did not visibly hide platform-specific fields. For example, the Android App ID field remains visible for Windows, Linux, and macOS.

## Current Local Artifacts

Screenshots from the live site are saved under:

- `output/playwright/rdgen-home.png`
- `output/playwright/rdgen-windows.png`
- `output/playwright/rdgen-windows-x86.png`
- `output/playwright/rdgen-linux.png`
- `output/playwright/rdgen-android.png`
- `output/playwright/rdgen-macos.png`

## Related Prior Project

The user previously deployed and modified a separate rdgen fork at:
`D:\rustdesk_web客户端\rdgen-repo`

That repository's remote is:
`https://github.com/zhenzhen122/rdgen.git`

The prior project contains useful fixes, but it also includes personal/custom behavior that should not be copied directly into this general-purpose generator.

Prior project themes that appear broadly reusable:

- UTF-8 handling in encrypted secrets extraction.
- MSI Unicode codepage fixes for Windows packaging.
- Longer upload timeouts for large generated artifacts.
- Splitting Windows EXE upload from optional MSI upload.
- Showing only Windows download links for files that actually exist.
- Resolving callback URLs through reusable environment variables.
- Better progress/failure status updates from workflows.
- For hide connection window, forcing password approval mode when `hidecm` is enabled.

Prior project themes that are personal/specific and should be isolated or avoided for a generic generator:

- Checkout and overlay from `zhenzhen122/rustdesk`.
- Custom module copying from that overlay.
- Account/auth gate/client module changes tied to the user's RustDesk fork.
- Chinese-only end-user status strings unless the new project explicitly chooses Chinese localization.
