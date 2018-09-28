import uuid

from django.contrib import messages
from django.core.cache import cache
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from .forms import SearchAndReplaceForm


class SearchAndReplaceView(TemplateView):
    template_name = "search_and_replace/search_and_replace.html"
    form_class = SearchAndReplaceForm
    models_and_fields = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Search and replace")
        context["form"] = self.form
        return context

    def get_form(self, request):
        return self.form_class(
            self.models_and_fields, data=request.POST if request.POST else None
        )

    def get(self, request, *args, **kwargs):
        self.form = self.get_form(request)
        return super().get(request, *args, **kwargs)

    def is_double_submit(self):
        preview_id = self.request.POST.get("preview_id")
        if not preview_id:
            return True

        cache_key = "search-replace-{}".format(preview_id)
        if cache.get(cache_key):
            return True
        else:
            cache.set(cache_key, "done")
            return False

    def post(self, request, *args, **kwargs):
        self.form = self.get_form(request)
        if self.form.is_valid():
            if "apply" in request.POST and not self.is_double_submit():
                return self.form_valid(preview=False)
            else:
                return self.form_valid(preview=True)
        return self.render_to_response(self.get_context_data())

    def get_query_set(self, model):
        return model._default_manager.all()

    def filter_qs(self, search, model, fields):
        assert fields
        qs = self.get_query_set(model)
        filter = Q()
        for field in fields:
            filter |= Q(**{"{}__contains".format(field): search})
        return qs.filter(filter)

    def apply_search_and_replace(self, search, replace, model, fields, preview):
        qs = self.filter_qs(search, model, fields)
        results = []
        for instance in qs:
            changed_fields = []
            for field in fields:
                value = getattr(instance, field)

                # support for markup fields
                if hasattr(value, "raw"):
                    value = value.raw

                if search in value:
                    new_value = value.replace(search, replace)
                    setattr(instance, field, new_value)
                    changed_fields.append((field, value, new_value))
            results.append((instance, changed_fields))
            if not preview:
                instance.save()
        return results

    def get_results(self, search, replace, preview=True):
        results = []
        for model, selected_fields in self.form.get_selected_fields():
            result = self.apply_search_and_replace(
                search, replace, model, selected_fields, preview=preview
            )
            if result:
                results.append((model, result))
        return results

    def form_valid(self, preview=True):
        search = self.form.cleaned_data["search"]
        replace = self.form.cleaned_data["replace"]

        results = self.get_results(search, replace, preview=preview)
        num_results = sum(len(instances) for model, instances in results)

        if preview:
            return self.response_preview(search, replace, results, num_results)
        else:
            return self.response_success(search, replace, results, num_results)

    def response_preview(self, search, replace, results, num_results):
        return self.render_to_response(
            self.get_context_data(
                results=results,
                num_results=num_results,
                search=search,
                replace=replace,
                preview_id=str(uuid.uuid4()),
            )
        )

    def response_success(self, search, replace, results, num_results):
        messages.success(
            self.request,
            _("Replaced {} with {} in {} instances").format(
                search, replace, num_results
            ),
        )
        return HttpResponseRedirect(".")
