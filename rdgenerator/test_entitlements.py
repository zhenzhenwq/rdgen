import hashlib
import shutil
import uuid
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from .forms import ManagedUserCreationForm
from .models import (
    create_github_run_with_reservation,
    GenerationQuotaExceeded,
    GithubRun,
    UserEntitlement,
    reserve_generation,
)


class UserEntitlementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("quota-user")

    def test_time_policy_can_be_permanent_or_expired(self):
        entitlement = UserEntitlement.objects.create(user=self.user)

        self.assertFalse(entitlement.is_expired)
        self.assertFalse(reserve_generation(self.user))

        entitlement.expires_at = timezone.now() - timedelta(seconds=1)
        entitlement.save(update_fields=["expires_at"])
        with self.assertRaises(GenerationQuotaExceeded):
            reserve_generation(self.user)

    def test_count_policy_reserves_until_limit(self):
        entitlement = UserEntitlement.objects.create(
            user=self.user,
            expiration_mode="count",
            generation_limit=1,
        )

        self.assertTrue(reserve_generation(self.user))
        entitlement.refresh_from_db()
        self.assertEqual(entitlement.reserved_generations, 1)
        with self.assertRaises(GenerationQuotaExceeded):
            reserve_generation(self.user)

    def test_run_creation_failure_rolls_back_count_reservation(self):
        entitlement = UserEntitlement.objects.create(
            user=self.user,
            expiration_mode="count",
            generation_limit=1,
        )

        with patch.object(
            GithubRun.objects,
            "create",
            side_effect=RuntimeError("database write failed"),
        ):
            with self.assertRaises(RuntimeError):
                create_github_run_with_reservation(
                    self.user,
                    uuid=str(uuid.uuid4()),
                    status="starting",
                )

        entitlement.refresh_from_db()
        self.assertEqual(entitlement.reserved_generations, 0)
        self.assertFalse(GithubRun.objects.exists())

    def test_run_creation_reserves_count_and_persists_the_run_together(self):
        entitlement = UserEntitlement.objects.create(
            user=self.user,
            expiration_mode="count",
            generation_limit=1,
        )

        run = create_github_run_with_reservation(
            self.user,
            uuid=str(uuid.uuid4()),
            status="starting",
        )

        entitlement.refresh_from_db()
        self.assertTrue(run.quota_chargeable)
        self.assertTrue(run.quota_reserved)
        self.assertEqual(entitlement.reserved_generations, 1)

    def test_expiry_form_interprets_input_as_beijing_time(self):
        form = ManagedUserCreationForm(
            data={
                "username": "beijing-time-user",
                "password1": "Strong-test-password-2026",
                "password2": "Strong-test-password-2026",
                "expiration_mode": "time",
                "expires_at": "2026-07-31T12:00",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        expires_at = form.cleaned_data["expires_at"]
        self.assertEqual(expires_at.tzinfo, ZoneInfo("Asia/Shanghai"))
        self.assertEqual(expires_at.hour, 12)


class ArtifactQuotaTests(TestCase):
    def setUp(self):
        self.token = "artifact-callback-token"
        self.user = get_user_model().objects.create_user("artifact-owner")
        self.entitlement = UserEntitlement.objects.create(
            user=self.user,
            expiration_mode="count",
            generation_limit=2,
            reserved_generations=1,
        )
        self.run_uuid = str(uuid.uuid4())
        self.run = GithubRun.objects.create(
            uuid=self.run_uuid,
            status="in_progress",
            owner=self.user,
            callback_token_hash=hashlib.sha256(self.token.encode()).hexdigest(),
            download_ttl_hours=24,
            quota_chargeable=True,
            quota_reserved=True,
        )
        self.output_dir = Path("exe") / self.run_uuid

    def tearDown(self):
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def _upload(self, filename, content):
        return self.client.post(
            "/save_custom_client",
            {
                "uuid": self.run_uuid,
                "file": SimpleUploadedFile(filename, content),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

    def test_first_valid_package_counts_once_and_starts_expiry(self):
        first_upload = timezone.now()
        with patch("rdgenerator.models.timezone.now", return_value=first_upload):
            self.assertEqual(self._upload("client.exe", b"first-package").status_code, 200)

        self.assertEqual(self._upload("client.msi", b"second-package").status_code, 200)
        self.run.refresh_from_db()
        self.entitlement.refresh_from_db()

        self.assertEqual(self.entitlement.generations_used, 1)
        self.assertEqual(self.entitlement.reserved_generations, 0)
        self.assertEqual(self.run.artifact_file_count, 2)
        self.assertTrue(self.run.quota_counted)
        self.assertEqual(
            self.run.download_expires_at,
            first_upload + timedelta(hours=24),
        )
        self.assertEqual(
            self.run.artifact_expires_at,
            first_upload + timedelta(days=7),
        )

    def test_retrying_same_filename_does_not_inflate_file_count(self):
        self.assertEqual(self._upload("client.exe", b"first-attempt").status_code, 200)
        self.assertEqual(self._upload("client.exe", b"first-attempt").status_code, 200)

        self.run.refresh_from_db()
        self.entitlement.refresh_from_db()
        self.assertEqual(self.run.artifact_file_count, 1)
        self.assertEqual(self.entitlement.generations_used, 1)
        self.assertEqual(self.entitlement.reserved_generations, 0)

    def test_zero_byte_or_unknown_file_does_not_consume_quota(self):
        self.assertEqual(self._upload("empty.exe", b"").status_code, 200)
        self.assertEqual(self._upload("notes.txt", b"not-a-package").status_code, 200)

        self.run.refresh_from_db()
        self.entitlement.refresh_from_db()
        self.assertEqual(self.run.status, "in_progress")
        self.assertFalse(self.run.quota_counted)
        self.assertEqual(self.entitlement.generations_used, 0)
        self.assertEqual(self.entitlement.reserved_generations, 1)

    def test_late_package_counts_after_reservation_was_released(self):
        self.run.quota_reserved = False
        self.run.save(update_fields=["quota_reserved"])
        self.entitlement.reserved_generations = 0
        self.entitlement.save(update_fields=["reserved_generations"])

        self.assertEqual(self._upload("late-client.exe", b"late-package").status_code, 200)

        self.run.refresh_from_db()
        self.entitlement.refresh_from_db()
        self.assertTrue(self.run.quota_counted)
        self.assertEqual(self.entitlement.generations_used, 1)
        self.assertEqual(self.entitlement.reserved_generations, 0)

    def test_package_counts_when_admin_already_cleared_the_reservation(self):
        self.entitlement.expiration_mode = "time"
        self.entitlement.generation_limit = None
        self.entitlement.reserved_generations = 0
        self.entitlement.save(
            update_fields=[
                "expiration_mode",
                "generation_limit",
                "reserved_generations",
            ]
        )

        response = self._upload("mode-change-client.exe", b"package")

        self.assertEqual(response.status_code, 200)
        self.run.refresh_from_db()
        self.entitlement.refresh_from_db()
        self.assertTrue(self.run.quota_counted)
        self.assertFalse(self.run.quota_reserved)
        self.assertEqual(self.entitlement.generations_used, 1)
        self.assertEqual(self.entitlement.reserved_generations, 0)
