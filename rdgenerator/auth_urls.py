from django.contrib.auth import views as auth_views
from django.urls import path

from . import auth_views as account_views
from .forms import UsernameAuthenticationForm


app_name = "users"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=UsernameAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", account_views.PostOnlyLogoutView.as_view(), name="logout"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change_form.html",
            success_url="/password/changed/",
        ),
        name="password_change",
    ),
    path("password/changed/", account_views.password_changed, name="password_change_done"),
    path("users/", account_views.user_list, name="list"),
    path("users/create/", account_views.user_create, name="create"),
    path("users/<int:user_id>/edit/", account_views.user_edit, name="edit"),
    path("users/<int:user_id>/password/", account_views.user_password, name="password"),
    path("users/<int:user_id>/toggle/", account_views.user_toggle, name="toggle"),
]
