import base64
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import pyzipper
from django.conf import settings
from django.test import TestCase, override_settings


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
            "version": "1.4.7",
            "delayFix": "on",
            "beijingCustom": "on",
            "exename": "AllFeatures",
            "appname": "WuYouDesk",
            "direction": direction,
            "installation": "installationN",
            "settings": "settingsN",
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
            "removeWallpaper": "on",
            "defaultManual": "custom-option=Y",
            "overrideManual": "override-option=N",
            "cycleMonitor": "on",
            "xOffline": "on",
            "removeNewVersionNotif": "on",
            "hideSettingsMenu": "on",
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
            "copyIdPasswordButton",
            "manualTemporaryPassword",
            "showStartOnBootCheckbox",
            "incomingCompactMode",
            "forceDisableFileTransfer",
            "cycleMonitor",
            "xOffline",
            "removeNewVersionNotif",
            "hideSettingsMenu",
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
        self.assertEqual(custom_config["disable-settings"], "Y")
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
        self.assertEqual(custom_config["override-settings"]["override-option"], "N")

    def test_windows_x86_keeps_windows_options_but_skips_flutter_only_flags(self):
        _, inputs_raw, _ = self._post_and_read_inputs(
            self._feature_payload(platform="windows-x86", direction="incoming")
        )

        self.assertEqual(inputs_raw["hideNetworkSetting"], "true")
        self.assertEqual(inputs_raw["silentInstallOnDoubleClick"], "true")
        self.assertEqual(inputs_raw["copyIdPasswordButton"], "false")
        self.assertEqual(inputs_raw["manualTemporaryPassword"], "false")
        self.assertEqual(inputs_raw["showStartOnBootCheckbox"], "false")
        self.assertEqual(inputs_raw["incomingCompactMode"], "false")
        self.assertEqual(inputs_raw["beijingCustom"], "false")

    def test_android_generation_suppresses_desktop_only_flags(self):
        _, inputs_raw, custom_config = self._post_and_read_inputs(
            self._feature_payload(platform="android", direction="incoming")
        )

        expected_false_flags = [
            "hideNetworkSetting",
            "removeSetupServerTip",
            "silentInstallOnDoubleClick",
            "copyIdPasswordButton",
            "manualTemporaryPassword",
            "showStartOnBootCheckbox",
            "incomingCompactMode",
            "beijingCustom",
        ]
        for key in expected_false_flags:
            self.assertEqual(inputs_raw[key], "false", key)
        self.assertEqual(inputs_raw["forceDisableFileTransfer"], "true")
        self.assertNotIn("hide-network-setting", custom_config)

    def test_linux_generation_serializes_beijing_custom_when_checked(self):
        dispatch_url, inputs_raw, custom_config = self._post_and_read_inputs(
            self._feature_payload(platform="linux", direction="incoming")
        )

        self.assertTrue(dispatch_url.endswith("/actions/workflows/generator-linux.yml/dispatches"))
        self.assertEqual(inputs_raw["beijingCustom"], "true")
        self.assertEqual(inputs_raw["hideNetworkSetting"], "true")
        self.assertEqual(inputs_raw["removeSetupServerTip"], "true")
        self.assertEqual(inputs_raw["copyIdPasswordButton"], "true")
        self.assertEqual(inputs_raw["manualTemporaryPassword"], "true")
        self.assertEqual(inputs_raw["incomingCompactMode"], "true")
        self.assertEqual(inputs_raw["forceDisableFileTransfer"], "true")
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
            "copyIdPasswordButton",
            "manualTemporaryPassword",
            "incomingCompactMode",
            "forceDisableFileTransfer",
            "cycleMonitor",
            "xOffline",
            "removeNewVersionNotif",
            "hideSettingsMenu",
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
        self.assertEqual(custom_config, {})
