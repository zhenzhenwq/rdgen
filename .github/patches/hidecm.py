from pathlib import Path


ROOT = Path.cwd()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Could not find {label}")
    return text.replace(old, new, 1)


def uncomment_block(text: str, inner: str, label: str) -> str:
    commented = f"    /*\n{inner}    */"
    if inner in text and commented not in text:
        return text
    return replace_once(text, commented, inner, label)


def patch_settings_page() -> None:
    path = ROOT / "flutter/lib/desktop/pages/desktop_setting_page.dart"
    text = path.read_text(encoding="utf-8")
    if "hide_cm(!locked).marginOnly" in text and "//   hide_cm(!locked)" not in text:
        print("Safety settings already show hide_cm.")
        return
    old = """            // if (usePassword)
            //   hide_cm(!locked).marginOnly(left: _kContentHSubMargin - 6),
"""
    new = """            if (usePassword)
              hide_cm(!locked).marginOnly(left: _kContentHSubMargin - 6),
"""
    path.write_text(replace_once(text, old, new, "hide_cm settings toggle"), encoding="utf-8")
    print("Enabled hide_cm in safety settings.")


def patch_main() -> None:
    path = ROOT / "flutter/lib/main.dart"
    text = path.read_text(encoding="utf-8")
    if "// gFFI.serverModel.hideCm = hide;" in text:
        print("Connection manager startup already leaves model hideCm untouched.")
        return
    path.write_text(
        replace_once(
            text,
            "  gFFI.serverModel.hideCm = hide;\n",
            "  // gFFI.serverModel.hideCm = hide;\n",
            "connection manager hideCm assignment",
        ),
        encoding="utf-8",
    )
    print("Adjusted connection manager startup hideCm handling.")


def patch_server_model() -> None:
    path = ROOT / "flutter/lib/models/server_model.dart"
    text = path.read_text(encoding="utf-8")
    if "bool hideCm = false;" in text:
        text = text.replace("  bool hideCm = false;\n", "  bool _hideCm = false;\n", 1)
    if "bool get hideCm => _hideCm;" not in text:
        text = replace_once(
            text,
            "  bool get clipboardOk => _clipboardOk;\n\n",
            "  bool get clipboardOk => _clipboardOk;\n\n  bool get hideCm => _hideCm;\n\n",
            "hideCm getter insertion point",
        )

    text = uncomment_block(
        text,
        """    if (method != kUsePermanentPassword) {
      await bind.mainSetOption(
          key: 'allow-hide-cm', value: bool2option('allow-hide-cm', false));
    }
""",
        "verification method hide_cm reset block",
    )
    text = uncomment_block(
        text,
        """    if (mode != 'password') {
      await bind.mainSetOption(
          key: 'allow-hide-cm', value: bool2option('allow-hide-cm', false));
    }
""",
        "approve mode hide_cm reset block",
    )
    text = uncomment_block(
        text,
        """    // initital _hideCm at startup
    final verificationMethod =
        bind.mainGetOptionSync(key: kOptionVerificationMethod);
    final approveMode = bind.mainGetOptionSync(key: kOptionApproveMode);
    _hideCm = option2bool(
        'allow-hide-cm', bind.mainGetOptionSync(key: 'allow-hide-cm'));
    if (!(approveMode == 'password' &&
        verificationMethod == kUsePermanentPassword)) {
      _hideCm = false;
    }
""",
        "initial hide_cm block",
    )
    text = uncomment_block(
        text,
        """    var hideCm = option2bool(
        'allow-hide-cm', await bind.mainGetOption(key: 'allow-hide-cm'));
    if (!(approveMode == 'password' &&
        verificationMethod == kUsePermanentPassword)) {
      hideCm = false;
    }
""",
        "hide_cm polling block",
    )
    text = uncomment_block(
        text,
        """    if (_hideCm != hideCm) {
      _hideCm = hideCm;
      if (desktopType == DesktopType.cm) {
        if (hideCm) {
          await hideCmWindow();
        } else {
          await showCmWindow();
        }
      }
      update = true;
    }
""",
        "hide_cm update block",
    )
    path.write_text(text, encoding="utf-8")
    print("Enabled hide_cm state updates in ServerModel.")


def patch_ipc_hide_cm_gate() -> None:
    path = ROOT / "src/ipc.rs"
    text = path.read_text(encoding="utf-8")
    old = """                } else if name == "hide_cm" {
                    value = if crate::hbbs_http::sync::is_pro() || crate::common::is_custom_client()
                    {
                        Some(hbb_common::password_security::hide_cm().to_string())
                    } else {
                        None
                    };
"""
    new = """                } else if name == "hide_cm" {
                    value = Some(hbb_common::password_security::hide_cm().to_string());
"""
    if new in text:
        print("hide_cm IPC lookup already bypasses pro/custom-client gate.")
        return
    path.write_text(replace_once(text, old, new, "hide_cm IPC pro/custom-client gate"), encoding="utf-8")
    print("Allowed hide_cm IPC lookup for default app-name clients.")


def main() -> None:
    patch_settings_page()
    patch_main()
    patch_server_model()
    patch_ipc_hide_cm_gate()


if __name__ == "__main__":
    main()
