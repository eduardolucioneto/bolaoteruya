from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import path, reverse

from core.forms import GoogleImportForm
from core.google_imports import import_google_data


class GoogleImportAdminMixin:
    change_list_template = "admin/custom_tools_changelist.html"

    def get_urls(self):
        opts = self.model._meta
        custom_urls = [
            path(
                "import-google/",
                self.admin_site.admin_view(self.import_google_view),
                name=f"{opts.app_label}_{opts.model_name}_import_google",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        extra_context = extra_context or {}
        extra_context["google_import_url"] = reverse(f"admin:{opts.app_label}_{opts.model_name}_import_google")
        return super().changelist_view(request, extra_context=extra_context)

    def import_google_view(self, request):
        opts = self.model._meta
        if request.method == "POST":
            form = GoogleImportForm(request.POST)
            if form.is_valid():
                try:
                    results = import_google_data(
                        groups_url=form.cleaned_data["groups_sheet_url"],
                        matches_url=form.cleaned_data["matches_sheet_url"],
                        ranking_url=form.cleaned_data["ranking_sheet_url"],
                    )
                except ValidationError as exc:
                    form.add_error(None, exc.message)
                except Exception as exc:
                    form.add_error(None, f"Falha ao importar dados do Google: {exc}")
                else:
                    messages.success(
                        request,
                        f"Importação concluída. Grupos: {results['groups']} | Jogos: {results['matches']} | Ranking: {results['ranking']}",
                    )
                    return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))
        else:
            form = GoogleImportForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": opts,
            "title": "Importar dados do Google Sheets",
            "form": form,
        }
        return render(request, "admin/import_google_data.html", context)


class CsvExportAdminMixin:
    change_list_template = "admin/custom_tools_changelist.html"
    export_url_name = None
    export_label = "Baixar CSV"
    export_filename = "export.csv"

    def get_urls(self):
        opts = self.model._meta
        custom_urls = [
            path(
                "export-csv/",
                self.admin_site.admin_view(self.export_csv_view),
                name=self.export_url_name or f"{opts.app_label}_{opts.model_name}_export_csv",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        extra_context = extra_context or {}
        object_tool_links = list(extra_context.get("object_tool_links", []))
        object_tool_links.append(
            {
                "url": reverse(self.export_url_name or f"admin:{opts.app_label}_{opts.model_name}_export_csv"),
                "label": self.export_label,
            }
        )
        extra_context["object_tool_links"] = object_tool_links
        return super().changelist_view(request, extra_context=extra_context)

    def export_csv_view(self, request):
        queryset = self.get_export_queryset(request)
        return self.build_csv_response(queryset)

    def get_export_queryset(self, request):
        return self.get_queryset(request)

    def build_csv_response(self, queryset):
        raise NotImplementedError("Subclasses must implement build_csv_response().")
