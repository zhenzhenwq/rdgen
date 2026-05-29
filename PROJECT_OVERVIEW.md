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

## Current Customized Direction

The current project has moved away from the author's public English UI and toward the user's deployed generator:

- Visible generator UI is Chinese.
- Main visual theme is blue and white.
- Sponsor/source-code footer links were removed from the generator page.
- The generated/download/failure/waiting pages have been localized and styled consistently enough for current deployment.
- The generator is intended to remain generally usable, not locked to the user's older personal fork.

## Current Implemented Feature Set

Important implemented changes compared with the upstream author's baseline:

- Hide connection window support:
  - `hidecm` now forces `approve-mode = password` in generated settings.
  - `verification-method` is set to permanent-password behavior when hiding the connection window.
  - Windows workflows apply `hidecm.diff` before build.
- Hide RustDesk settings entry:
  - Form field `settings` controls whether client settings are allowed or disabled.
  - `settingsN` writes `disable-settings = Y`.
  - Windows workflows can apply `hide_settings_menu.diff`.
- Built-in server settings:
  - `rdgenerator/views.py` writes `custom-rendezvous-server` and `relay-server` into the generated config.
  - This fixed earlier cases where generated clients did not actually embed the desired server.
- Windows self-signed code signing:
  - GitHub Actions can sign generated Windows EXE, DLL, and MSI outputs using `CODE_SIGN_PFX_BASE64` and `CODE_SIGN_PFX_PASSWORD`.
  - External signing service behavior remains available if configured.
  - If no signing secrets are configured, workflows skip signing rather than fail.
- Android universal APK output:
  - Android matrix still builds three ABI split APKs.
  - The deploy job now creates and uploads a fourth `-universal.apk`.
  - The intended Android download set is:
    - `${filename}-universal.apk`
    - `${filename}-aarch64.apk`
    - `${filename}-armv7.apk`
    - `${filename}-x86_64.apk`

## External Systems

- Live generator URL: `http://120.55.0.199:8000/`
- Live generator host directory: `/opt/rdgen`
- Live generator Docker service: `rdgen-rdgen-1`
- Current project repo/fork: `https://github.com/zhenzhenwq/rdgen.git`
- Upstream author's repo: `https://github.com/bryangerlach/rdgen`
- Author's public generator: `https://rdgen.crayoneater.org/`
- Old user project, read-only only: `D:\rustdesk_web客户端\rdgen-repo`

Secrets are intentionally not stored here. Ask the user or use already configured secure stores when a task requires SSH, GitHub, or signing credentials.

## Current Test Links

- Android universal verification:
  `http://120.55.0.199:8000/check_for_file?filename=WuYouDesk&uuid=9de4743a-ec38-4266-b155-cd383ae64685&platform=android`
- Old Android report that only has pre-fix split APKs:
  `http://120.55.0.199:8000/check_for_file?filename=WuYouDesk&uuid=dcaa5218-3b21-4883-a4e9-d28a96c467eb&platform=android`
