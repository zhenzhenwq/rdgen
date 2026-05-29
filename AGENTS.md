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
- Generator server is reachable at `http://120.55.0.199:8000/`.
- The deployed generator directory on `120.55.0.199` is `/opt/rdgen`, but that server currently does not have `git` installed.
- The live Docker service is `rdgen-rdgen-1`, published on host port `8000`.
- If deploying source changes to `120.55.0.199`, do not assume `git pull` works there. Either install git deliberately, upload a controlled source snapshot, or rebuild/recreate the Docker service from a known copied tree.
- The old project `D:\rustdesk_web客户端\rdgen-repo` remains read-only even if it contains useful reference fixes.

## Current Git Caveats

- Local HEAD at handoff is the latest local commit; confirm with `git log --oneline -n 8 --decorate`.
- Local `origin/master` may be stale because fetch/push had network/proxy/credential friction.
- Recent functional commits:
  - `e94a851 add self-signed windows code signing`
  - `3c382cc document windows signing test`
  - `65b491a add android universal apk output`
  - `d4c7f42 document android universal apk verification`
  - latest `add new window handoff memory` commit
- The Android universal APK workflow was proven by a live build, so the functional Android change is not theoretical.
- A final documentation push may still be needed if GitHub rejects credentials in a new session.

## Recently Verified Outputs

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
