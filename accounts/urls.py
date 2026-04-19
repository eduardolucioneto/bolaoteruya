from django.contrib.auth import views as auth_views
from django.urls import path

from accounts.views import AdminCreateUserView, LoginView, LogoutView, ProfileView, SignUpView

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("admin/create-user/", AdminCreateUserView.as_view(), name="admin_create_user"),
    path("password-change/", auth_views.PasswordChangeView.as_view(template_name="accounts/password_change.html", success_url="/accounts/password-change/done/"), name="password_change"),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"), name="password_change_done"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html", email_template_name="accounts/emails/password_reset_email.txt", subject_template_name="accounts/emails/password_reset_subject.txt", success_url="/accounts/password-reset/done/"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html", success_url="/accounts/reset/done/"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
]

