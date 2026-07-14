from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


CHAINS = {
    "windows": [
        ("allowCustom.py", []),
        ("remove_setup_server_tip.py", []),
        ("delay_fix.py", []),
        ("cycle_monitor.py", []),
        ("xoffline.py", []),
        ("remove_new_version_notif.py", []),
        ("hidecm.py", []),
        ("hide_settings_menu.py", []),
        ("hide_network_setting.py", []),
        ("runtime_features.py", ["--copy-id-password", "--manual-temporary-password", "--show-start-on-boot"]),
        ("remove_recent_sessions.py", []),
        ("force_disable_file_transfer.py", []),
        ("silent_install.py", []),
        ("incoming_compact.py", ["--width", "260", "--height", "360"]),
    ],
    "windows-x86": [
        ("allowCustom.py", []),
        ("remove_setup_server_tip.py", []),
        ("delay_fix.py", []),
        ("remove_new_version_notif.py", []),
        ("hidecm.py", []),
        ("hide_settings_menu.py", []),
        ("hide_network_setting.py", []),
        ("remove_recent_sessions.py", []),
        ("force_disable_file_transfer.py", []),
        ("silent_install.py", []),
    ],
    "linux": [
        ("allowCustom.py", ["--linux-uri-filename", "SmokeClient"]),
        ("remove_setup_server_tip.py", []),
        ("delay_fix.py", []),
        ("cycle_monitor.py", []),
        ("xoffline.py", []),
        ("hidecm.py", []),
        ("hide_settings_menu.py", []),
        ("hide_network_setting.py", []),
        ("runtime_features.py", ["--copy-id-password", "--manual-temporary-password"]),
        ("remove_recent_sessions.py", []),
        ("remove_new_version_notif.py", []),
        ("force_disable_file_transfer.py", []),
        ("incoming_compact.py", ["--width", "260", "--height", "360"]),
    ],
    "macos": [
        ("allowCustom.py", []),
        ("remove_setup_server_tip.py", []),
        ("delay_fix.py", []),
        ("cycle_monitor.py", []),
        ("xoffline.py", []),
        ("hidecm.py", []),
        ("hide_settings_menu.py", []),
        ("hide_network_setting.py", []),
        ("runtime_features.py", ["--copy-id-password", "--manual-temporary-password"]),
        ("remove_recent_sessions.py", []),
        ("remove_new_version_notif.py", []),
        ("force_disable_file_transfer.py", []),
        ("incoming_compact.py", ["--width", "260", "--height", "360"]),
    ],
    "android": [
        ("allowCustom.py", []),
        ("android_custom_config.py", []),
        ("delay_fix.py", []),
        ("xoffline.py", []),
        ("remove_new_version_notif.py", []),
        ("force_disable_file_transfer.py", []),
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=CHAINS, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--patches", type=Path, required=True)
    parser.add_argument("--passes", type=int, default=2)
    args = parser.parse_args()

    source = args.source.resolve()
    patches = args.patches.resolve()
    if not (source / "Cargo.toml").is_file():
        raise SystemExit(f"RustDesk source root is invalid: {source}")

    for pass_number in range(1, args.passes + 1):
        for script_name, script_args in CHAINS[args.platform]:
            command = [sys.executable, str(patches / script_name), *script_args]
            print(f"[{args.platform} pass {pass_number}] {script_name}", flush=True)
            subprocess.run(command, cwd=source, check=True)


if __name__ == "__main__":
    main()
