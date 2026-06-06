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
class BeijingCustomPayloadTests(TestCase):
    def setUp(self):
        self.created_secret_zips = []

    def tearDown(self):
        for path in self.created_secret_zips:
            if path.exists():
                path.unlink()

    def _payload(self, platform):
        return {
            "platform": platform,
            "version": "1.4.6",
            "delayFix": "on",
            "beijingCustom": "on",
            "exename": "BeijingCustomTest",
            "appname": "WuYouDesk",
            "direction": "both",
            "installation": "installationY",
            "settings": "settingsY",
            "serverIP": "10.0.0.1",
            "apiServer": "http://10.0.0.1:21114",
            "key": "test-server-key",
            "urlLink": "https://example.com",
            "downloadLink": "https://example.com/download",
            "compname": "Example Ltd",
            "theme": "system",
            "themeDorO": "default",
            "passApproveMode": "password-click",
            "permanentPassword": "",
            "permissionsDorO": "default",
            "permissionsType": "custom",
            "enableKeyboard": "on",
            "enableClipboard": "on",
            "enableFileTransfer": "on",
            "enableAudio": "on",
            "enableTCP": "on",
            "enableRemoteRestart": "on",
            "enableRecording": "on",
            "enableBlockingInput": "on",
            "enablePrinter": "on",
            "enableCamera": "on",
            "enableTerminal": "on",
        }

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
        return post_mock.call_args.args[0], inputs_raw

    def test_linux_generation_serializes_beijing_custom_when_checked(self):
        dispatch_url, inputs_raw = self._post_and_read_inputs(self._payload("linux"))

        self.assertTrue(dispatch_url.endswith("/actions/workflows/generator-linux.yml/dispatches"))
        self.assertEqual(inputs_raw["beijingCustom"], "true")

    def test_non_linux_generation_suppresses_beijing_custom(self):
        dispatch_url, inputs_raw = self._post_and_read_inputs(self._payload("windows"))

        self.assertTrue(dispatch_url.endswith("/actions/workflows/generator-windows.yml/dispatches"))
        self.assertEqual(inputs_raw["beijingCustom"], "false")
