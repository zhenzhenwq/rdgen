import hashlib
import json
import shutil
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from .models import GithubRun
from .views import STATUS_UPDATE_SALT, ZIP_DOWNLOAD_SALT


class MachineEndpointTests(TestCase):
    def setUp(self):
        self.token = "callback-token-for-tests"
        self.run_uuid = str(uuid.uuid4())
        owner = get_user_model().objects.create_user("machine-owner")
        self.run = GithubRun.objects.create(
            uuid=self.run_uuid,
            status="in_progress",
            owner=owner,
            callback_token_hash=hashlib.sha256(self.token.encode()).hexdigest(),
        )
        self.png_dir = Path("png") / self.run_uuid
        self.exe_dir = Path("exe") / self.run_uuid
        self.temp_dir = Path("temp_zips")
        self.png_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        (self.png_dir / "icon.png").write_bytes(b"png-data")
        self.created_temp_files = []

    def tearDown(self):
        shutil.rmtree(self.png_dir, ignore_errors=True)
        shutil.rmtree(self.exe_dir, ignore_errors=True)
        for path in self.created_temp_files:
            path.unlink(missing_ok=True)

    def _bearer(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.token}"}

    def test_png_requires_matching_callback_token(self):
        url = f"/get_png?filename=icon.png&uuid={self.run_uuid}"

        self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(
            self.client.get(url, **self._bearer("wrong-token")).status_code,
            401,
        )
        response = self.client.get(url, **self._bearer())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"png-data")

    def test_expired_callback_token_is_rejected(self):
        GithubRun.objects.filter(uuid=self.run_uuid).update(
            created_at=timezone.now() - timedelta(days=2)
        )

        response = self.client.get(
            f"/get_png?filename=icon.png&uuid={self.run_uuid}",
            **self._bearer(),
        )

        self.assertEqual(response.status_code, 401)

    def test_status_update_requires_matching_callback_token(self):
        payload = json.dumps({"uuid": self.run_uuid, "status": "success"})

        self.assertEqual(
            self.client.post("/updategh", payload, content_type="application/json").status_code,
            401,
        )
        response = self.client.post(
            "/updategh",
            payload,
            content_type="application/json",
            **self._bearer(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            GithubRun.objects.get(uuid=self.run_uuid).status,
            "success",
        )

    def test_status_update_accepts_task_scoped_signed_url(self):
        signature = signing.dumps(
            {"uuid": self.run_uuid},
            salt=STATUS_UPDATE_SALT,
        )

        response = self.client.post(
            f"/updategh?signature={signature}",
            json.dumps({"uuid": self.run_uuid, "status": "failure"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            GithubRun.objects.get(uuid=self.run_uuid).status,
            "failure",
        )

    def test_upload_requires_token_and_saves_only_under_run_directory(self):
        upload = SimpleUploadedFile("client.exe", b"client-data")

        self.assertEqual(
            self.client.post(
                "/save_custom_client",
                {"uuid": self.run_uuid, "file": upload},
            ).status_code,
            401,
        )
        upload = SimpleUploadedFile("client.exe", b"client-data")
        response = self.client.post(
            "/save_custom_client",
            {"uuid": self.run_uuid, "file": upload},
            **self._bearer(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual((self.exe_dir / "client.exe").read_bytes(), b"client-data")

    def test_cleanup_requires_token_and_deletes_only_matching_archive(self):
        matching = self.temp_dir / f"secrets_{self.run_uuid}_build.zip"
        unrelated = self.temp_dir / f"secrets_{uuid.uuid4()}_build.zip"
        matching.write_bytes(b"matching")
        unrelated.write_bytes(b"unrelated")
        self.created_temp_files.extend([matching, unrelated])
        payload = json.dumps({"uuid": self.run_uuid})

        response = self.client.post(
            "/cleanzip",
            payload,
            content_type="application/json",
            **self._bearer(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(matching.exists())
        self.assertTrue(unrelated.exists())

    def test_signed_zip_rejects_missing_tampered_and_expired_signatures(self):
        filename = f"secrets_{self.run_uuid}_build.zip"
        archive = self.temp_dir / filename
        archive.write_bytes(b"zip-data")
        self.created_temp_files.append(archive)
        signature = signing.dumps(
            {"filename": filename},
            salt=ZIP_DOWNLOAD_SALT,
        )

        self.assertEqual(self.client.get(f"/get_zip?filename={filename}").status_code, 403)
        self.assertEqual(
            self.client.get(
                f"/get_zip?filename=secrets_other.zip&signature={signature}"
            ).status_code,
            403,
        )
        response = self.client.get(
            f"/get_zip?filename={filename}&signature={signature}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"zip-data")

        with patch("rdgenerator.views.ZIP_DOWNLOAD_MAX_AGE", -1):
            expired = self.client.get(
                f"/get_zip?filename={filename}&signature={signature}"
            )
        self.assertEqual(expired.status_code, 403)

    @override_settings(API_SHARED_SECRET="shared-api-token")
    def test_startgh_rejects_requests_without_shared_api_token(self):
        response = self.client.post(
            "/startgh",
            json.dumps({"platform": "windows"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_machine_post_endpoints_are_csrf_exempt_after_token_auth(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/updategh",
            json.dumps({"uuid": self.run_uuid, "status": "success"}),
            content_type="application/json",
            **self._bearer(),
        )

        self.assertEqual(response.status_code, 200)
