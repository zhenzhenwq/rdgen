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
- Public Actions history contains successful manual Windows generator runs for `8e33770` and `cd2c358`, but their artifacts were not audited here. No Linux, macOS, or Android build has been verified for this batch.
- The automatic Docker runs for `8e33770` and `cd2c358` failed before image build because Docker Hub login inputs were unavailable.
- The current deployed application release is `f2f8ea0ecc0ccff4178e81e1ca95dbb179005a81` (tree `3499379ef567692978e4b55f917e6f9b5dce54b8`). Windows x64 builds now remain pending until both the EXE and MSI have reached the generator and an authenticated finalization call validates both non-empty files. MSI build/sign/package failures are no longer optional, and callback/poll races cannot bypass or undo finalization.
- Commits through `11ce7a5` were on `origin/master` before the final deployment record was written; verify the remote tip before future work. A push to `master` starts the known Docker image workflow.
- A push to `master` starts `docker-build.yml`; it does not dispatch a RustDesk client generator workflow.
- Confirm the current local and remote state with `git status --short --branch`, `git log --oneline -n 8 --decorate`, and a fresh remote query before follow-up release work.

## Current Deployment State

- Deployment ID: `20260722-124503-f2f8ea0ecc0c`.
- Verified live image: `sha256:f87baa88f651ccb10b8b8c9312c54a1661d11cacce4541766dd4f16b138921db`.
- The service was verified `running`, `healthy`, restart count `0`, and with no error fingerprints in live logs. Django `5.2.16` passed all 104 tests inside the candidate image; both Windows workflow command tests also passed.
- Anonymous generator access redirects to `/login/`. The production `admin` superuser exists; its password is intentionally absent from repository memory.
- HTTPS uses a trusted Let's Encrypt IPv4 certificate, HTTP redirects to HTTPS, HSTS is initially 300 seconds, invalid hosts return 400, and login rate limiting returns 429 after the configured burst.
- `.env`, `data`, `exe`, `png`, `temp_zips`, and SQLite inodes were preserved. Migrations `0004` through `0006` are applied; `migrate --check` and SQLite `quick_check` passed with 3 users, 3 entitlement rows, and all 27 task rows retained.
- `/etc/cron.d/rdgen-cleanup` runs the retention command hourly under `flock`. The first enforced cleanup removed 13 expired secret ZIPs and one empty directory, no generated installer and no quota reservation; the immediate follow-up dry-run was empty.
- Keep `/opt/rdgen-backups/20260722-124503-f2f8ea0ecc0c`, `/opt/rdgen-previous-20260722-124503-f2f8ea0ecc0c`, and image tag `rdgen-rollback:20260722-124503-f2f8ea0ecc0c` for the current rollback. Retain the preceding `20260722-122857-11ce7a56af22`, `20260722-110755-276fb0c016c6`, and earlier rollback sets as fallbacks.

## Historical Verified Outputs

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
