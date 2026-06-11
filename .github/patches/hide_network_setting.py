from pathlib import Path


ROOT = Path.cwd()
PATH = ROOT / "flutter/lib/desktop/pages/desktop_setting_page.dart"
NETWORK_TAB_BLOCK = """    if (!bind.isDisableSettings() &&
        bind.mainGetBuildinOption(key: kOptionHideNetworkSetting) != 'Y')
      SettingsTabKey.network,
"""


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    if NETWORK_TAB_BLOCK in text:
        PATH.write_text(text.replace(NETWORK_TAB_BLOCK, "", 1), encoding="utf-8")
        print("Removed the Network tab from desktop settings.")
        return
    if "SettingsTabKey.network" not in text:
        print("Network tab is already absent from desktop settings.")
        return
    raise SystemExit("Could not find the expected Network tab block.")


if __name__ == "__main__":
    main()
