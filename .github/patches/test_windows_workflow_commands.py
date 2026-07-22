import unittest
from pathlib import Path


WORKFLOW_DIR = Path(__file__).resolve().parents[1] / "workflows"
WINDOWS_WORKFLOWS = (
    "generator-windows.yml",
    "sh-generator-windows.yml",
)


def named_step(workflow: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    if marker not in workflow:
        raise AssertionError(f"Missing workflow step: {name}")
    step = workflow.split(marker, 1)[1]
    return step.split("      - name:", 1)[0]


class WindowsWorkflowCommandTests(unittest.TestCase):
    def test_update_notification_patch_uses_windows_available_downloader(self):
        for workflow_name in WINDOWS_WORKFLOWS:
            with self.subTest(workflow=workflow_name):
                workflow = (WORKFLOW_DIR / workflow_name).read_text(encoding="utf-8")
                step = named_step(workflow, "removeNewVersionNotif")

                self.assertIn("shell: pwsh", step)
                self.assertIn("Invoke-WebRequest", step)
                self.assertIn("-OutFile remove_new_version_notif.py", step)
                self.assertIn("python remove_new_version_notif.py", step)
                self.assertNotIn("wget ", step)

    def test_windows_x64_requires_and_finalizes_both_installers(self):
        for workflow_name in WINDOWS_WORKFLOWS:
            with self.subTest(workflow=workflow_name):
                workflow = (WORKFLOW_DIR / workflow_name).read_text(encoding="utf-8")
                upload_step = named_step(workflow, "send file to rdgen server")

                for step_name in (
                    "Build msi",
                    "zip exe and msi",
                    "unzip exe and msi",
                    "rename rustdesk.msi to filename.msi",
                ):
                    self.assertNotIn(
                        "continue-on-error: true",
                        named_step(workflow, step_name),
                    )
                self.assertIn('test -s "./SignOutput/${{ env.filename }}.exe"', upload_step)
                self.assertIn('test -s "./SignOutput/${{ env.filename }}.msi"', upload_step)
                self.assertEqual(upload_step.count('-F "defer_completion=true"'), 2)
                self.assertIn("/finalize_custom_client", upload_step)
                self.assertNotIn('if [[ -f "./SignOutput/${{ env.filename }}.msi" ]]', upload_step)


if __name__ == "__main__":
    unittest.main()
