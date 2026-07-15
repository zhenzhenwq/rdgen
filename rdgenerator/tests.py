import base64
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import pyzipper
from django.conf import settings
from django.test import TestCase, override_settings

from .forms import GenerateForm


@override_settings(
    GHUSER="test-owner",
    REPONAME="test-repo",
    GHBRANCH="master",
    GENURL="http://generator.example",
    PROTOCOL="http",
    ZIP_PASSWORD="test-zip-password",
)
class GeneratorFeaturePayloadTests(TestCase):
    def setUp(self):
        self.created_secret_zips = []

    def tearDown(self):
        for path in self.created_secret_zips:
            if path.exists():
                path.unlink()

    def _feature_payload(self, platform="windows", direction="incoming"):
        data = {
            "platform": platform,
            "version": "1.4.9",
            "formSchemaVersion": "2",
            "delayFix": "on",
            "beijingCustom": "on",
            "exename": "AllFeatures",
            "appname": "WuYouDesk",
            "direction": direction,
            "installation": "installationN",
            "settings": "settingsY",
            "hideNetworkSetting": "on",
            "defaultViewStyle": "adaptive",
            "removeSetupServerTip": "on",
            "silentInstallOnDoubleClick": "on",
            "copyIdPasswordButton": "on",
            "manualTemporaryPassword": "on",
            "showStartOnBootCheckbox": "on",
            "incomingCompactMode": "on",
            "incomingContentWidth": "260",
            "incomingContentHeight": "360",
            "androidappid": "com.example.wuyoudesk",
            "serverIP": "10.0.0.1",
            "apiServer": "",
            "key": "test-server-key",
            "urlLink": "https://example.com",
            "downloadLink": "https://example.com/download",
            "compname": "Example Ltd",
            "theme": "system",
            "themeDorO": "default",
            "passApproveMode": "password-click",
            "permanentPassword": "fixed-password",
            "denyLan": "on",
            "enableDirectIP": "on",
            "autoClose": "on",
            "permissionsDorO": "default",
            "permissionsType": "custom",
            "enableKeyboard": "on",
            "enableClipboard": "on",
            "enableFileCopyPaste": "on",
            "enableFileTransfer": "on",
            "forceDisableFileTransfer": "on",
            "enableAudio": "on",
            "enableTCP": "on",
            "enableRemoteRestart": "on",
            "enableRecording": "on",
            "enableBlockingInput": "on",
            "enableRemoteModi": "on",
            "enablePrinter": "on",
            "enableCamera": "on",
            "enableTerminal": "on",
            "hidecm": "on",
            "hidecmDefaultEnabled": "on",
            "removeWallpaper": "on",
            "defaultManual": "custom-option=Y",
            "overrideManual": "override-option=N",
            "cycleMonitor": "on",
            "xOffline": "on",
            "removeNewVersionNotif": "on",
            "hideSettingsMenu": "on",
            "removeRecentSessions": "on",
        }
        return data

    def _post_and_read_inputs(self, data):
        counter = iter(range(1, 20))

        def fake_uuid4():
            return UUID(int=next(counter))

        github_response = SimpleNamespace(status_code=204, content=b"", text="")
        with (
            patch("rdgenerator.views.uuid.uuid4", side_effect=fake_uuid4),
            patch("rdgenerator.views.requests.post", return_value=github_response) as post_mock,
            patch("rdgenerator.views.save_png", side_effect=ValueError("no image in test")),
        ):
            response = self.client.post("/generator", data=data)

        self.assertEqual(response.status_code, 200)
        post_payload = post_mock.call_args.kwargs["json"]
        zip_url = json.loads(post_payload["inputs"]["zip_url"])
        zip_path = Path("temp_zips") / zip_url["file"]
        self.created_secret_zips.append(zip_path)
        with pyzipper.AESZipFile(zip_path) as zf:
            zf.setpassword(settings.ZIP_PASSWORD.encode())
            inputs_raw = json.loads(zf.read("secrets.json").decode("utf-8"))
        custom_config = json.loads(base64.b64decode(inputs_raw["custom"]).decode("ascii"))
        return post_mock.call_args.args[0], inputs_raw, custom_config

    def test_windows_all_features_are_serialized_for_generation(self):
        dispatch_url, inputs_raw, custom_config = self._post_and_read_inputs(
            self._feature_payload(platform="windows", direction="incoming")
        )

        self.assertTrue(dispatch_url.endswith("/actions/workflows/generator-windows.yml/dispatches"))
        expected_true_flags = [
            "delayFix",
            "hideNetworkSetting",
            "removeSetupServerTip",
            "silentInstallOnDoubleClick",
            "hidecm",
            "hidecmDefaultEnabled",
            "copyIdPasswordButton",
            "manualTemporaryPassword",
            "showStartOnBootCheckbox",
            "incomingCompactMode",
            "forceDisableFileTransfer",
            "cycleMonitor",
            "xOffline",
            "removeNewVersionNotif",
            "hideSettingsMenu",
            "removeRecentSessions",
        ]
        for key in expected_true_flags:
            self.assertEqual(inputs_raw[key], "true", key)
        self.assertEqual(inputs_raw["direction"], "incoming")
        self.assertEqual(inputs_raw["beijingCustom"], "false")
        self.assertEqual(inputs_raw["incomingContentWidth"], "260")
        self.assertEqual(inputs_raw["incomingContentHeight"], "360")
        self.assertEqual(inputs_raw["apiServer"], "http://10.0.0.1:21114")

        self.assertEqual(custom_config["conn-type"], "incoming")
        self.assertEqual(custom_config["disable-installation"], "Y")
        self.assertNotIn("disable-settings", custom_config)
        self.assertEqual(custom_config["hide-network-setting"], "Y")
        self.assertEqual(custom_config["custom-rendezvous-server"], "10.0.0.1")
        self.assertEqual(custom_config["relay-server"], "10.0.0.1")
        self.assertEqual(custom_config["api-server"], "http://10.0.0.1:21114")
        self.assertEqual(custom_config["key"], "test-server-key")
        self.assertEqual(custom_config["password"], "fixed-password")

        default_settings = custom_config["default-settings"]
        self.assertEqual(default_settings["view-style"], "adaptive")
        self.assertEqual(default_settings["enable-file-copy-paste"], "Y")
        self.assertEqual(default_settings["enable-file-transfer"], "N")
        self.assertEqual(default_settings["approve-mode"], "password")
        self.assertEqual(default_settings["verification-method"], "use-permanent-password")
        self.assertEqual(default_settings["allow-hide-cm"], "Y")
        self.assertEqual(default_settings["allow-remote-config-modification"], "Y")
        self.assertEqual(default_settings["direct-server"], "Y")
        self.assertEqual(default_settings["custom-option"], "Y")
        override_settings = custom_config["override-settings"]
        self.assertNotIn("approve-mode", override_settings)
        self.assertNotIn("verification-method", override_settings)
        self.assertNotIn("allow-hide-cm", override_settings)
        self.assertEqual(override_settings["override-option"], "N")

    def test_hide_connection_window_capability_starts_disabled_without_password(self):
        data = self._feature_payload(platform="windows")
        data["hidecmDefaultEnabled"] = ""
        data["permanentPassword"] = ""
        data["permissionsDorO"] = "override"
        data["settings"] = "settingsY"
        data["overrideManual"] = "\n".join([
            "approve-mode=click",
            "verification-method=use-permanent-password",
            "allow-hide-cm=Y",
        ])

        _, inputs_raw, custom_config = self._post_and_read_inputs(data)

        self.assertEqual(inputs_raw["hidecm"], "true")
        self.assertEqual(inputs_raw["hidecmDefaultEnabled"], "false")
        self.assertNotIn("password", custom_config)
        self.assertEqual(
            custom_config["default-settings"]["approve-mode"],
            "password-click",
        )
        self.assertEqual(
            custom_config["default-settings"]["verification-method"],
            "use-both-passwords",
        )
        self.assertEqual(
            custom_config["default-settings"]["allow-hide-cm"],
            "N",
        )
        self.assertNotIn("approve-mode", custom_config["override-settings"])
        self.assertNotIn("verification-method", custom_config["override-settings"])
        self.assertNotIn("allow-hide-cm", custom_config["override-settings"])

    def test_default_hidden_connection_window_remains_user_configurable(self):
        data = self._feature_payload(platform="windows")
        data["permissionsDorO"] = "override"
        data["overrideManual"] = "\n".join([
            "approve-mode=click",
            "verification-method=use-both-passwords",
            "allow-hide-cm=N",
        ])

        _, _, custom_config = self._post_and_read_inputs(data)

        self.assertEqual(
            custom_config["default-settings"]["approve-mode"],
            "password",
        )
        self.assertEqual(
            custom_config["default-settings"]["verification-method"],
            "use-permanent-password",
        )
        self.assertEqual(
            custom_config["default-settings"]["allow-hide-cm"],
            "Y",
        )
        self.assertNotIn("approve-mode", custom_config["override-settings"])
        self.assertNotIn("verification-method", custom_config["override-settings"])
        self.assertNotIn("allow-hide-cm", custom_config["override-settings"])

    def test_legacy_hide_connection_window_post_keeps_default_enabled(self):
        data = self._feature_payload(platform="windows")
        data.pop("formSchemaVersion")
        data.pop("hidecmDefaultEnabled")
        data["settings"] = "settingsN"

        _, inputs_raw, custom_config = self._post_and_read_inputs(data)

        self.assertEqual(inputs_raw["hidecm"], "true")
        self.assertEqual(inputs_raw["hidecmDefaultEnabled"], "true")
        self.assertEqual(custom_config["disable-settings"], "Y")
        self.assertEqual(
            custom_config["default-settings"]["allow-hide-cm"],
            "Y",
        )

    def test_company_name_is_sed_escaped_in_workflow_input(self):
        data = self._feature_payload(platform="windows")
        data["compname"] = "Research & Development"
        _, inputs_raw, _ = self._post_and_read_inputs(data)
        self.assertEqual(inputs_raw["compname"], r"Research \& Development")

    def test_windows_x86_keeps_windows_options_but_skips_flutter_only_flags(self):
        data = self._feature_payload(platform="windows-x86", direction="incoming")
        data["cycleMonitor"] = ""
        data["xOffline"] = ""
        data["copyIdPasswordButton"] = ""
        data["manualTemporaryPassword"] = ""
        data["showStartOnBootCheckbox"] = ""
        data["incomingCompactMode"] = ""
        _, inputs_raw, _ = self._post_and_read_inputs(
            data
        )

        self.assertEqual(inputs_raw["hideNetworkSetting"], "true")
        self.assertEqual(inputs_raw["silentInstallOnDoubleClick"], "true")
        self.assertEqual(inputs_raw["copyIdPasswordButton"], "false")
        self.assertEqual(inputs_raw["manualTemporaryPassword"], "false")
        self.assertEqual(inputs_raw["showStartOnBootCheckbox"], "false")
        self.assertEqual(inputs_raw["incomingCompactMode"], "false")
        self.assertEqual(inputs_raw["removeRecentSessions"], "true")
        self.assertEqual(inputs_raw["beijingCustom"], "false")

    def test_android_generation_suppresses_desktop_only_flags(self):
        data = self._feature_payload(platform="android", direction="incoming")
        data["hideSettingsMenu"] = ""
        _, inputs_raw, custom_config = self._post_and_read_inputs(
            data
        )

        expected_false_flags = [
            "hideNetworkSetting",
            "removeSetupServerTip",
            "silentInstallOnDoubleClick",
            "copyIdPasswordButton",
            "manualTemporaryPassword",
            "showStartOnBootCheckbox",
            "incomingCompactMode",
            "removeRecentSessions",
            "beijingCustom",
            "hidecm",
            "hidecmDefaultEnabled",
            "hideSettingsMenu",
        ]
        for key in expected_false_flags:
            self.assertEqual(inputs_raw[key], "false", key)
        self.assertEqual(inputs_raw["forceDisableFileTransfer"], "true")
        self.assertEqual(inputs_raw["xOffline"], "true")
        self.assertNotIn("hide-network-setting", custom_config)

    def test_linux_generation_serializes_beijing_custom_when_checked(self):
        dispatch_url, inputs_raw, custom_config = self._post_and_read_inputs(
            self._feature_payload(platform="linux", direction="incoming")
        )

        self.assertTrue(dispatch_url.endswith("/actions/workflows/generator-linux.yml/dispatches"))
        self.assertEqual(inputs_raw["beijingCustom"], "true")
        self.assertEqual(inputs_raw["hideNetworkSetting"], "true")
        self.assertEqual(inputs_raw["removeSetupServerTip"], "true")
        self.assertEqual(inputs_raw["hidecm"], "true")
        self.assertEqual(inputs_raw["copyIdPasswordButton"], "true")
        self.assertEqual(inputs_raw["manualTemporaryPassword"], "true")
        self.assertEqual(inputs_raw["incomingCompactMode"], "true")
        self.assertEqual(inputs_raw["forceDisableFileTransfer"], "true")
        self.assertEqual(inputs_raw["removeRecentSessions"], "true")
        self.assertEqual(custom_config["hide-network-setting"], "Y")
        self.assertEqual(custom_config["default-settings"]["view-style"], "adaptive")
        self.assertEqual(custom_config["default-settings"]["enable-file-transfer"], "N")

    def test_linux_generation_without_beijing_custom_suppresses_linux_custom_features(self):
        data = self._feature_payload(platform="linux", direction="incoming")
        data.pop("beijingCustom")
        dispatch_url, inputs_raw, custom_config = self._post_and_read_inputs(data)

        self.assertTrue(dispatch_url.endswith("/actions/workflows/generator-linux.yml/dispatches"))
        expected_false_flags = [
            "beijingCustom",
            "delayFix",
            "hideNetworkSetting",
            "removeSetupServerTip",
            "hidecm",
            "hidecmDefaultEnabled",
            "copyIdPasswordButton",
            "manualTemporaryPassword",
            "incomingCompactMode",
            "forceDisableFileTransfer",
            "cycleMonitor",
            "xOffline",
            "removeNewVersionNotif",
            "hideSettingsMenu",
            "removeRecentSessions",
        ]
        for key in expected_false_flags:
            self.assertEqual(inputs_raw[key], "false", key)
        self.assertEqual(inputs_raw["direction"], "both")
        self.assertEqual(inputs_raw["server"], "rs-ny.rustdesk.com")
        self.assertEqual(inputs_raw["apiServer"], "http://rs-ny.rustdesk.com:21114")
        self.assertEqual(inputs_raw["key"], "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=")
        self.assertEqual(inputs_raw["appname"], "rustdesk")
        self.assertEqual(inputs_raw["filename"], "rustdesk")
        self.assertEqual(inputs_raw["iconlink_url"], "false")
        self.assertEqual(inputs_raw["logolink_url"], "false")
        self.assertEqual(inputs_raw["privacylink_url"], "false")

    def test_default_version_is_1_4_9(self):
        self.assertEqual(GenerateForm().fields["version"].initial, "1.4.9")

    def test_hide_connection_window_capability_allows_empty_permanent_password(self):
        data = self._feature_payload()
        data["hidecmDefaultEnabled"] = ""
        data["permanentPassword"] = ""
        data["settings"] = "settingsY"
        form = GenerateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_new_form_missing_default_checkbox_means_default_disabled(self):
        data = self._feature_payload()
        data.pop("hidecmDefaultEnabled")
        data["permanentPassword"] = ""
        form = GenerateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["hidecmDefaultEnabled"])

    def test_unknown_form_schema_does_not_use_legacy_hide_defaults(self):
        data = self._feature_payload()
        data["formSchemaVersion"] = "3"
        data.pop("hidecmDefaultEnabled")
        data["settings"] = "settingsN"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("settings", form.errors)
        self.assertFalse(form.cleaned_data["hidecmDefaultEnabled"])

    def test_hide_connection_window_capability_requires_settings_access(self):
        data = self._feature_payload()
        data["hidecmDefaultEnabled"] = ""
        data["settings"] = "settingsN"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("settings", form.errors)

    def test_default_hidden_connection_window_requires_permanent_password(self):
        data = self._feature_payload()
        data["permanentPassword"] = ""
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("permanentPassword", form.errors)

    def test_default_hidden_connection_window_requires_settings_access(self):
        data = self._feature_payload()
        data["settings"] = "settingsN"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("settings", form.errors)

    def test_default_hidden_connection_window_requires_capability(self):
        data = self._feature_payload()
        data["hidecm"] = ""
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("hidecmDefaultEnabled", form.errors)

    def test_manual_settings_allow_blank_lines_and_equals_in_value(self):
        data = self._feature_payload()
        data["hidecm"] = ""
        data["hidecmDefaultEnabled"] = ""
        data["defaultManual"] = "\ntoken=part=two\n"
        data["overrideManual"] = ""
        form = GenerateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_manual_setting_is_a_form_error(self):
        data = self._feature_payload()
        data["hidecm"] = ""
        data["hidecmDefaultEnabled"] = ""
        data["defaultManual"] = "missing-separator"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("defaultManual", form.errors)

    def test_android_rejects_logo(self):
        data = self._feature_payload(platform="android")
        data["hidecm"] = ""
        data["hidecmDefaultEnabled"] = ""
        data["logobase64"] = "data:image/png;base64,AA=="
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("logofile", form.errors)

    def test_privacy_image_is_windows_64_only(self):
        data = self._feature_payload(platform="macos")
        data["hidecm"] = ""
        data["hidecmDefaultEnabled"] = ""
        data["privacybase64"] = "data:image/png;base64,AA=="
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("privacyfile", form.errors)

    def test_windows_x86_rejects_flutter_only_options(self):
        data = self._feature_payload(platform="windows-x86")
        data["hidecm"] = ""
        data["hidecmDefaultEnabled"] = ""
        data["cycleMonitor"] = "on"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("cycleMonitor", form.errors)

    def test_android_rejects_desktop_settings_menu_option(self):
        data = self._feature_payload(platform="android")
        data["hidecm"] = ""
        data["hidecmDefaultEnabled"] = ""
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("hideSettingsMenu", form.errors)

    def test_version_gated_features_reject_unsupported_versions(self):
        requirements = {
            "incomingCompactMode": "1.4.1",
            "hideNetworkSetting": "1.4.3",
            "hideSettingsMenu": "1.4.3",
            "forceDisableFileTransfer": "1.4.4",
        }
        gated_fields = list(requirements)
        for field, version in requirements.items():
            with self.subTest(field=field, version=version):
                data = self._feature_payload()
                for gated_field in gated_fields:
                    data[gated_field] = ""
                data["version"] = version
                data[field] = "on"
                form = GenerateForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_master_allows_version_gated_features(self):
        data = self._feature_payload()
        data["version"] = "master"
        form = GenerateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_compact_dimensions_are_optional_when_feature_is_disabled(self):
        data = self._feature_payload()
        data["incomingCompactMode"] = ""
        data.pop("incomingContentWidth")
        data.pop("incomingContentHeight")
        form = GenerateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_build_script_metacharacters(self):
        data = self._feature_payload()
        data["exename"] = "client;touch-pwned"
        data["serverIP"] = "server.example.com'"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("exename", form.errors)
        self.assertIn("serverIP", form.errors)

    def test_rejects_nonportable_build_names(self):
        invalid_names = (
            ("exename", "CON"),
            ("appname", "NUL.txt"),
            ("appname", "Client?"),
            ("appname", "Client."),
            ("appname", "-Client"),
        )
        for field, value in invalid_names:
            with self.subTest(field=field, value=value):
                data = self._feature_payload()
                data[field] = value
                form = GenerateForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_rejects_build_names_that_exceed_filesystem_limits(self):
        invalid_names = (
            ("exename", "a" * 65),
            ("appname", "\U0001F600" * 51),
        )
        for field, value in invalid_names:
            with self.subTest(field=field):
                data = self._feature_payload()
                data[field] = value
                form = GenerateForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_linux_package_name_requires_at_least_two_characters(self):
        data = self._feature_payload(platform="linux")
        data["exename"] = "A"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("exename", form.errors)

    def test_beijing_linux_rejects_unverified_versions(self):
        for version in ("1.4.6", "master"):
            with self.subTest(version=version):
                data = self._feature_payload(platform="linux")
                data["version"] = version
                form = GenerateForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn("beijingCustom", form.errors)

    def test_single_character_name_remains_valid_for_windows(self):
        data = self._feature_payload(platform="windows")
        data["exename"] = "A"
        form = GenerateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_linux_package_metadata_rejects_shell_substitution(self):
        data = self._feature_payload(platform="linux")
        data["appname"] = "$(touch unsafe)"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("appname", form.errors)

    def test_linux_package_metadata_rejects_rpm_macros(self):
        invalid_values = {
            "appname": "Client%(printf unsafe)",
            "compname": "Company%{lua:unsafe}",
            "urlLink": "https://example.com/%{unsafe}",
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field):
                data = self._feature_payload(platform="linux")
                data[field] = value
                form = GenerateForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_linux_rpm_url_rejects_whitespace(self):
        data = self._feature_payload(platform="linux")
        data["urlLink"] = "https://example.com/a b"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("urlLink", form.errors)

    def test_percent_encoded_url_is_allowed_without_linux_rpm_customization(self):
        data = self._feature_payload(platform="linux")
        data["beijingCustom"] = ""
        data["urlLink"] = "https://example.com/a%20b"
        form = GenerateForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_invalid_android_app_id(self):
        data = self._feature_payload(platform="android")
        data["hidecm"] = ""
        data["hidecmDefaultEnabled"] = ""
        data["hideSettingsMenu"] = ""
        data["androidappid"] = "invalid-app-id"
        form = GenerateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("androidappid", form.errors)

    def test_rejects_non_absolute_http_urls(self):
        invalid_values = {
            "apiServer": "api.example.com",
            "urlLink": "not-a-url",
            "downloadLink": "ftp://example.com/client",
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field):
                data = self._feature_payload()
                data[field] = value
                form = GenerateForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)
