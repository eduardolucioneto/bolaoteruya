from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm, UserCreationForm, UserChangeForm
from django.urls import path
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from accounts.models import Profile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "is_superuser", "groups", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações pessoais", {"fields": ("first_name", "last_name", "email")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "first_name", "last_name", "password1", "password2", "is_active", "is_staff"),
            },
        ),
    )

    def get_urls(self):
        custom_urls = [
            path("<int:user_id>/reset-password/", self.admin_site.admin_view(self.reset_password_view), name="accounts_user_reset_password"),
        ]
        return custom_urls + super().get_urls()

    def reset_password_view(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if request.method == "POST":
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Senha redefinida para {user.username}.")
                return redirect("admin:accounts_user_change", user_id)
        else:
            form = AdminPasswordChangeForm(user)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "original": user,
            "title": "Redefinir senha",
        }
        return render(request, "admin/accounts/user/reset_password.html", context)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "city", "country", "timezone")
    search_fields = ("user__username", "display_name", "city", "country")
