# Roadmap

## Immediate Optimization Candidates

1. Improve the main generator UI layout:
   - clearer grouping
   - better spacing
   - more scannable controls
   - mobile responsive layout
2. Hide or de-emphasize platform-specific fields when they do not apply.
3. Add stronger client-side validation for:
   - configuration name
   - host/API URL format
   - Android App ID
   - PNG upload dimensions and size
   - manual settings syntax
4. Improve save/load configuration:
   - avoid repeatedly registering `change` handlers
   - restore platform icon active state after loading
   - restore permission preset state after loading
5. Improve generated/waiting/failure pages:
   - clearer build progress
   - GitHub log links
   - retry guidance
   - better file availability checks

## Completed UI Direction

1. The main generator and generation flow pages now use Chinese visible text.
2. The main generator page now uses a blue-white theme.
3. The bottom source-code and sponsor links were removed from the generator page.

## Backend Hardening Candidates

1. Validate and normalize manual `key=value` settings before splitting lines.
2. Protect file download endpoints from path traversal.
3. Add file size limits for uploaded images and returned build artifacts.
4. Ensure temporary zips can be cleaned reliably.
5. Avoid broad `except` blocks around image handling.
6. Review CSRF, allowed hosts, and public endpoint exposure before production deployment.
7. Avoid assuming GitHub dispatch returns a JSON body on every success path.
8. Preserve `GithubRun.github_run_id` support from current upstream, but handle GitHub dispatch responses defensively.
9. Add download existence checks before presenting or serving build artifacts.

## Code Quality Candidates

1. Move inline CSS and JavaScript out of `generator.html`.
2. Extract custom config building from `generator_view` into a testable helper.
3. Add focused unit tests for config serialization and filename sanitization.
4. Add template/UI smoke tests for platform selection and save/load behavior.
5. Consolidate duplicated permission serialization logic for default vs override settings.

## Reusable Fixes To Evaluate From Prior Project

1. Port UTF-8-safe secret extraction from `D:\rustdesk_web客户端\rdgen-repo\.github\actions\decrypt-secrets\action.yml`.
2. Port Windows MSI UTF-8 codepage patch in a generic way.
3. Increase artifact upload timeout from one minute to a safer value for large builds.
4. Split Windows EXE upload status from optional MSI upload so missing MSI does not block EXE availability.
5. Gate generated download buttons by actual uploaded file existence.
6. Add progress/failure workflow callbacks without binding to a specific external API server.
7. Keep `hidecm` generic fix: when hide connection window is enabled, use permanent password approval mode.
8. Review Windows x86 overlay file list fixes such as `rendezvous_mediator.rs`, but avoid copying personal overlay logic.

## Hide Connection Window Fix

The author's current code exposes `Allow hiding the connection window from remote screen.`, but Windows builds do not currently apply the `hidecm.diff` patch. The old project fixed this generically.

Required generic changes:

1. In `rdgenerator/views.py`, when `hidecm` is enabled, force `approve-mode` to `password` for both default and override settings.
2. In Windows workflows, apply `.github/patches/hidecm.diff` before build:
   - `.github/workflows/generator-windows.yml`
   - `.github/workflows/generator-windows-x86.yml`
   - `.github/workflows/sh-generator-windows.yml`
3. Do not copy the old project's custom overlay steps. The local `hidecm.diff` patch is already the same between the clean project and the old project.

## Do Not Directly Port

1. Any workflow step that checks out `zhenzhen122/rustdesk`.
2. Personal custom module overlays such as account panels, auth gates, device login limits, or first-install password behavior unless later made optional and source-configurable.
3. Chinese-only deployment text in backend responses unless localization is implemented systematically.

## Known UI Issues From Initial Inspection

- The page is one long form, making it hard to complete confidently.
- Save/load config is fixed in the upper-left and can visually compete with the main heading.
- Some labels are long and wrap awkwardly.
- Platform icons are decorative but not clearly tied to field relevance.
- Android-specific input is visible for non-Android platforms.
- File upload controls show browser-default Chinese text on this machine while the rest of the page is English.
- There is a JavaScript typo: `enableTerminal.disable = true` should likely be `enableTerminal.disabled = true`.
- In custom permission mode, printer/camera/terminal checkboxes are unchecked but not re-enabled in the same way as the other permissions.
