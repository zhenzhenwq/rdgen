# New Window Handoff

This is the current durable handoff for the RustDesk generator work.

## Workspace And Safety

- Main repository: `D:\rustdesk-生成器\rdgen`
- Branch: `master`
- User fork/build repository: `https://github.com/zhenzhenwq/rdgen.git`
- Upstream: `https://github.com/bryangerlach/rdgen.git`
- Deployed generator: `https://120.55.0.199/`
- Old reference project: `D:\rustdesk_web客户端\rdgen-repo`

The old reference project is strictly read-only. Do not edit, format, move, delete, clean, or generate files inside it.

Do not write server passwords, GitHub tokens, signing passwords, private certificate material, Django secrets, or API bearer tokens into repository files or answers. Code-signing material under `D:\rustdesk-生成器\codesign\` is sensitive and outside this repository.

Do not submit the live generator form unless the user explicitly asks. A push to `master` automatically starts the repository's Docker image workflow, but it does not dispatch a RustDesk client generation workflow.

The full generator path requires public GitHub Actions callbacks. Local Docker cannot provide meaningful end-to-end generation coverage and is not a release prerequisite; use local services only for UI/form inspection unless the user explicitly requests local container work.

## Current Release Batch

The active batch adapts the generator to RustDesk `1.4.9` while retaining `1.4.7` and `1.4.8` compatibility for strict optional patches.

The batch includes:

- RustDesk `1.4.9` as the form and workflow default.
- Windows x64, Windows x86, Linux, macOS, and Android patch-chain compatibility.
- Strict patch failures instead of `continue-on-error` for selected customizations.
- Version/platform capability checks in Django and matching dynamic UI visibility.
- Hidden-connection-window capability is separate from its default state. New forms keep the settings entry available, legacy POSTs retain their old default-on meaning, and Windows x86 exposes the same user toggle through Sciter. Flutter and Sciter write explicit `Y`/`N` overrides so users can disable a build default even when the app name remains `RustDesk`.
- Safer build inputs, manual settings, portable artifact names, Windows reserved-name checks, and bounded name lengths.
- Linux native packages, AppImage, and Flatpak customization and upload reliability fixes.
- Beijing Linux customization is accepted only for the verified `1.4.7`, `1.4.8`, and `1.4.9` tags; the UI and Django validation both enforce this boundary.
- macOS NASM `2.16.03`, packaged custom config, whole-bundle P12 signing, verification, and ad-hoc fallback signing.
- Android universal plus split APK output retained and hardened.
- Strict HTTP failure handling for generator/API uploads and external Windows signing requests.
- Shared Actions/cache/reusable-workflow cleanup.

Eleven new patch and test files belong to the batch and must never be omitted from its commit:

- `.github/patches/android_custom_config.py`
- `.github/patches/apply_linux_base_fixes.py`
- `.github/patches/customize_appimage_recipe.py`
- `.github/patches/customize_flatpak_manifest.py`
- `.github/patches/customize_linux_native_packages.py`
- `.github/patches/delay_fix.py`
- `.github/patches/hide_settings_menu.py`
- `.github/patches/rustdesk_default_linux_149.diff`
- `.github/patches/smoke_149_patch_chain.py`
- `.github/patches/test_linux_packaging_customization.py`
- `.github/patches/validate_customization.py`

Runtime patch helpers are downloaded from the current `${{ github.sha }}`; the smoke and packaging test scripts are local verification tools. Keep all eleven files in the same release commit so the implementation and its repeatable checks remain complete.

## Repository State

- Development baseline: `8ff0593`, which matched `origin/master` when this batch resumed.
- Core release commit: `8e33770` (`Adapt generator for RustDesk 1.4.9`).
- First capability-state follow-up: `cd2c358` (`Decouple hide window capability from default state`).
- Compatibility follow-up: `23d1cf3` (`Fix hide window capability compatibility`).
- Auth and task-security release: `13408fb` (`Add authenticated user management`, tree `c1b8bd7ed1dd30209a13f6e59fbf42297aaf3056`).
- Current deployed application release: `fe7ee968c91a0eead6e5d31267e41cc013522eb9` (`Show generation entitlements on workspace`, tree `057845f4718b4987e01eb634cad3a58dbe9127de`). It includes the prior account/download/artifact hardening plus visible ordinary-user entitlement summaries and exhausted/expired generation controls.
- Application commit `c92c48c` was independently verified after a non-force fast-forward to `origin/master`; later documentation-only commits may follow. Push-triggered Docker run `29907047085` failed at the known Docker Hub login step; no RustDesk client workflow was dispatched.
- Treat the latest `master` commit containing this handoff as the authoritative batch state.

## Verified State

- The optional patch chains for Windows, Windows x86, Linux, macOS, and Android were each run twice against RustDesk `1.4.7`, `1.4.8`, and `1.4.9` sources.
- Linux AppImage, Flatpak, RPM, SUSE, Arch, URI-scheme, service-config, and DEB purge customizations passed repeatability checks against real RustDesk `1.4.7`, `1.4.8`, and `1.4.9` file layouts.
- Django: 38 tests pass; system checks report no issues. Coverage includes new-form unchecked semantics, legacy POST migration, unknown schema handling, and settings-entry requirements for both hidden-window default states.
- Windows x86 patch chains ran twice on real RustDesk `1.4.7`, `1.4.8`, and `1.4.9` sources after adding the Sciter `allow-hide-cm` control.
- Linux packaging customization: 20 focused regression tests pass. They cover Python 3.6 compatibility in the Ubuntu 18.04 native container, exact `rustdesk` name handling, RPM metadata rejection, AppImage YAML quoting, Flatpak identity/metainfo/device permissions, URI protocol consistency, runtime configuration paths, udev migration, and repeatability.
- `actionlint`: no findings.
- Python AST and workflow YAML parsing: pass.
- Workflow patch references: no missing concrete files.
- Every workflow curl POST now uses HTTP failure detection.
- `git diff --check`: no whitespace errors; Git only reports the repository's existing LF-to-CRLF checkout warnings.
- Playwright desktop/mobile and platform switching checks passed. A focused follow-up also verified capability-only/default-on transitions, forced password submission, and old/current JSON import behavior with no page errors.
- Screenshots: `output/playwright/resume-149-desktop.png` and `output/playwright/resume-149-mobile.png`.
- `data/` and `output/` are ignored runtime directories and must not be committed.
- Authentication and task security add Django sessions/CSRF, administrator-created accounts, strict per-user task ownership, callback bearer tokens, signed expiring downloads, and POST-only logout. Public registration is intentionally absent.
- Django `5.2.16`: 134 tests pass locally and in the candidate release path. The entitlement matrix covers count availability/reservations/exhaustion/missing limits, permanent/time/under-24-hour/expired memberships, administrators, invalid forms, and forged POST rejection. System checks, migration-drift checks, and `git diff --check` pass.
- Entitlement UI screenshots passed at 1440px desktop, 900px tablet, and 390px mobile with no page-level horizontal overflow or overlap. Desktop uses the sidebar account area; narrower layouts use a navigation-under status strip with two-column mobile metrics.
- Desktop, 768px tablet, and 390px mobile layouts passed Playwright checks across Windows, Windows x86, Android, standard/custom Linux, and macOS visibility states. Imported PNG previews now use strict base64 validation plus DOM node creation; a malicious JSON import was verified not to execute while valid PNG previews still render.
- The live generator was deployed from tree `057845f4718b4987e01eb634cad3a58dbe9127de`. Windows x64 task success still requires exact persisted `.exe` and `.msi` receipts whose size and SHA-256 match the final files; uploads are staged and atomically committed, retries cannot replace immutable content, and terminal status callbacks cannot revive or bypass finalization.

Important Linux/Flatpak boundaries:

- The native package helper rejects RPM macro characters and whitespace-invalid RPM URLs, avoids same-file `mv` failures for the exact `rustdesk` name, and keeps binary/service names separate from visible app/company metadata.
- Linux deep links use a stable `rdgen-<filename hex>` URI scheme in both Rust runtime code and the desktop handler. Service config copying and DEB purge cleanup follow `directories-next` whitespace/lowercase behavior and shell-quote cleanup paths.
- Uinput rules use `0660` plus `uaccess`; install/upgrade hooks reload and trigger udev, and legacy `chmod 0666 /dev/uinput` blocks are removed.
- Flatpak uses a case-preserving hex-derived `com.rdgen.app_<hex>` ID and keeps manifest ID, desktop rename, metainfo component/launchable, and `build-bundle` ref synchronized. `--device=dri` remains and `--device=all` is removed.
- Consequently, Flatpak must not be advertised as supporting `/dev/uinput`-based unattended Wayland input. X11 remains the expected path; a real X11/Wayland portal smoke test is still required before making a stronger runtime claim.

## Live Deployment

- URL: `https://120.55.0.199/` (`http://120.55.0.199/` redirects to HTTPS; public port 8000 is closed).
- Application source commit: `fe7ee968c91a0eead6e5d31267e41cc013522eb9`; application tree: `057845f4718b4987e01eb634cad3a58dbe9127de`.
- Deployment ID: `20260722-180717-fe7ee968c91a`.
- Source archive SHA-256: `cb7133b2f8c48fb1f3566317a7987dbefec2ee11dae5cd5c7cc4ae627abd9b5e`.
- Live image: `sha256:2d89717ea403ccc92c639254b28695c489ebf5bc72586844269130395bb64c50`.
- Live container is `rdgen-rdgen-1`, verified `running`, `healthy`, restart count `0`, with zero traceback/critical/worker-timeout log fingerprints. Ordinary users now see their actual entitlement on the generator workspace; unavailable entitlements disable submission, while administrators remain unlimited and have no entitlement panel. Windows x64 tasks stay pending until exact EXE/MSI receipts and final disk hashes pass explicit finalization. Passwords require only 6 characters; numeric/common/username-matching values are allowed, and all password guidance/errors are Chinese.
- Nginx terminates TLS and rate-limits `/login/`; the container binds only `127.0.0.1:8000`. The trusted Let's Encrypt IP certificate is renewed by the enabled `rdgen-certbot-renew.timer`; staging renewal passed.
- The production `admin` superuser exists. Never add its password to Git, memory files, shell history, or chat summaries.
- Persistent `.env`, `data`, `exe`, `png`, `temp_zips`, and SQLite data were preserved. `.env` remains mode `600`; migration `0007_githubrun_artifact_contract_generatedartifact` is applied, and SQLite `quick_check` passed with 3 users and all 27 task rows retained. The receipt table began empty so historical tasks continue through the legacy file fallback.
- Account expiry now supports permanent/time-based and successful-package-count policies. Download delivery supports creator/admin login or public token access with 1-hour, 1-day, 3-day, or 7-day expiry beginning at the first valid installer upload. Quota reservation creation and artifact settlement are atomic and guard administrative mode changes.
- `/etc/cron.d/rdgen-cleanup` runs hourly with `flock`. Initial enforcement removed 13 expired secret ZIPs and one empty directory, no installer and no reservation; the immediate post-run dry-run reported zero pending removals.
- Root-only rollback material is under `/opt/rdgen-backups/20260722-180717-fe7ee968c91a`, `/opt/rdgen-previous-20260722-180717-fe7ee968c91a`, and `rdgen-rollback:20260722-180717-fe7ee968c91a`. The preceding `20260722-163349-c92c48cc71d6` and earlier rollback sets remain present.
- The hourly cleanup converted the former cancelled legacy `in_progress` row to `timed_out`. Current database and GitHub gates report zero active client workflows.
- Existing task 27 was verified to render both `21313.exe` and `21313.msi`; SQLite retained 3 users and all 27 tasks. No live generator form was submitted and no client workflow was dispatched during deployment.

## Not Yet Verified

- Public Actions history contains successful manually dispatched Windows generator runs `29318081070` at `8e33770` and `29326063260` at `cd2c358`. They were not push-triggered; their artifacts and runtime behavior have not been audited here, and the public API cannot distinguish a GitHub UI dispatch from a generator/API dispatch.
- No fresh public Windows generation has been intentionally submitted against `fe7ee96`; task 27 verifies legacy EXE/MSI rendering, while artifact and entitlement enforcement are covered by backend/workflow tests. A real generation remains an explicit user-approved follow-up.
- No real Linux, macOS, or Android client compilation has been verified for this batch.
- Docker image runs, including `29406597406` and the latest application push run `29907047085`, fail at `Login to Docker Hub` because repository Docker Hub credentials are unavailable. The production image was built and tested directly on the server; repair `vars.DOCKERHUB_USERNAME` and `secrets.DOCKERHUB_TOKEN` separately.
- macOS P12 signing is structurally validated but still needs a real macOS runner with configured signing secrets.
- No real Flatpak bundle installation/runtime smoke test has been run for this batch.

## Resume Checklist

1. Run `git status --short --branch` and `git log --oneline -n 8 --decorate`.
2. Confirm the eleven new patch and test files are tracked in the release commit.
3. Re-run Django tests, `actionlint`, patch-reference checks, YAML/Python parsing, and `git diff --check` after any edit.
4. Verify remote state before pushing; the machine's global Git proxy may point at unavailable `127.0.0.1:7892`.
5. Treat additional client builds, local Docker setup, and Docker credential repair as separate, explicit follow-up work. The live generator deployment is complete.

## Deployment Notes

The deployed host directory is `/opt/rdgen`; the Docker service is `rdgen-rdgen-1` on loopback port `8000`, behind Nginx on public ports 80/443. The host is CentOS 9 with Docker `29.6.1` and Compose `v5.2.0`; `/opt/rdgen` is a controlled source snapshot rather than a Git checkout.

For a future deployment, preserve `.env`, `exe`, `png`, `temp_zips`, and `data`. On Windows, use `git -c core.autocrlf=false archive` when byte-for-byte Git blob fidelity matters. Build and test the candidate while the old container remains live; before a schema-changing cutover, stop or block public writes, take and verify a final SQLite snapshot, recheck GitHub activity from the isolated snapshot, then switch and keep signal-aware rollback responsibility until health checks pass. Do not perform a blind destructive sync or remove current rollback material before the next deployment is verified.

Historical work, previous real Windows signing and Android universal APK verification, and RustDesk server network investigation remain documented in `WORKLOG.md`.
