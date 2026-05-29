# New Window Handoff

This file is the durable handoff for continuing the rdgen/RustDesk generator work in a new Codex window.

## Role / Style For New Window

Continue as a pragmatic coding agent working with the user in Chinese.

The user prefers direct action over long theory. Explain what you are doing, keep the user updated during long work, and implement when the intent is clear.

Do not ask for repeated background unless the answer is not available in these memory files or the local repository.

## Workspace

- Main repository:
  `D:\rustdesk-生成器\rdgen`
- Shell:
  PowerShell
- Current local branch:
  `master`
- Upstream author's project:
  `https://github.com/bryangerlach/rdgen`
- Current user fork/build repo:
  `https://github.com/zhenzhenwq/rdgen.git`
- Author's live generator:
  `https://rdgen.crayoneater.org/`
- User's deployed generator:
  `http://120.55.0.199:8000/`
- Old user project:
  `D:\rustdesk_web客户端\rdgen-repo`

Important: the old user project is read-only. Do not write, edit, format, delete, move, generate files, run formatters, or clean anything inside `D:\rustdesk_web客户端\rdgen-repo`.

## Secret Handling

Do not write secrets into repository files.

Sensitive items intentionally omitted from this handoff:

- SSH passwords
- GitHub tokens
- GitHub bearer tokens
- Django secret keys
- upload bearer tokens
- PFX/code-signing passwords

The user provided server credentials during the prior conversation. If needed in the new window, ask the user again or use already configured secure local stores. Do not paste secrets back into final answers or memory files.

Code signing material exists outside the repo:

- Directory: `D:\rustdesk-生成器\codesign\`
- Public certificate: `rdgen-selfsigned-codesign.cer`
- PFX: `rdgen-selfsigned-codesign.pfx`
- PFX base64 helper: `rdgen-selfsigned-codesign.pfx.base64.txt`
- Password helper file exists in the same directory, but treat it as sensitive.
- Certificate thumbprint:
  `198E54637FF5B21D964BDB7A06E964B79BAD0FFA`
- Signer subject:
  `CN=RDGen Self-Signed Code Signing`

## Repository State At Handoff

Local HEAD:

- Confirm with `git log --oneline -n 8 --decorate`.
- The newest local commit should be `add new window handoff memory`.

Recent commits:

- latest `add new window handoff memory` commit
- `d4c7f42 document android universal apk verification`
- `65b491a add android universal apk output`
- `3c382cc document windows signing test`
- `e94a851 add self-signed windows code signing`
- `fa50cd9 embed server settings in custom client config`
- `c7a8ef8 add hide settings menu option`

At the end of the prior window, `git status --short --branch` showed:

```text
## master...origin/master [ahead 4]
```

This may partly be stale local remote-tracking state because GitHub fetch/push had proxy/credential problems and prior pushes were done through alternate methods. Do not assume `origin/master` is accurate until you run a fresh remote check.

Known Git/GitHub issue:

- Global Git proxy has been configured to `http://127.0.0.1:7892`.
- That proxy is often unavailable.
- Normal `git push origin master` failed through the proxy.
- `git -c http.proxy= -c https.proxy= push origin master` hung or hit credential-manager prompts.
- `credential.interactive=never` failed because Git could not retrieve a password.
- `gh` CLI was not installed/available in PowerShell.

Recommended first Git checks in a new window:

```powershell
cd D:\rustdesk-生成器\rdgen
git status --short --branch
git log --oneline -n 8 --decorate
git -c http.proxy= -c https.proxy= ls-remote https://github.com/zhenzhenwq/rdgen.git refs/heads/master
```

If remote auth is needed, coordinate with the user. Do not hardcode tokens in commands that may be logged.

## Core Project Summary

`rdgen` is a Django app that generates customized RustDesk clients.

Main flow:

1. User fills the generator form.
2. Django builds a RustDesk custom config.
3. Secrets/customization inputs are encrypted into a zip.
4. Django dispatches a GitHub Actions workflow for the selected platform.
5. The workflow builds RustDesk.
6. Built files are uploaded back to the generator server.
7. The waiting page polls GitHub run state.
8. The generated page exposes downloads.

Important files:

- `rdgenerator/forms.py`
  Django fields, labels, defaults, platform choices.
- `rdgenerator/views.py`
  Form handling, custom config serialization, GitHub dispatch, status polling, upload/download endpoints.
- `rdgenerator/templates/generator.html`
  Main form UI, inline CSS/JS, Chinese text, save/load config.
- `rdgenerator/templates/waiting.html`
  Progress/polling page.
- `rdgenerator/templates/generated.html`
  Download page.
- `rdgenerator/templates/failure.html`
  Failure page.
- `.github/workflows/generator-windows.yml`
  Windows x64 build.
- `.github/workflows/generator-windows-x86.yml`
  Windows x86 build.
- `.github/workflows/sh-generator-windows.yml`
  Windows self-hosted build path.
- `.github/workflows/generator-android.yml`
  Android build, now including universal APK creation.
- `.github/patches/hide_settings_menu.diff`
  RustDesk source patch to hide the three-dot/settings menu.
- `.github/patches/hidecm.diff`
  Upstream hide connection window patch, downloaded/applied by workflows.

## User Intent / Product Direction

The user previously had a heavily customized generator, but it lost generality. This project should preserve general-purpose behavior as much as possible while adding the user's requested production features.

Current design direction:

- Chinese UI.
- Blue-white theme.
- Remove sponsor/source-code links.
- Keep generator practical and deployment-focused.
- Avoid copying old personal fork overlays unless specifically requested and made optional.

## Completed Work

### Initial Setup

- Cloned author's rdgen repo into `D:\rustdesk-生成器\rdgen`.
- Reviewed author's GitHub repo and live generator.
- Created long-term memory files:
  - `AGENTS.md`
  - `PROJECT_OVERVIEW.md`
  - `ROADMAP.md`
  - `WORKLOG.md`

### Old Project Comparison

- Compared current project with old project at `D:\rustdesk_web客户端\rdgen-repo`.
- Old project is read-only.
- Identified useful generic ideas from old project:
  - UTF-8 handling for secret extraction.
  - MSI Unicode/codepage fixes.
  - Longer upload timeouts.
  - Splitting Windows EXE upload from optional MSI upload.
  - Hiding download links for missing files.
  - Better callback/progress/failure reporting.
  - Hide connection window fix by forcing permanent password approval mode.
- Avoided old project-specific overlays tied to `zhenzhen122/rustdesk`.

### Chinese Blue-White UI

- Main generator visible text converted to Chinese.
- Theme changed to blue-white.
- Source-code and sponsor display/jump links removed.
- Generated/waiting/failure pages styled/localized enough for deployed use.

### Hide Connection Window

User cared about:

`Allow hiding the connection window from remote screen.`

Findings:

- Author's UI exposed the option.
- It did not work correctly in current upstream build path.
- Old project had a generic fix.

Implemented:

- In `rdgenerator/views.py`, when `hidecm` is enabled:
  - `approve-mode` is forced to `password`.
  - `verification-method` becomes permanent-password behavior.
  - `allow-hide-cm = Y`.
- Windows workflows apply `hidecm.diff` before build:
  - `generator-windows.yml`
  - `generator-windows-x86.yml`
  - `sh-generator-windows.yml`

### Hide Settings / Three-Dot Menu

User showed a RustDesk client screenshot with the three-dot menu and wanted those entry points hidden.

Implemented:

- `rdgenerator/forms.py` has a Chinese `settings` field:
  - `settingsY`: allow settings
  - `settingsN`: disable settings
- `rdgenerator/views.py` writes:
  - `disable-settings = Y` when settings are disabled.
- Windows workflows apply:
  - `.github/patches/hide_settings_menu.diff`
- Workflows fetch the patch from the current repository SHA so GitHub Actions uses the exact repo version.

### Embedded Server Settings

There was a client connectivity debugging phase where generated clients and official manually configured clients were compared.

Generator-side fix:

- `rdgenerator/views.py` now writes server settings into custom config:
  - `custom-rendezvous-server = server`
  - `relay-server = server`
  - `key = user key or default key`

Commit:

- `fa50cd9 embed server settings in custom client config`

### RustDesk Server Investigation

Separate from generator code, the user had RustDesk server connectivity problems.

Main server under investigation:

- `45.207.213.2`

Actions performed:

- Stopped Docker-based RustDesk server.
- Installed/started official native `hbbs`/`hbbr` services.
- Reused keypair from old Docker data.
- Confirmed local services listened on:
  - `21115/TCP`
  - `21116/TCP`
  - `21116/UDP`
  - `21117/TCP`
  - `21118/TCP`
  - `21119/TCP`
- Tested official RustDesk client and generated Jssvag client.

Important finding:

- Inbound UDP to `45.207.213.2` did not reach the server OS.
- This was proven with multiple methods:
  - `tcpdump` on `45.207.213.2`
  - UDP from local PC
  - UDP from `120.55.0.199`
  - TCP sanity checks to same host/port
  - reverse UDP from `45.207.213.2` to `120.55.0.199`
- UDP worked toward `120.55.0.199`, but not inbound to `45.207.213.2`.
- Conclusion:
  The problem was provider/security-group/upstream UDP filtering for `45.207.213.2`, not generator code.

Remember:

- RustDesk OSS generally needs `21116/UDP` for normal rendezvous/NAT traversal behavior.
- TCP ports alone may not be enough for the observed registration/key-confirmation path.

### Windows Self-Signed Code Signing

User chose self-signed certificate signing.

Implemented:

- Created self-signed code-signing certificate outside repo.
- Added GitHub repository secrets:
  - `CODE_SIGN_PFX_BASE64`
  - `CODE_SIGN_PFX_PASSWORD`
- Updated Windows workflows:
  - `.github/workflows/generator-windows.yml`
  - `.github/workflows/generator-windows-x86.yml`
  - `.github/workflows/sh-generator-windows.yml`

Behavior:

- If `CODE_SIGN_PFX_BASE64` and `CODE_SIGN_PFX_PASSWORD` exist, workflows sign:
  - generated EXE files
  - DLL files
  - MSI files
- Timestamp server attempted:
  `http://timestamp.digicert.com`
- If timestamping fails, signing retries without timestamp.
- If self-signed secrets are absent, workflow can still use the external signing service if configured.
- If no signing method exists, workflows skip signing and continue.

Validation:

- Real Windows x64 test build:
  - filename: `SignTest`
  - UUID: `82f5ea38-c4ab-461e-a090-4e03f5d014bd`
  - GitHub Actions run: `26007760512`
  - Outputs downloaded locally:
    - `D:\rustdesk-生成器\sign-test-output\SignTest.exe`
    - `D:\rustdesk-生成器\sign-test-output\SignTest.msi`
- `Get-AuthenticodeSignature` confirmed both files are signed.
- Status is expectedly untrusted on normal machines until the public `.cer` is installed to trusted stores.

Important user-facing explanation:

- Self-signed signing does not make Windows trust the publisher automatically.
- It proves integrity after signing, but users still see trust warnings unless they trust/install the certificate.

### Android Universal APK

User asked why Android output did not show:

- one three-architecture combined package
- plus three separated ABI packages

Old behavior:

- Android workflow built three ABI split APKs:
  - `aarch64`
  - `armv7`
  - `x86_64`
- It did not produce a universal APK.

Old reported URL:

`http://120.55.0.199:8000/check_for_file?filename=WuYouDesk&uuid=dcaa5218-3b21-4883-a4e9-d28a96c467eb&platform=android`

Old UUID result:

- `WuYouDesk-aarch64.apk`
- `WuYouDesk-armv7.apk`
- `WuYouDesk-x86_64.apk`

Implemented:

- Modified `.github/workflows/generator-android.yml`.
- Matrix jobs upload split APK artifacts named:
  - `android-split-aarch64`
  - `android-split-armv7`
  - `android-split-x86_64`
- Deploy job downloads artifacts with:
  - `actions/download-artifact@v4`
  - `merge-multiple: true`
- Deploy job creates universal APK:
  - starts from base `aarch64` APK
  - copies native `lib/` folders from `armv7` and `x86_64`
  - excludes `META-INF/`
  - zipaligns
  - signs with Android release signing secrets if available
  - otherwise signs with generated debug keystore
  - verifies with `apksigner`
- Uploads universal APK to the generator server and API server if configured.
- Deletes split artifacts after deploy cleanup.
- `rdgenerator/views.py` now sorts Android output in this intended order:
  - `-universal.apk`
  - `-aarch64.apk`
  - `-armv7.apk`
  - `-x86_64.apk`

Test:

- New test generation:
  - filename: `WuYouDesk`
  - platform: Android
  - RustDesk version: `1.4.6`
  - UUID: `9de4743a-ec38-4266-b155-cd383ae64685`
- GitHub run:
  `https://github.com/zhenzhenwq/rdgen/actions/runs/26630926700`
- Server directory confirmed:
  - `WuYouDesk-aarch64.apk`
  - `WuYouDesk-armv7.apk`
  - `WuYouDesk-universal.apk`
  - `WuYouDesk-x86_64.apk`
- Download page:
  `http://120.55.0.199:8000/check_for_file?filename=WuYouDesk&uuid=9de4743a-ec38-4266-b155-cd383ae64685&platform=android`

Note:

- The old UUID will not retroactively gain a universal APK.
- New Android generations should produce four files.
- Live server had not necessarily deployed the `list_generated_files()` sort change, but universal appears once uploaded.

## Live Server Notes

Generator server:

- URL: `http://120.55.0.199:8000/`
- Host directory: `/opt/rdgen`
- Docker service: `rdgen-rdgen-1`
- Published port: `8000`
- `/opt/rdgen` contains source-like files and runtime directories.
- `/opt/rdgen` is not a git checkout:
  - `.git` absent
  - `git` command not installed
- Runtime/generated directories:
  - `/opt/rdgen/exe`
  - `/opt/rdgen/png`
  - `/opt/rdgen/temp_zips`
  - `/opt/rdgen/data`

Docker compose mounts these runtime directories into the container:

- `./exe:/opt/rdgen/exe`
- `./png:/opt/rdgen/png`
- `./temp_zips:/opt/rdgen/temp_zips`
- `./data:/opt/rdgen/data`

If asked to deploy:

1. Inspect current `/opt/rdgen`.
2. Do not run blind destructive syncs.
3. Preserve `.env`, `exe`, `png`, `temp_zips`, `data`.
4. Either install git and convert/update carefully, or upload a clean source snapshot.
5. Rebuild Docker image if source files inside image changed.
6. Recreate/restart service and verify `http://120.55.0.199:8000/`.

## Browser / Tool Notes

- User specifically preferred browser operation for GitHub in an earlier phase.
- Chrome DevTools MCP failed earlier due attachment issues.
- Playwright fallback worked for author's site inspection.
- If user asks for UI/browser verification, use the browser/chrome-devtools skill/tool when possible; otherwise explain fallback.

## Known Remaining Risks / Tasks

1. GitHub remote state needs a clean verification.
2. `d4c7f42` and the latest `add new window handoff memory` commit may not be pushed due credential/network problems.
3. Live deployed generator may not contain the latest Android sort helper unless redeployed.
4. The generator still has backend hardening issues:
   - manual setting parsing assumes every line contains `=`
   - download endpoints need path traversal review
   - uploaded file sizes need stronger limits
   - broad exception handling around image processing
5. UI still has opportunities:
   - platform-specific field hiding
   - clearer Android download labels
   - better progress/failure guidance
6. Self-signed code signing is technically working but not publicly trusted.
7. `45.207.213.2` RustDesk server UDP issue is provider-side until proven otherwise.

## Suggested Prompt For New Window

Use this prompt when opening a new Codex window:

```text
你好，我们继续在 D:\rustdesk-生成器\rdgen 这个项目上工作。请先读取项目里的长期记忆文件：

- AGENTS.md
- PROJECT_OVERVIEW.md
- ROADMAP.md
- WORKLOG.md
- NEW_WINDOW_HANDOFF.md

这是 bryangerlach/rdgen 的 RustDesk 客户端生成器项目，我的当前 fork/build repo 是 https://github.com/zhenzhenwq/rdgen.git，线上生成器是 http://120.55.0.199:8000/。

旧项目 D:\rustdesk_web客户端\rdgen-repo 只能读，绝对不能写、不能格式化、不能删除、不能生成文件进去。

请注意：

1. 不要把服务器密码、GitHub token、PFX 密码、Django secret 等敏感信息写入仓库文件或最终回答。
2. 当前主要仓库是 D:\rustdesk-生成器\rdgen。
3. 先用 git status --short --branch 和 git log --oneline -n 8 --decorate 确认本地状态。
4. 本地 GitHub 网络/凭据可能有问题；global proxy 可能指向 127.0.0.1:7892。不要盲目假设 push/fetch 正常。
5. 120.55.0.199 的 /opt/rdgen 不是 git checkout，而且服务器上没有 git；部署时不要直接 git pull。要保护 .env、exe、png、temp_zips、data。

当前已经完成的重点：

- 页面改为中文蓝白风格。
- 去掉作者赞助和源码跳转。
- 修复 hide connection window：hidecm 开启时强制 approve-mode=password，并在 Windows workflow 应用 hidecm.diff。
- 增加隐藏 RustDesk 设置/三点菜单功能：settingsN 写 disable-settings=Y，并应用 hide_settings_menu.diff。
- 生成器已内置写入服务器配置 custom-rendezvous-server、relay-server、key。
- Windows 自签名签名已接入 GitHub Actions，SignTest 构建验证成功，签名者 CN=RDGen Self-Signed Code Signing，thumbprint=198E54637FF5B21D964BDB7A06E964B79BAD0FFA。注意自签名不等于公网可信。
- Android 已改为同时生成 1 个 universal APK 和 3 个 ABI split APK。

Android 修复验证：

- 新测试链接：http://120.55.0.199:8000/check_for_file?filename=WuYouDesk&uuid=9de4743a-ec38-4266-b155-cd383ae64685&platform=android
- 应该有：
  - WuYouDesk-universal.apk
  - WuYouDesk-aarch64.apk
  - WuYouDesk-armv7.apk
  - WuYouDesk-x86_64.apk
- 旧链接 dcaa5218-3b21-4883-a4e9-d28a96c467eb 是修改前生成的，所以只有三个 split 包，不会自动补 universal。

当前 local HEAD 应该是最新的 `add new window handoff memory` 交接提交，请用 `git log --oneline -n 8 --decorate` 确认。最近功能/交接提交包括：

- e94a851 add self-signed windows code signing
- 3c382cc document windows signing test
- 65b491a add android universal apk output
- d4c7f42 document android universal apk verification
- 最新的 add new window handoff memory 提交

请先确认这些提交是否已经在 GitHub 远端。如果 d4c7f42 或最新交接提交还没推上去，等我确认凭据/网络后再推。

我们下一步可能要继续部署、优化下载页显示、或者继续修复生成器功能。请按现有代码和记忆接着做，不要从头分析整个项目，除非需要验证具体文件。
```
