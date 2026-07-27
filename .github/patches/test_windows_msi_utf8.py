import tempfile
import unittest
from pathlib import Path
from xml.dom import minidom

from configure_windows_msi_utf8 import configure_msi_utf8


PACKAGE_XML = """<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <?include Includes.wxi?>
  <Package Name="Example" Scope="perMachine">
    <SummaryInformation Codepage="!(loc.SummaryCodepage)" />
  </Package>
</Wix>
"""
LOCALIZATION_XML = """<!-- localization strings -->
<WixLocalization Culture="en-us" Codepage="1252"
  xmlns="http://wixtoolset.org/schemas/v4/wxl">
  <String Id="SummaryCodepage" Value="1252" />
  <String Id="ProductLanguage" Value="1033" />
</WixLocalization>
"""


def element_by_local_name(document, local_name, **attributes):
    matches = []
    for element in document.getElementsByTagName("*"):
        if element.localName != local_name:
            continue
        if any(element.getAttribute(key) != value for key, value in attributes.items()):
            continue
        matches.append(element)
    if len(matches) != 1:
        raise AssertionError(f"Expected one {local_name}, found {len(matches)}")
    return matches[0]


class WindowsMsiUtf8Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.package_path = self.root / "res/msi/Package/Package.wxs"
        self.localization_path = (
            self.root / "res/msi/Package/Language/Package.en-us.wxl"
        )
        self.package_path.parent.mkdir(parents=True)
        self.localization_path.parent.mkdir(parents=True)
        self.package_path.write_text(PACKAGE_XML, encoding="utf-8")
        self.localization_path.write_text(LOCALIZATION_XML, encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_configures_package_and_localization_codepages(self):
        self.assertTrue(configure_msi_utf8(self.root))

        package_document = minidom.parse(str(self.package_path))
        localization_document = minidom.parse(str(self.localization_path))
        package = element_by_local_name(package_document, "Package")
        summary = element_by_local_name(
            localization_document,
            "String",
            Id="SummaryCodepage",
        )

        self.assertEqual(package.getAttribute("Codepage"), "65001")
        self.assertEqual(
            localization_document.documentElement.getAttribute("Codepage"),
            "65001",
        )
        self.assertEqual(summary.getAttribute("Value"), "65001")
        self.assertIn("<?include Includes.wxi?>", self.package_path.read_text("utf-8"))
        self.assertIn(
            "<!-- localization strings -->",
            self.localization_path.read_text("utf-8"),
        )

    def test_second_run_is_a_no_op(self):
        configure_msi_utf8(self.root)
        package_after_first_run = self.package_path.read_bytes()
        localization_after_first_run = self.localization_path.read_bytes()

        self.assertFalse(configure_msi_utf8(self.root))
        self.assertEqual(self.package_path.read_bytes(), package_after_first_run)
        self.assertEqual(
            self.localization_path.read_bytes(),
            localization_after_first_run,
        )

    def test_missing_summary_codepage_fails_without_writing_either_file(self):
        self.localization_path.write_text(
            LOCALIZATION_XML.replace(' Id="SummaryCodepage"', ' Id="Other"'),
            encoding="utf-8",
        )
        package_before = self.package_path.read_bytes()
        localization_before = self.localization_path.read_bytes()

        with self.assertRaises(SystemExit):
            configure_msi_utf8(self.root)

        self.assertEqual(self.package_path.read_bytes(), package_before)
        self.assertEqual(self.localization_path.read_bytes(), localization_before)


if __name__ == "__main__":
    unittest.main()
