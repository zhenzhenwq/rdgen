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

## Upstream RustDesk Source References

### Client

- Current official client source reference: `D:\rustdesk-生成器\rustdesk-src`.
- Remote: `https://github.com/rustdesk/rustdesk.git`; local branch `upstream-master` tracks `origin/master`.
- Synced on 2026-08-09 to official default-branch commit `11190fa54e45fd244ad46b46052f92be6a01d3c5` (`docs: fix comma splice gui tutorial in README.md (#15787)`, committed 2026-08-08 09:33:58 +0800).
- Latest stable tag observed during that sync is `1.4.9` at `6c578292e8ebbbec708b76986ba8c4bc7c509747`; the synced master worktree currently declares RustDesk `1.4.9` in `Cargo.toml` and `1.4.9+67` in `flutter/pubspec.yaml`.
- The `libs/hbb_common` submodule is initialized at `69cea8dafee147848ae88702029f4bf7df7224c3` (`main`). The clone is intentionally shallow and partial (`blob:none`) but has a complete current working tree; fetch more history only when a later question needs it.
- Treat this directory as the clean current-upstream reference for future source questions. Do not modify it unless the user explicitly asks for an upstream-source change. The dirty `rustdesk-src-147-inspect` and `rustdesk-src-149-inspect` trees are separate patch experiments and must not be cleaned or overwritten.

### OSS Server

- Current official OSS server source reference: `D:\rustdesk-生成器\rustdesk-server-src`.
- Remote: `https://github.com/rustdesk/rustdesk-server.git`; local `master` tracks `origin/master`.
- Synced on 2026-08-09 to official default-branch commit `a7736be5e40f85bfc141120dce587e836e5d4b80` (`Delete .github/dependabot.yml`, committed 2026-08-07 16:56:36 +0800).
- Latest stable tag observed during the sync is `1.1.16` at `73523b31cfd25d77dee862e6fc9f5e1fb5e485ef`; current master declares development version `1.1.17` in `Cargo.toml`.
- The `libs/hbb_common` submodule is initialized at `69cea8dafee147848ae88702029f4bf7df7224c3`. The clone is intentionally shallow and partial (`blob:none`) with a complete, clean current working tree.
- Treat this as the clean current OSS server reference for later `hbbs`/`hbbr` questions. Do not modify it unless explicitly requested, and read its own `AGENTS.md` before any future edit; it forbids production `unwrap()`/`expect()` outside stated exceptions and formatting-only churn.

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
- The current deployed application release is `11bd5bd3f877ef02c702096dbb2a606302d136f9` (tree `0f5b6f760ced089e1b82ee540c9777a879ccc9c9`). It retains the scoped, read-only build-history dashboard and removes the shared 1180px desktop cap so build records, user management, and activation-code management use all space to the right of the 248px sidebar. Form panels retain their own narrower width limits.
- New registrations require a short-lived email code and start without membership. Staff can create, list, filter, and revoke unused codes for one generation, 3 days, 7 days, 30 days, or lifetime; plaintext activation codes are shown only at creation and stored as hashes. The production SMTP account and authorization value are intentionally absent from repository memory.
- The server application is built from `11bd5bd`; later documentation-only commits do not change the live image. Push-triggered Docker failures remain limited to the repository's existing Docker Hub login step and do not dispatch client builds or affect the directly deployed server image.
- GitHub Actions run `29975374837` passed the complete validation matrix for `x86_64` and `aarch64`: customization validation, compilation, embedded configuration packaging, ad-hoc code signing, bundle metadata and architecture checks, DMG creation, `hdiutil verify`, and artifact upload. Validation mode skipped production upload and cleanup callbacks by design.
- A push to `master` starts `docker-build.yml`; it does not dispatch a RustDesk client generator workflow.
- Confirm the current local and remote state with `git status --short --branch`, `git log --oneline -n 8 --decorate`, and a fresh remote query before follow-up release work.

## Current Deployment State

- Deployment ID: `20260806-114847-11bd5bd3f877`.
- Source archive SHA-256: `e496589895e3e69e8f8071fb859bd3d28281f9b1d143ae84586b280e31538b94`. Verified live image: `sha256:3661f8b5f014a789656915bb18cbc719aa1575bb0c61ed9c549c311ae0e9a63f`.
- The service is `running`, `healthy`, restart count `0`, and has no post-deploy error fingerprints. The complete 177-test suite passed locally and again in the candidate image running Django `5.2.16`; the copied-production migration rehearsal, all three full-width management-page render checks, build-record permission checks, login/registration rendering, static-asset hashes, and isolated candidate instance also passed.
- Production Nginx now serves only the two exact login assets at `/static/rdgenerator/login-modern.css` and `/static/rdgenerator/auth-build-flow.png`. The prior Nginx configuration is in the rollback backup, `nginx -t` passes, and the existing TLS, redirect, HSTS, login rate-limit, and application proxy rules remain unchanged.
- Public `/login/`, `/register/`, both new static assets, and `/healthz` return 200; `/register/email-code/` rejects GET with 405, HTTP redirects to HTTPS, and anonymous generator access still redirects to `/login/`. Browser verification found the stylesheet and 1254×1254 illustration loaded, no horizontal overflow, and no console issues.
- `.env`, `data`, `exe`, `png`, and `temp_zips` were preserved. `migrate --check` and SQLite `quick_check` pass with 4 users and all 39 historical task rows retained. Database and GitHub gates reported zero active client builds before, during, and after the switch.
- Keep `/opt/rdgen-backups/20260806-114847-11bd5bd3f877`, `/opt/rdgen-previous-20260806-114847-11bd5bd3f877`, and image tag `rdgen-rollback:20260806-114847-11bd5bd3f877` for the current rollback. The backup includes online and final SQLite snapshots, the prior environment and Nginx configuration, the exact source archive, build/test logs, and image metadata. Retain `20260806-112556-c304e1573be8` and earlier rollback sets as fallbacks.
- No live generator form was submitted and no client workflow was dispatched during deployment or verification.

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
