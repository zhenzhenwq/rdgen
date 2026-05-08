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
