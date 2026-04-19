from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from accounts.forms import ProfileForm, UserProfileForm
from core.models import PoolConfiguration


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"


class LogoutView(auth_views.LogoutView):
    http_method_names = ["get", "post", "options"]


class SignUpView(TemplateView):
    template_name = "accounts/signup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pool_config"] = PoolConfiguration.get_solo()
        return context

    def post(self, request, *args, **kwargs):
        messages.info(request, "O cadastro direto está desabilitado. Solicite seu acesso pelo WhatsApp.")
        return redirect("accounts:signup")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get(self, request, *args, **kwargs):
        user_form = UserProfileForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
        return render(request, self.template_name, {"user_form": user_form, "profile_form": profile_form})

    def post(self, request, *args, **kwargs):
        user_form = UserProfileForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect("accounts:profile")
        return render(request, self.template_name, {"user_form": user_form, "profile_form": profile_form})
