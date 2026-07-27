from __future__ import annotations

import argparse
from pathlib import Path
from xml.dom import minidom
from xml.parsers.expat import ExpatError


UTF8_CODEPAGE = "65001"
PACKAGE_PATH = Path("res/msi/Package/Package.wxs")
LOCALIZATION_PATH = Path("res/msi/Package/Language/Package.en-us.wxl")


def _load_xml(path: Path) -> minidom.Document:
    if not path.is_file():
        raise SystemExit(f"Required MSI source file is missing: {path}")
    try:
        return minidom.parse(str(path))
    except (OSError, ExpatError) as exc:
        raise SystemExit(f"Unable to parse MSI XML file {path}: {exc}") from exc


def _single_element(
    document: minidom.Document,
    local_name: str,
    *,
    attribute: str | None = None,
    value: str | None = None,
) -> minidom.Element:
    matches = []
    for element in document.getElementsByTagName("*"):
        if element.localName != local_name:
            continue
        if attribute is not None and element.getAttribute(attribute) != value:
            continue
        matches.append(element)
    if len(matches) != 1:
        detail = f" with {attribute}={value!r}" if attribute else ""
        raise SystemExit(
            f"Expected exactly one {local_name} element{detail}, found {len(matches)}"
        )
    return matches[0]


def _write_xml(document: minidom.Document, path: Path) -> None:
    temporary_path = path.with_name(f"{path.name}.rdgen.tmp")
    try:
        temporary_path.write_bytes(document.toxml(encoding="utf-8"))
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def configure_msi_utf8(root: Path) -> bool:
    package_path = root / PACKAGE_PATH
    localization_path = root / LOCALIZATION_PATH
    package_document = _load_xml(package_path)
    localization_document = _load_xml(localization_path)

    package = _single_element(package_document, "Package")
    localization = localization_document.documentElement
    if localization.localName != "WixLocalization":
        raise SystemExit(
            "Expected Package.en-us.wxl to contain a WixLocalization root element"
        )
    summary_codepage = _single_element(
        localization_document,
        "String",
        attribute="Id",
        value="SummaryCodepage",
    )

    changes = (
        package.getAttribute("Codepage") != UTF8_CODEPAGE
        or localization.getAttribute("Codepage") != UTF8_CODEPAGE
        or summary_codepage.getAttribute("Value") != UTF8_CODEPAGE
    )
    if not changes:
        print("Windows MSI sources already use UTF-8 codepage 65001.")
        return False

    package.setAttribute("Codepage", UTF8_CODEPAGE)
    localization.setAttribute("Codepage", UTF8_CODEPAGE)
    summary_codepage.setAttribute("Value", UTF8_CODEPAGE)
    _write_xml(package_document, package_path)
    _write_xml(localization_document, localization_path)
    print("Configured Windows MSI package and localization for UTF-8 codepage 65001.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    configure_msi_utf8(args.root.resolve())


if __name__ == "__main__":
    main()
