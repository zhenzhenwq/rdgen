from django.contrib import admin

from .models import GithubRun


@admin.register(GithubRun)
class GithubRunAdmin(admin.ModelAdmin):
    list_display = ("uuid", "owner", "status", "github_run_id", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("uuid", "status", "owner__username")
    readonly_fields = (
        "id",
        "uuid",
        "owner",
        "status",
        "github_run_id",
        "created_at",
        "callback_token_hash",
    )
