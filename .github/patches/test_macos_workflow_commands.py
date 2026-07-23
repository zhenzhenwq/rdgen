import unittest
from pathlib import Path


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / "workflows" / "generator-macos.yml"
)


def named_step(workflow: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    if marker not in workflow:
        raise AssertionError(f"Missing workflow step: {name}")
    step = workflow.split(marker, 1)[1]
    return step.split("      - name:", 1)[0]


class MacOSWorkflowCommandTests(unittest.TestCase):
    def test_cargo_branding_is_applied_before_customization_validation(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        update_step = named_step(workflow, "Update macOS Info.plist and settings")

        replacements = (
            (
                'description = "RustDesk Remote Desktop"',
                'description = "${{ env.appname }}"',
            ),
            ('ProductName = "RustDesk"', 'ProductName = "${{ env.appname }}"'),
            (
                'FileDescription = "RustDesk Remote Desktop"',
                'FileDescription = "${{ env.appname }}"',
            ),
            (
                'OriginalFilename = "rustdesk.exe"',
                'OriginalFilename = "${{ env.appname }}.exe"',
            ),
        )
        for manifest in ("./Cargo.toml", "./libs/portable/Cargo.toml"):
            for source, target in replacements:
                with self.subTest(manifest=manifest, source=source):
                    self.assertIn(
                        f"sed -i '' -e 's|{source}|{target}|' {manifest}",
                        update_step,
                    )

        self.assertLess(
            workflow.index("      - name: Update macOS Info.plist and settings"),
            workflow.index("      - name: Validate customization"),
        )
        self.assertLess(
            workflow.index("      - name: Validate customization"),
            workflow.index("      - name: Build rustdesk"),
        )

    def test_macos_branding_and_validator_use_the_same_inputs(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        update_step = named_step(workflow, "Update macOS Info.plist and settings")
        validate_step = named_step(workflow, "Validate customization")

        self.assertIn('info["CFBundleName"] = "${{ env.appname }}"', update_step)
        self.assertIn(
            'info["CFBundleDisplayName"] = "${{ env.appname }}"',
            update_step,
        )
        self.assertIn("PRODUCT_NAME = ${{ env.appname }}", update_step)
        self.assertIn('MACOS_BUNDLE_ID="com.rdgen.${BUNDLE_SUFFIX}"', update_step)
        self.assertIn("--platform=macos", validate_step)
        self.assertIn('--app-name="${{ env.appname }}"', validate_step)
        self.assertIn('--macos-bundle-id="com.rdgen.${BUNDLE_SUFFIX}"', validate_step)

    def test_both_architectures_produce_distinct_dmg_names(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        create_step = named_step(workflow, "Create DMG")
        rename_step = named_step(workflow, "Rename rustdesk")
        upload_step = named_step(workflow, "Upload macOS DMG artifact")

        self.assertIn("x86_64-apple-darwin", workflow)
        self.assertIn("aarch64-apple-darwin", workflow)
        self.assertIn('${{ env.appname }}-${{ matrix.job.arch }}.dmg', create_step)
        self.assertIn('${{ env.filename }}-${{ matrix.job.arch }}.dmg', rename_step)
        self.assertIn("uses: actions/upload-artifact@v4", upload_step)
        self.assertIn(
            "name: ${{ env.filename }}-${{ matrix.job.arch }}-dmg",
            upload_step,
        )
        self.assertIn(
            "path: ${{ github.workspace }}/${{ env.filename }}-${{ matrix.job.arch }}.dmg",
            upload_step,
        )
        self.assertIn("retention-days: 1", upload_step)

    def test_generator_cleanup_only_calls_back_for_rdgen_tasks(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        cleanup_step = named_step(workflow, "Finalize and Cleanup zip/json")

        self.assertIn("always()", cleanup_step)
        self.assertIn("env.rdgen == 'true'", cleanup_step)
        self.assertIn("continue-on-error: true", cleanup_step)


if __name__ == "__main__":
    unittest.main()
