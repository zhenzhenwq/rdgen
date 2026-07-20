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


if __name__ == "__main__":
    unittest.main()
