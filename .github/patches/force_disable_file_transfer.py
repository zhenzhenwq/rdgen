import re
from pathlib import Path


ROOT = Path.cwd()
PATH = ROOT / "src/server/connection.rs"
PATTERN = re.compile(
    r"(?m)^(?P<indent>\s*)fn permission\(\n"
    r"(?P=indent)    enable_prefix_option: &str,\n"
    r"(?P=indent)    control_permissions: &Option<ControlPermissions>,\n"
    r"(?P=indent)\) -> bool \{\n"
)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    if "if enable_prefix_option == keys::OPTION_ENABLE_FILE_TRANSFER" in text:
        print("File transfer permission override already present.")
        return
    match = PATTERN.search(text)
    if not match:
        raise SystemExit("Could not find permission() function in src/server/connection.rs")
    indent = match.group("indent")
    insert = (
        match.group(0)
        + f"{indent}    if enable_prefix_option == keys::OPTION_ENABLE_FILE_TRANSFER {{\n"
        + f"{indent}        return false;\n"
        + f"{indent}    }}\n"
    )
    PATH.write_text(text[: match.start()] + insert + text[match.end() :], encoding="utf-8")
    print("Forced file-transfer permission checks to return false.")


if __name__ == "__main__":
    main()
