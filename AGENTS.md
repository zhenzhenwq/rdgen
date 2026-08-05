# Agent Notes

## Project Context

This repository is a local clone of `https://github.com/bryangerlach/rdgen`.
The working directory is `D:\rustdesk-生成器\rdgen`.

The user wants to optimize this RustDesk custom client generator. Keep changes scoped and preserve upstream behavior unless the requested optimization requires a behavior change.

## Operating Rules

- Use PowerShell commands from the repository root unless a task requires another shell.
- Prefer `rg` / `rg --files` for source discovery.
- Use `apply_patch` for manual edits.
- Do not overwrite user changes. Check `git status --short` before edits.
- Avoid submitting the live generator form unless the user explicitly asks.
- Full generation depends on public GitHub Actions callbacks and cannot be proven with a local-only Docker stack. Do not treat local Docker parity as a release requirement; local services are useful only for UI/form inspection unless the user explicitly asks for local container work.
- Browser inspection artifacts should go under `output/playwright/`.

## Git / Network Notes

- The machine has global Git proxy configured as `http://127.0.0.1:7892` for both HTTP and HTTPS.
- That proxy was unavailable during the initial clone attempt.
- The repo was cloned successfully with temporary proxy overrides:
  `git -c http.proxy= -c https.proxy= clone --depth 1 https://github.com/bryangerlach/rdgen.git rdgen`

## Browser Notes

- The Chrome DevTools MCP connection did not work in this session even after launching Chrome with `--remote-debugging-port=9222`.
- Playwright was used as fallback through a temporary install in `%TEMP%\rdgen-pw-inspect`, using system Chrome as the executable.
- Saved screenshots currently exist in `output/playwright/`.

## Prior Project Reference

- Previous user-customized fork: `D:\rustdesk_web客户端\rdgen-repo`.
- Treat it as strictly read-only. Do not write, edit, format, move, delete, clean, or generate files inside this old project.
- Useful generic fixes may be ported, but avoid copying personal overlay behavior tied to `zhenzhen122/rustdesk`.

## Current Session Handoff Rules

- Primary working repo remains `D:\rustdesk-生成器\rdgen`.
- The current GitHub repo/fork used for builds is `https://github.com/zhenzhenwq/rdgen.git`.
- `upstream` remains `https://github.com/bryangerlach/rdgen.git`.
- Do not store plaintext server passwords, GitHub tokens, PFX passwords, or API bearer tokens in repository files.
- Credentials were provided in chat during previous work, but repository memory files intentionally omit the secret values.
- Code signing certificate material is outside the repo at `D:\rustdesk-生成器\codesign\`; treat the PFX and password file as sensitive.
- Generator server is reachable at `https://120.55.0.199/`; HTTP port 80 redirects to HTTPS.
- The deployed generator directory on `120.55.0.199` is `/opt/rdgen`, but that server currently does not have `git` installed.
- The live Docker service is `rdgen-rdgen-1`. Container port `8000` is bound only to `127.0.0.1`; Nginx owns public ports 80/443 and applies login rate limiting.
- Let's Encrypt issues the trusted IP certificate. `rdgen-certbot-renew.timer` checks renewal twice daily and reloads Nginx after successful renewal.
- If deploying source changes to `120.55.0.199`, do not assume `git pull` works there. Either install git deliberately, upload a controlled source snapshot, or rebuild/recreate the Docker service from a known copied tree.
- The old project `D:\rustdesk_web客户端\rdgen-repo` remains read-only even if it contains useful reference fixes.

## Current Release State

- The development baseline for the RustDesk `1.4.9` batch was `8ff0593`, matching `origin/master` when work resumed on 2026-07-13.
- The core batch was committed as `8e33770`; `cd2c358` separated hidden-window capability from its default state, and `23d1cf3` completed the compatibility follow-up. Use the latest `master` commit for subsequent fixes.
- The batch changes the form and platform workflows, ports strict optional patch chains, and hardens Linux packaging, macOS signing, uploads, and build inputs.
- Eleven new patch/test files under `.github/patches/` were tracked by the release commit; runtime workflows download patch helpers from the exact `${{ github.sha }}`.
- Public Actions history contains successful manual Windows generator runs for `8e33770` and `cd2c358`, but their artifacts were not audited here. No Linux or Android build has been verified for this batch. macOS was compiled on real GitHub-hosted macOS runners for both Intel and Apple Silicon in validation run `29975374837`.
- The automatic Docker runs for `8e33770` and `cd2c358` failed before image build because Docker Hub login inputs were unavailable.
- The current deployed application release is `16389d36cd355089ff72d7030648567644a7fca0` (tree `7b1d52640717ff2ad9a8ed7bda89d45d3157e1dc`). It adds public email-verified registration, membership activation, and staff activation-code management while retaining the hide-tray, artifact, entitlement, icon, and platform-workflow behavior from the previous release.
- New registrations require a short-lived email code and start without membership. Staff can create, list, filter, and revoke unused codes for one generation, 3 days, 7 days, 30 days, or lifetime; plaintext activation codes are shown only at creation and stored as hashes. The production SMTP account and authorization value are intentionally absent from repository memory.
- The server application is built from `16389d36`; later documentation-only commits do not change the live image. Push-triggered Docker failures remain limited to the repository's existing Docker Hub login step and do not dispatch client builds or affect the directly deployed server image.
- GitHub Actions run `29975374837` passed the complete validation matrix for `x86_64` and `aarch64`: customization validation, compilation, embedded configuration packaging, ad-hoc code signing, bundle metadata and architecture checks, DMG creation, `hdiutil verify`, and artifact upload. Validation mode skipped production upload and cleanup callbacks by design.
- A push to `master` starts `docker-build.yml`; it does not dispatch a RustDesk client generator workflow.
- Confirm the current local and remote state with `git status --short --branch`, `git log --oneline -n 8 --decorate`, and a fresh remote query before follow-up release work.

## Current Deployment State

- Deployment ID: `20260805-171543-16389d36cd35`.
- Source archive SHA-256: `bc131b2efd9bcbc86137beb78a1a48bc6a9c6a9c65b873d2158098ceb653d907`. Verified live image: `sha256:bbae70fc379f02227cba3c6cfab37e781e2cf30b325d4fd3ead3eda2c5078fd0`.
- The service is `running`, `healthy`, restart count `0`, and has no post-deploy error fingerprints. Django `5.2.16` passed all 169 tests locally and in the candidate image; the isolated candidate also passed migrations, copied-production data checks, login/registration rendering, and a real QQ SMTP authentication check without sending a post-deploy message.
- Public `/login/` and `/register/` return 200, `/register/email-code/` rejects GET with 405, HTTP redirects to HTTPS, and HSTS remains enabled. Anonymous generator access still redirects to `/login/`; the production administrator password remains intentionally absent from repository memory.
- `.env`, `data`, `exe`, `png`, `temp_zips`, and their persistent inodes were preserved. Migrations `0008_activationcode` and `0009_registrationemailcode` are applied; `migrate --check` and SQLite `quick_check` pass with 3 users and all 39 task rows retained. Both new tables began empty, and database plus GitHub gates report zero active client builds.
- The first cutover attempt safely rolled back because Docker health was still `starting` when the application was already responding. The corrected script waited for `healthy`, repeated final database/GitHub gates, and completed successfully; no data was lost.
- Keep `/opt/rdgen-backups/20260805-171543-16389d36cd35`, `/opt/rdgen-previous-20260805-171543-16389d36cd35`, and image tag `rdgen-rollback:20260805-171543-16389d36cd35` for the current rollback. The backup directory contains online and both stop-time SQLite snapshots plus the prior environment and source archive. Retain `20260723-162446-e7e4740f6986` and earlier rollback sets as fallbacks.
- Push-triggered Docker run `30992470460` failed at the known Docker Hub login step; it did not dispatch a client build. No live generator form was submitted during deployment or verification.

## Historical Verified Outputs

- macOS dual-architecture validation:
  - implementation commit: `5694553478ccde3967446c460e734ae719f278d6`
  - GitHub Actions run: `29975374837`
  - outputs: `MacAudit-x86_64.dmg` and `MacAudit-aarch64.dmg` as separate architecture-specific images, not a Universal binary
  - both app bundles passed architecture, ad-hoc codesign, and DMG checksum verification on real macOS runners
  - local SHA-256: x86_64 `25151cb4d1349fa2055f98393547174c05c7f536bb391d4ba962e072333e234e`; aarch64 `849022e5ca9a84b24cbb7ef233cbb253e0fee8e24a3d1b05b85d18207662eb67`
  - local archive directory: `D:\rustdesk-生成器\rdgen\output\macos-validation-29975374837`
  - production P12 signing, notarization, and stapling were not exercised
- Windows self-signed signing test:
  - filename: `SignTest`
  - UUID: `82f5ea38-c4ab-461e-a090-4e03f5d014bd`
  - GitHub Actions run: `26007760512`
  - Local downloaded outputs:
    - `D:\rustdesk-生成器\sign-test-output\SignTest.exe`
    - `D:\rustdesk-生成器\sign-test-output\SignTest.msi`
  - Both were signed by `CN=RDGen Self-Signed Code Signing`.
- Android universal output test:
  - filename: `WuYouDesk`
  - UUID: `9de4743a-ec38-4266-b155-cd383ae64685`
  - Expected and verified outputs on generator server:
    - `WuYouDesk-universal.apk`
    - `WuYouDesk-aarch64.apk`
    - `WuYouDesk-armv7.apk`
    - `WuYouDesk-x86_64.apk`
