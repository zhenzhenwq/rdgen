import unittest
from pathlib import Path


WORKFLOW_DIR = Path(__file__).resolve().parents[1] / "workflows"
SMART_WORKFLOWS = {
    "generator-windows.yml": (
        "Stage smart multi-relay patch bundle",
        "Restore bridge files",
    ),
    "generator-windows-x86.yml": (
        "Stage smart multi-relay patch bundle",
        "Install ImageMagick on Windows",
    ),
    "generator-linux.yml": (
        "Stage smart multi-relay patch bundle",
        "Set Swap Space",
    ),
    "generator-android.yml": (
        "Stage customization patches",
        "Install flutter",
    ),
}


def named_step(workflow: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    if marker not in workflow:
        raise AssertionError(f"Missing workflow step: {name}")
    step = workflow.split(marker, 1)[1]
    return step.split("      - name:", 1)[0]


class SmartMultiRelayWorkflowTests(unittest.TestCase):
    def test_lifecycle_invalidation_reuses_the_generated_bridge_contract(self):
        root_patch = (
            Path(__file__).resolve().parent / "smart_multi_relay_149_root.diff"
        ).read_text(encoding="utf-8")
        self.assertIn("unawaited(bind.mainCheckConnectStatus());", root_patch)
        self.assertIn(
            "failed to invalidate smart relay network state: {error}",
            root_patch,
        )
        self.assertNotIn("mainNotifyNetworkChanged", root_patch)

    def test_supported_workflows_apply_only_the_locked_true_path(self):
        for workflow_name, (stage_name, first_following_step) in SMART_WORKFLOWS.items():
            with self.subTest(workflow=workflow_name):
                workflow = (WORKFLOW_DIR / workflow_name).read_text(encoding="utf-8")
                stage = named_step(workflow, stage_name)
                apply = named_step(workflow, "Apply locked smart multi-relay patch")

                if stage_name == "Stage smart multi-relay patch bundle":
                    self.assertIn("env.smartMultiRelay == 'true'", stage)
                self.assertIn("env.smartMultiRelay == 'true'", apply)
                self.assertIn("apply_smart_multi_relay_149.py", apply)
                self.assertIn("--enabled true", apply)
                self.assertIn("--source .", apply)
                self.assertIn("--patches", apply)
                self.assertNotIn("continue-on-error", apply)

                stage_index = workflow.index(f"      - name: {stage_name}")
                apply_index = workflow.index(
                    "      - name: Apply locked smart multi-relay patch"
                )
                checkout_indices = []
                offset = 0
                checkout_marker = "      - name: Checkout source code"
                while True:
                    index = workflow.find(checkout_marker, offset)
                    if index < 0:
                        break
                    checkout_indices.append(index)
                    offset = index + len(checkout_marker)
                checkouts_before_apply = [
                    index for index in checkout_indices if index < apply_index
                ]
                self.assertGreaterEqual(len(checkouts_before_apply), 2)
                self.assertLess(stage_index, min(checkouts_before_apply))
                self.assertLess(
                    apply_index,
                    workflow.index(f"      - name: {first_following_step}"),
                )

    def test_smart_patch_bundle_is_complete_and_macos_is_excluded(self):
        patches = Path(__file__).resolve().parent
        for name in (
            "apply_smart_multi_relay_149.py",
            "smart_multi_relay_149_root.diff",
            "smart_multi_relay_149_hbb_common.diff",
        ):
            self.assertTrue((patches / name).is_file(), name)

        macos = (WORKFLOW_DIR / "generator-macos.yml").read_text(encoding="utf-8")
        self.assertNotIn("smartMultiRelay", macos)
        self.assertNotIn("apply_smart_multi_relay_149.py", macos)

    def test_release_validation_uses_private_actions_artifacts(self):
        fetch = (WORKFLOW_DIR / "fetch-encrypted-secrets.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Download prepared release inputs", fetch)
        self.assertIn("source == 'actions-artifact'", fetch)
        self.assertIn("run-id: ${{ fromJSON(inputs.zip_url_json).run_id }}", fetch)
        self.assertIn("github-token: ${{ github.token }}", fetch)
        self.assertIn("source != 'actions-artifact'", fetch)

        release = (WORKFLOW_DIR / "smart-release-validation.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("actions: write", release)
        self.assertIn('"allow-websocket": "Y"', release)
        self.assertIn('"allow-insecure-tls-fallback": "N"', release)
        self.assertIn('"smartMultiRelay": "true"', release)
        self.assertIn('"rdgen": "validation"', release)
        self.assertIn('"source": "actions-artifact"', release)
        for workflow_name in SMART_WORKFLOWS:
            self.assertIn(f'"{workflow_name}"', release)

    def test_release_validation_never_calls_generator_cleanup(self):
        for workflow_name in SMART_WORKFLOWS:
            with self.subTest(workflow=workflow_name):
                workflow = (WORKFLOW_DIR / workflow_name).read_text(encoding="utf-8")
                cleanup_count = workflow.count("Finalize and Cleanup zip/json")
                self.assertGreaterEqual(cleanup_count, 1)
                self.assertEqual(
                    workflow.count("always() && env.rdgen != 'validation'"),
                    cleanup_count,
                )


if __name__ == "__main__":
    unittest.main()
