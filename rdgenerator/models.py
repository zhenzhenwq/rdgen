from django.conf import settings
from django.db import models


class GithubRun(models.Model):
    id = models.IntegerField(verbose_name="ID", primary_key=True)
    uuid = models.CharField(verbose_name="uuid", max_length=100)
    status = models.CharField(verbose_name="status", max_length=100)
    github_run_id = models.BigIntegerField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="github_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    callback_token_hash = models.CharField(max_length=64, blank=True, default="")
