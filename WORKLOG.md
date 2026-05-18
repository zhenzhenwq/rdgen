# Worklog

## 2026-05-08

### Repository Setup

- Started in `D:\rustdesk-生成器`.
- Directory was initially empty and not a Git repository.
- Initial clone failed because global Git proxy pointed to `http://127.0.0.1:7892`, which was unavailable.
- Cloned upstream successfully with temporary proxy overrides:
  `git -c http.proxy= -c https.proxy= clone --depth 1 https://github.com/bryangerlach/rdgen.git rdgen`
- Local repository path:
  `D:\rustdesk-生成器\rdgen`
- Checked latest local commit:
  `0537a2c Applied missing branding and icon customization to .deb and AppImage builds (#248)`
- Repository status after clone was clean.

### Upstream / Live Generator Review

- Reviewed `https://github.com/bryangerlach/rdgen`.
- Reviewed the author's live generator at:
  `https://rdgen.crayoneater.org/`
- Did not submit the live generator form.
- Chrome DevTools MCP connection failed to attach to local Chrome.
- Used Playwright fallback with a temporary install in `%TEMP%\rdgen-pw-inspect`.
- Captured live-page screenshots into `output/playwright/`.

### Live Page Findings

- Main live form sections:
  - Select Platform
  - General
  - Custom Server
  - Security
  - Visual
  - Permissions
  - Code Changes
  - Other
- Supported platforms visible in the UI:
  - Windows 64Bit
  - Windows 32Bit
  - Linux
  - Android
  - macOS
- Platform switching was tested for all five platform options.
- No major field visibility changes were observed between platforms.
- The Android App ID field remains visible for all platforms.

### Local Code Review Notes

- Read `rdgenerator/templates/generator.html`.
- Read `rdgenerator/forms.py`.
- Read `rdgenerator/views.py`.
- Noted that the generator UI is mostly inline CSS/JS in `generator.html`.
- Noted a likely JavaScript bug in permission preset handling:
  `enableTerminal.disable = true` should likely be `enableTerminal.disabled = true`.
- Noted that manual settings parsing in `views.py` assumes every non-empty line contains `=`.
- Noted that download and image endpoints build paths from request query parameters and should be reviewed before public deployment.

### Memory Files

- Created `AGENTS.md`.
- Created `PROJECT_OVERVIEW.md`.
- Created `ROADMAP.md`.
- Created `WORKLOG.md`.

### Prior Project Review

- User provided previous customized project path:
  `D:\rustdesk_web客户端\rdgen-repo`
- Confirmed it is a Git repository.
- Remote:
  `https://github.com/zhenzhen122/rdgen.git`
- Current branch:
  `master`
- Latest commit:
  `8bd0b4b fix: add rendezvous_mediator.rs to x86 workflow copy list`
- Working tree had one local modification:
  `.github/workflows/sh-generator-windows.yml`
- Performed read-only comparisons against the clean upstream clone at:
  `D:\rustdesk-生成器\rdgen`

Observed reusable improvements from the prior project:

- UTF-8 handling in `.github/actions/decrypt-secrets/action.yml`.
- Windows workflow environment adds `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`.
- Windows MSI codepage patch changes `1252` to `65001`.
- Workflow upload timeout increased for generated artifacts.
- Windows EXE and MSI uploads split so optional MSI failure does not hide the EXE.
- Generated page can hide download links until files exist.
- Workflow status callbacks report progress and failure/cancel states.
- `hidecm` causes approve mode to be forced to `password`.

Observed personal/non-generic changes:

- Workflows check out `zhenzhen122/rustdesk` as `custom-overlay`.
- Workflows copy custom modules from that overlay into RustDesk source.
- This overlay appears tied to account/auth/device-login/client-specific behavior and should not be copied directly into the generic generator.

User constraint recorded:

- The old project at `D:\rustdesk_web客户端\rdgen-repo` is read-only reference material.
- Do not write, edit, format, move, delete, clean, or generate files inside that old project.

### Hide Connection Window Investigation

- Focused on the UI option:
  `Allow hiding the connection window from remote screen.`
- Compared current clean upstream project with old read-only project.
- The local `.github/patches/hidecm.diff` file is identical between both projects.
- Current clean upstream applies `hidecm.diff` in Android, Linux, and macOS workflows.
- Current clean upstream does not apply `hidecm.diff` in:
  - `.github/workflows/generator-windows.yml`
  - `.github/workflows/generator-windows-x86.yml`
  - `.github/workflows/sh-generator-windows.yml`
- Old project adds `hide-cm` workflow steps to those Windows workflows.
- Old project also changes `rdgenerator/views.py` so when `hidecm` is selected, `approve-mode` is forced to `password`.
- Conclusion: the generic fix should port only the backend `effectiveApproveMode` behavior and Windows workflow patch application steps. Do not port personal overlay logic.

### Hide Connection Window Fix Applied

- Updated current project `rdgenerator/views.py`:
  - Added `effectiveApproveMode = 'password' if hidecm else passApproveMode`.
  - Used `effectiveApproveMode` for both default and override `approve-mode`.
- Updated current project Windows workflows to apply `.github/patches/hidecm.diff` before build:
  - `.github/workflows/generator-windows.yml`
  - `.github/workflows/generator-windows-x86.yml`
  - `.github/workflows/sh-generator-windows.yml`
- Verification:
  - `python -m py_compile rdgenerator\views.py` passed.
  - `npx --yes js-yaml` parsed all three modified workflow YAML files successfully.

### GitHub Deployment Preparation

- Checked `setup.md` for the author's recommended deployment flow.
- Confirmed `gh` CLI is not installed on this machine.
- Renamed local remote:
  - `origin` -> `upstream`
  - `upstream` points to `https://github.com/bryangerlach/rdgen.git`
- Left `origin` unset until the user's own GitHub fork/repository URL is available.
- Updated `docker-compose.yml` to use `build: .` instead of the author's published image, because this deployment must include the local `hidecm` fix.
- Added `output/` to `.gitignore` so Playwright screenshots are not pushed.
- Created local commit:
  `8a7c216 fix hide connection window builds`
- Server/GitHub secrets still require user-specific values:
  - GitHub fork/repository URL
  - GitHub username
  - Fine-grained GitHub token for the fork
  - Public server URL for `GENURL`
  - Matching `ZIP_PASSWORD` in GitHub Actions secret and server environment

### GitHub Fork Setup

- Created and prepared the user's GitHub fork:
  `https://github.com/zhenzhenwq/rdgen`
- Added `origin` remote pointing to the fork and kept the author's repository as `upstream`.
- Pushed the local fixed branch to `origin/master`.
- Enabled GitHub Actions on the fork through the GitHub web UI.
- Added repository Actions secret `ZIP_PASSWORD` through the GitHub web UI.
- Created fine-grained personal access token `rdgen-build-dispatch` through the GitHub web UI:
  - Resource owner: `zhenzhenwq`
  - Repository access: only `zhenzhenwq/rdgen`
  - Expiration: no expiration
  - Repository permissions:
    - `Actions`: read and write
    - `Workflows`: read and write
    - `Metadata`: read-only, required by GitHub
- The token value was copied in the browser and must be stored by the user for the server `GHBEARER` environment variable. Do not commit or log the token value.
- Still pending:
  - Public server URL/domain for GitHub Actions secret `GENURL`
  - Server deployment environment values

### Server Deployment Preparation

- Received deployment server details:
  - Host: `120.55.0.199`
  - SSH user: `root`
  - SSH port: `22`
- Verified SSH port 22 is reachable.
- Verified the server OS and runtime state:
  - OS: CentOS Linux 8
  - Docker is installed.
  - Docker Compose v2 is installed.
  - `git` is not installed.
  - Port 80 is already used by nginx.
  - Port 8000 was not occupied during the initial check.
- Added GitHub Actions secret `GENURL` with the initial direct-IP URL:
  `http://120.55.0.199:8000`
- Updated `docker-compose.yml` to read deployment settings from `.env` instead of storing placeholder values directly in the compose file.
- Added `.env.example` for non-secret deployment configuration reference.
- Updated `.dockerignore` so `.env` and runtime artifact directories are not copied into the Docker image.
- Added Docker build args `PIP_INDEX_URL` and `PIP_TRUSTED_HOST` so deployments with restricted or unstable PyPI access can use a local/regional package mirror without hardcoding it.
- Planned deployment path:
  `/opt/rdgen`
- Planned public test URL:
  `http://120.55.0.199:8000`

### Server Deployment Completed

- Deployed current fork code to:
  `/opt/rdgen`
- Wrote server-local `.env` with deployment secrets and runtime settings. The `.env` file is not committed and is excluded from the Docker build context.
- Because the server does not have `git`, deployment used the GitHub branch archive download:
  `https://github.com/zhenzhenwq/rdgen/archive/refs/heads/master.tar.gz`
- Server-local `.env` uses an Aliyun PyPI mirror for Docker builds because the default PyPI index failed from inside the server build container.
- Built and started the service with:
  `docker compose up -d --build`
- Docker container status after deployment:
  `healthy`
- Public URL verified with HTTP 200:
  `http://120.55.0.199:8000/`
- Browser check confirmed the deployed page loads and contains:
  `Allow hiding the connection window from remote screen.`

### 500 During Generation Investigation

- User reported a 500 error when testing with:
  `C:\Users\32590\Downloads\Desk (1).json`
- Read the JSON locally and confirmed the configuration loads as a dictionary and has required form-like fields such as `platform`, `version`, `exename`, `passApproveMode`, and `hidecm`.
- The config enables `hidecm`, so it exercises the fixed hide-connection-window path.
- Identified a backend bug in `rdgenerator/views.py`:
  - GitHub workflow dispatch normally succeeds with HTTP `204 No Content`.
  - The current code treated `204` as success but still called `response.json()`.
  - Parsing an empty `204` response raises an exception and returns a 500 even when GitHub accepted the dispatch.
- Applied a compatibility fix:
  - Only parse JSON when the response body is non-empty.
  - Save the `GithubRun` record and render the waiting page on `204` success.
  - Fall back to the repository Actions page when no workflow run URL is available.
  - Avoid polling a `/runs/None` GitHub API URL when the dispatch response does not include a run id.
- Reproduced another 500 root cause inside the deployed container:
  - Host bind-mounted directories `exe/`, `png/`, and `temp_zips/` were created as root-owned.
  - The container application runs as Unix user `user` (`uid=1000`) and could not write `temp_zips/secrets_*.zip`.
  - Fixed the live server by changing those host directory owners to uid/gid `1000:1000`.
  - Added `entrypoint.sh` so future container starts create and chown runtime artifact directories before dropping to the app user.
- Reproduced the browser-only 500 with the imported config after the directory ownership fix:
  - The imported form data was accepted by the frontend and included `platform=windows`, `hidecm=on`, and the imported base64 images.
  - The backend still returned Django's generic 500 page before it printed a GitHub dispatch response.
  - Confirmed `GithubRun` DB writes work and the container can reach `https://api.github.com`.
  - Confirmed the app user cannot write files in `/opt/rdgen` but can write inside `temp_zips/`.
  - Root cause: `generator_view` wrote `data_*.json` to the project root before zipping secrets. After the Docker entrypoint began running Gunicorn as the unprivileged app user, that root-level temporary file write raised `PermissionError`.
- Fixed the browser-only 500 path:
  - Moved the temporary `data_*.json` file into `temp_zips/`, the same runtime directory already created and chowned for app writes.
  - Used UTF-8 when writing the temporary JSON because imported configs may contain non-ASCII company names.
  - Marked `GithubRun` as `success` when GitHub Actions uploads a finished client to `/save_custom_client`.
  - Normalized status comparisons in `/check_for_file` so both workflow conclusions and upload callbacks can advance the waiting page.
- During redeploy from the GitHub branch archive, Docker failed to execute `/opt/rdgen/entrypoint.sh` because tarball checkout did not preserve the executable bit.
- Added `chmod +x /opt/rdgen/entrypoint.sh` inside the Docker build so archive-based deployments start reliably.
- After that fix, the imported config successfully reached GitHub dispatch and GitHub returned a workflow run id, but the view still returned:
  `Connection error: attempt to write a readonly database`
- Root cause:
  - Docker image build created `db.sqlite3` as root.
  - Runtime Gunicorn now runs as the unprivileged `user`, so it could not insert the generated `GithubRun` record.
- Fixed database persistence and permissions:
  - Moved SQLite to `/opt/rdgen/data/db.sqlite3` by default through `SQLITE_PATH`.
  - Added a `./data:/opt/rdgen/data` Compose mount.
  - Updated `entrypoint.sh` to create/chown `data`, run migrations as the app user, then start Gunicorn.
  - Removed build-time migration so the runtime database owns its files correctly.
- Verified the browser flow with `C:\Users\32590\Downloads\Desk (1).json` after the database fix:
  - `/generator` returned HTTP 200.
  - The page navigated to `/check_for_file`.
  - A `GithubRun` record was saved with the returned GitHub run id.
- The triggered Windows workflow then failed in `.github/actions/decrypt-secrets` during `Load Secrets`.
- Root cause:
  - The imported config contains a non-ASCII company name.
  - On Windows runners, the Python action used the platform default output/file encoding and raised `UnicodeEncodeError` while masking/writing secrets.
- Fixed the decrypt action to use UTF-8 stdout/stderr and UTF-8 `GITHUB_ENV` writes, and to stringify values before masking/exporting.
- Re-ran the imported JSON flow after the UTF-8 fix:
  - GitHub Actions run `25533835760` completed successfully.
  - The server received `Desk.exe`.
  - The waiting page moved to the generated-download page.
- Found another upstream usability bug after successful generation:
  - `generated.html` always showed platform-specific hardcoded download links, including `Desk.msi`, even when only `Desk.exe` was uploaded.
  - Clicking a missing artifact would raise a backend 500.
- Fixed generated/failure pages to list only files actually present under the run's output directory, and changed `/download` to return 404 for missing generated files.

### Generator UI Chinese / Blue-White Theme

- User requested `$frontend-design` changes for a blue-white generator page with Chinese display.
- Updated `rdgenerator/templates/generator.html`:
  - Reworked the main generator page from the original dark theme to a blue-white theme.
  - Translated visible form section names, labels, buttons, help text, and client-side save/load errors into Chinese.
  - Removed the bottom GitHub source-code and sponsor links so they are no longer displayed or clickable.
- Updated `rdgenerator/forms.py`:
  - Translated form choice labels and validation messages into Chinese while keeping submitted values unchanged.
- Updated flow templates for a consistent Chinese display:
  - `rdgenerator/templates/waiting.html`
  - `rdgenerator/templates/generated.html`
  - `rdgenerator/templates/failure.html`
  - `rdgenerator/templates/maintenance.html`
- Verification:
  - `python -m py_compile rdgenerator\forms.py rdgenerator\views.py` passed.
  - `git diff --check` passed.
- Follow-up frontend fix:
  - Avoid saving empty file-input objects into exported JSON.
  - Only render imported image previews when the imported value is a PNG data URL, preventing `/[object Object]` preview requests.
- Deployment verification:
  - Deployed commit `c6717f35d769bd58a3e9460e6ae2feb58ae4f837` to `/opt/rdgen`.
  - Docker container reported `healthy`.
  - Public homepage returned HTTP 200 at `http://120.55.0.199:8000/`.
  - Browser import test with `C:\Users\32590\Downloads\Desk (1).json` populated the form without triggering a new build.
  - Confirmed source-code and sponsor links are absent from the generator page.
  - Saved browser screenshot to `output/playwright/rdgen-blue-chinese-home.png`.

### Hide Desktop Three-Dot Settings Menu

- User requested hiding the RustDesk desktop client main-page three-dot menu shown beside the local ID.
- Analyzed RustDesk client source directly, without reading the old project:
  - The visible three-dot button is in `flutter/lib/desktop/pages/desktop_home_page.dart`.
  - It is rendered from `buildPopupMenu(context)` in the ID row and opens settings via `DesktopTabPage.onAddSetting`.
- Added generator option:
  - `hideSettingsMenu` / `隐藏主界面右上角三点菜单`.
- Added `.github/patches/hide_settings_menu.diff`:
  - Replaces the desktop home-page `buildPopupMenu(context)` call with a fixed-size empty `SizedBox`.
  - This hides the three-dot widget and removes its click target while preserving row spacing.
- Wired the option through `rdgenerator/views.py` into the encrypted Actions payload.
- Added workflow patch steps for:
  - Windows x64
  - Windows x86
  - Self-hosted Windows
  - Linux
  - Android
  - macOS
- Compatibility check:
  - `git apply --check` passed against RustDesk tags `1.3.3` through `1.4.6` and current `master`.

### Bridge Workflow Pub Cache Failure

- Investigated failed generation URL:
  - `/check_for_file?filename=Jssvag&uuid=074406d3-2a5e-420b-a779-004c905be33f&platform=windows`
  - GitHub Actions run: `25543182149`
- Result:
  - The waiting page correctly moved to the failure page.
  - No generated files existed under `exe/074406d3-2a5e-420b-a779-004c905be33f`.
- Root cause:
  - The workflow failed before Windows compilation.
  - `generate-bridge / Install flutter rust bridge deps` failed during `flutter pub get`.
  - Dart pub crashed with `Null check operator used on a null value` inside `HostedSource._getAdvisories.readAdvisoriesFromCache`.
  - This appears tied to restored pub advisory cache data, not the RustDesk three-dot menu patch.
- Fix:
  - Disabled Flutter pub-cache restore in `.github/workflows/bridge.yml`.
  - Removed `${PUB_CACHE}/hosted/pub.dev/.cache` before bridge `flutter pub get`.
  - Kept cargo/tool caches intact.

### Jssvag Clean Local Config Retest

- Backed up and removed local client state:
  - `C:\Users\32590\AppData\Roaming\Jssvag`
  - `C:\Users\32590\AppData\Local\Jssvag`
  - Backup directory: `D:\rustdesk-生成器\backups\Jssvag-20260508-173215`
- Started `C:\Users\32590\Downloads\Jssvag (7).exe`; it launched from `%LOCALAPPDATA%\Jssvag`.
- Fresh client config no longer contained the old `vwag.cc` rendezvous server.
- Fresh client log showed:
  - generated new ID `6568890`
  - `start rendezvous mediator of desk.jssvag.com`
  - UDP/NAT responses from `desk.jssvag.com:21116` and `desk.jssvag.com:21115`
  - `sysinfo updated`
  - repeated `register_pk of desk due to key not confirmed`
- DNS confirmed `desk.jssvag.com -> 45.207.213.2`.
- Pulled read-only database snapshots from the RustDesk server to `D:\rustdesk-生成器\server-snapshots\rustdesk-20260508-173643`.
- The RustDesk API database recorded the fresh Windows 11 client:
  - peer ID `6568890`
  - hostname `desktop-s1vq4l4`
  - version `1.4.6`
  - last IP `220.166.163.248`
  - created `2026-05-08 17:33:59 +08:00`
  - updated `2026-05-08 17:36:20 +08:00`
- Server observation:
  - formal container `rustdesk-rustdesk-1` still had `MUST_LOGIN=Y` in the running environment.
  - test container `rustdesk-test` had `MUST_LOGIN=N` and separate `22114-22119` ports.

### RustDesk Server OSS Native Retest

- User reported Jssvag UI still shows `Not ready. Please check your connection`.
- Installed official RustDesk Server OSS `.deb` packages on `45.207.213.2`:
  - `rustdesk-server-hbbs_1.1.15_amd64.deb`
  - `rustdesk-server-hbbr_1.1.15_amd64.deb`
- Backed up previous Docker data to `/root/rd-official-install/backup-before-official-20260508-094704`.
- Stopped Docker RustDesk containers and disabled their restart policy:
  - `rustdesk-rustdesk-1`
  - `rustdesk-test`
- Started official native systemd services:
  - `rustdesk-hbbs.service`
  - `rustdesk-hbbr.service`
- Reused the original server key pair from `/data/rustdesk/server` in `/var/lib/rustdesk-server`.
- Added systemd overrides:
  - `hbbs`: `/usr/bin/hbbs -r 45.207.213.2:21117 -k dH0WO9xf8kmRM1IjDhprjn+MhuXnIEvhnTWQR21agIY=`
  - `hbbr`: `/usr/bin/hbbr -k dH0WO9xf8kmRM1IjDhprjn+MhuXnIEvhnTWQR21agIY=`
- Verified listeners are native `hbbs/hbbr` on `21115-21119`; Docker no longer owns those ports.
- Read the user's reference script `C:\Users\32590\Desktop\阿里云服务器信息写入.bat`; it uses `xdesk.exe --config "host=...,key=..."`.
- Confirmed RustDesk 1.4.6 source only applies `--config` when the client is installed and running with admin/root privileges, so it does not update the portable Jssvag runtime.
- Directly wrote Jssvag local config in `Jssvag2.toml`:
  - `custom-rendezvous-server = '45.207.213.2'`
  - `relay-server = '45.207.213.2:21117'`
  - `key = 'dH0WO9xf8kmRM1IjDhprjn+MhuXnIEvhnTWQR21agIY='`
- Found local DNS/proxy issue:
  - `desk.jssvag.com` resolved locally to `198.18.0.75`, not `45.207.213.2`.
  - MaoMaoCloud TUN was a default route and HTTP proxy was enabled at `127.0.0.1:7892`.
- Added a host route for `45.207.213.2/32` via `WLAN` gateway `192.168.31.1`; `Test-NetConnection` then used source `192.168.31.25`.
- After bypassing TUN and using direct IP, Jssvag log showed stable NAT responses from `45.207.213.2:21116` and `45.207.213.2:21115`, but still repeated:
  - `register_pk of 45.207.213.2:21116 due to key not confirmed`
- Forced TCP by setting `disable-udp = 'Y'`; client connected but timed out waiting for rendezvous handshake:
  - `rendezvous mediator error: deadline has elapsed`
- Server `/var/lib/rustdesk-server/db_v2.sqlite3` `peer` table remained empty.
- Current conclusion:
  - Official native server is installed and owns ports correctly.
  - Local fake-IP/proxy was a real problem and was bypassed for `45.207.213.2`.
  - The current pre-existing `Jssvag (7).exe` still does not complete key confirmation with the native server; likely needs a newly generated client that embeds server fields using the generator fix committed later (`fa50cd9`).

### RustDesk Official Client Same Failure

- User confirmed the official RustDesk client shows the same connection problem as Jssvag.
- Temporarily configured the official client to use the RustDesk server:
  - `custom-rendezvous-server = '45.207.213.2'`
  - `relay-server = '45.207.213.2:21117'`
  - `key = 'dH0WO9xf8kmRM1IjDhprjn+MhuXnIEvhnTWQR21agIY='`
- Official client log repeated:
  - `register_pk of 45.207.213.2:21116 due to key not confirmed`
  - TCP NAT test responses from `45.207.213.2:21116` and `45.207.213.2:21115`
- Verified the native official server is active and listening:
  - `hbbs`: TCP `21115`, TCP/UDP `21116`, TCP `21118`
  - `hbbr`: TCP `21117`, TCP `21119`
  - Linux firewall/UFW is not blocking input.
- Synthetic UDP tests:
  - From the local PC, explicitly bound to WLAN `192.168.31.25`, UDP packets to `45.207.213.2:21116` did not appear on `45.207.213.2` `ens17`.
  - From the separate server `120.55.0.199`, UDP packets to `45.207.213.2:21116` also did not appear on `45.207.213.2` `ens17`.
  - From `45.207.213.2` to `120.55.0.199`, UDP packets were captured successfully on `120.55.0.199`.
  - From the local PC to `120.55.0.199:21116`, UDP packets were captured successfully.
- Conclusion:
  - The shared failure is not caused by the generator or by the official Windows client configuration.
  - `45.207.213.2` is not receiving inbound public UDP traffic on `21116`; this happens before packets reach the server OS.
  - The likely fix is in the cloud/provider firewall or security group for `45.207.213.2`: allow inbound `21116/UDP` at minimum, and keep the RustDesk TCP ports open.

### Multi-Method UDP Recheck

- Re-ran several independent checks after the user requested more test methods.
- Method 1: `tcpdump` on `45.207.213.2` `ens17` with local PC and `120.55.0.199` sending synthetic UDP to `45.207.213.2:21116`.
  - Result: `0` matching UDP packets captured.
- Method 2: same server capture with TCP and UDP to the same destination port.
  - Local TCP connection to `45.207.213.2:21116` was captured immediately.
  - Local UDP packet to `45.207.213.2:21116` was not captured.
- Method 3: `120.55.0.199` sent UDP to multiple destination ports on `45.207.213.2`: `53`, `443`, `21115`, `21116`, `21117`, `21118`, `21119`, `40000`.
  - Result: no inbound UDP packets to `45.207.213.2` were captured.
- Method 4: reverse sanity check from `45.207.213.2` to `120.55.0.199:41116`.
  - Result: UDP packets were captured successfully on `120.55.0.199`, proving the testing method works and UDP outbound from `45.207.213.2` works.
- Method 5: server network/firewall counters.
  - `hbbs` listens on `*:21116/UDP`.
  - `INPUT` policy is `ACCEPT`; no host firewall rule explains the drop.
  - After synthetic test bursts, host-level packet counters did not reflect the missing inbound UDP test packets.
- Method 6: real official RustDesk client restart while capturing `21115-21119`.
  - Server captured only TCP NAT-test traffic on `21115/21116`.
  - No UDP packets were captured.
  - Official client log still showed `start udp: 45.207.213.2:21116` and repeated `register_pk ... due to key not confirmed`.
- Updated conclusion:
  - External inbound UDP to `45.207.213.2` is blocked before the packet reaches the server OS.
  - This appears broader than only `21116/UDP`; tested external UDP to several destination ports did not reach `45.207.213.2`.
  - Fix remains provider-side security group/firewall/upstream UDP policy, not generator code.

### Windows Self-Signed Code Signing

- User chose the self-signed certificate path for generated Windows clients.
- Generated a local self-signed code signing certificate:
  - PFX: `D:\rustdesk-生成器\codesign\rdgen-selfsigned-codesign.pfx`
  - Public CER: `D:\rustdesk-生成器\codesign\rdgen-selfsigned-codesign.cer`
  - PFX base64 and password helper files are in the same `codesign` directory.
  - Certificate thumbprint: `198E54637FF5B21D964BDB7A06E964B79BAD0FFA`
- Added GitHub Actions repository secrets through the GitHub API:
  - `CODE_SIGN_PFX_BASE64`
  - `CODE_SIGN_PFX_PASSWORD`
- Updated Windows workflows to support local Authenticode signing with `signtool.exe`:
  - `.github/workflows/generator-windows.yml`
  - `.github/workflows/generator-windows-x86.yml`
  - `.github/workflows/sh-generator-windows.yml`
- Signing behavior:
  - If `CODE_SIGN_PFX_BASE64` and `CODE_SIGN_PFX_PASSWORD` are configured, workflows decode the PFX and sign generated `.exe`, `.dll`, and `.msi` files.
  - Timestamp signing is attempted first with `http://timestamp.digicert.com`; if timestamping fails, the workflow retries signing without timestamping.
  - If no self-signing secrets exist, the existing external signing service path using `SIGN_BASE_URL` / `SIGN_API_KEY` remains supported.
  - If neither signing method is configured, the workflow keeps the old skip behavior and continues with unsigned files.
- Validation:
  - Parsed the modified workflow YAML files successfully with PyYAML.
  - Secrets were accepted by GitHub API during creation.
- Caveat:
  - Self-signed signatures prove file integrity after signing, but Windows will not trust the publisher on other machines until the public `.cer` certificate is installed into trusted certificate stores.

### SignTest Build Verification

- Triggered a real Windows x64 generator build through the deployed generator at `120.55.0.199:8000`.
- Test input:
  - filename/app name: `SignTest`
  - UUID: `82f5ea38-c4ab-461e-a090-4e03f5d014bd`
  - RustDesk version: `1.4.6`
- GitHub Actions run:
  - `26007760512`
  - `Build Windows` completed successfully.
  - `sign dlls` completed successfully.
  - `sign exe and msi` completed successfully.
- Downloaded generated files from the generator server:
  - `D:\rustdesk-生成器\sign-test-output\SignTest.exe`
  - `D:\rustdesk-生成器\sign-test-output\SignTest.msi`
- Authenticode verification:
  - Both files have a signature.
  - Signer subject: `CN=RDGen Self-Signed Code Signing`
  - Thumbprint: `198E54637FF5B21D964BDB7A06E964B79BAD0FFA`
  - PowerShell status: `UnknownError` with message that the chain terminates in an untrusted root, which is expected until `rdgen-selfsigned-codesign.cer` is installed as trusted.
