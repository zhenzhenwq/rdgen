from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST

from .forms import ManagedSetPasswordForm, ManagedUserCreationForm, ManagedUserEditForm


User = get_user_model()


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


class PostOnlyLogoutView(LogoutView):
    http_method_names = ["post", "options"]


def _managed_user_or_403(actor, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser and not actor.is_superuser:
        raise PermissionDenied
    if user.is_staff and not actor.is_superuser and user.pk != actor.pk:
        raise PermissionDenied
    return user


@staff_required
def user_list(request):
    users = User.objects.order_by("username")
    if not request.user.is_superuser:
        users = users.filter(Q(is_staff=False) | Q(pk=request.user.pk))
    return render(request, "users/user_list.html", {"users": users})


@sensitive_post_parameters("password1", "password2")
@staff_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    if request.method == "POST":
        form = ManagedUserCreationForm(request.POST, actor=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"账号 {user.username} 已创建。")
            return redirect("users:list")
    else:
        form = ManagedUserCreationForm(actor=request.user)
    return render(
        request,
        "users/user_form.html",
        {"form": form, "page_title": "创建账号", "submit_label": "创建账号"},
    )


@staff_required
@require_http_methods(["GET", "POST"])
def user_edit(request, user_id):
    user = _managed_user_or_403(request.user, user_id)
    if request.method == "POST":
        form = ManagedUserEditForm(request.POST, instance=user, actor=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"账号 {user.username} 已更新。")
            return redirect("users:list")
    else:
        form = ManagedUserEditForm(instance=user, actor=request.user)
    return render(
        request,
        "users/user_form.html",
        {
            "form": form,
            "managed_user": user,
            "page_title": f"编辑 {user.username}",
            "submit_label": "保存更改",
        },
    )


@sensitive_post_parameters("new_password1", "new_password2")
@staff_required
@require_http_methods(["GET", "POST"])
def user_password(request, user_id):
    user = _managed_user_or_403(request.user, user_id)
    if request.method == "POST":
        form = ManagedSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            if user.pk == request.user.pk:
                update_session_auth_hash(request, user)
            messages.success(request, f"账号 {user.username} 的密码已重置。")
            return redirect("users:list")
    else:
        form = ManagedSetPasswordForm(user)
    return render(
        request,
        "users/password_form.html",
        {"form": form, "managed_user": user},
    )


@staff_required
@require_POST
def user_toggle(request, user_id):
    user = _managed_user_or_403(request.user, user_id)
    if user.pk == request.user.pk:
        messages.error(request, "不能停用当前登录账号。")
        return redirect("users:list")
    if user.is_superuser and user.is_active:
        has_another_superuser = User.objects.filter(
            is_superuser=True,
            is_active=True,
        ).exclude(pk=user.pk).exists()
        if not has_another_superuser:
            messages.error(request, "不能停用最后一个可用的超级管理员。")
            return redirect("users:list")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    state = "启用" if user.is_active else "停用"
    messages.success(request, f"账号 {user.username} 已{state}。")
    return redirect(reverse("users:list"))


@login_required
def password_changed(request):
    return render(request, "accounts/password_change_done.html")
