from django import forms
from django.db.models.options import Options


class SearchAndReplaceForm(forms.Form):
    search = forms.CharField(strip=False)
    replace = forms.CharField(required=False, strip=False)

    def _get_form_field_name(self, model, field):
        opts = model._meta
        assert isinstance(opts, Options)
        return "{}_{}_{}".format(opts.app_label, opts.model_name, field)

    def _get_field_label(self, model, field):
        opts = model._meta
        assert isinstance(opts, Options)
        return opts.get_field(field).verbose_name

    def get_form_fields_by_model(self):
        """
        Returns a list of (model verbose name, [form field, ...]) tuples.
        Used to render the form.
        """
        results = []
        for model, fields in self.models_and_fields:
            form_fields = []
            for field in fields:
                form_field_name = self._get_form_field_name(model, field)
                form_fields.append(self[form_field_name])
            results.append((model, form_fields))
        return results

    def get_extra_form_fields(self):
        """
        Returns all fields except search, replace and the ones returned by get_form_fields_by_model.
        """
        ignored = {"search", "replace"}.union(
            {
                self._get_form_field_name(model, field)
                for model, fields in self.models_and_fields
                for field in fields
            }
        )
        fields = []
        for field in self.fields:
            if field not in ignored:
                fields.append(self[field])
        return fields

    def get_selected_fields(self):
        """
        Returns a list of (Model, [field name, ...]) tuples that were selected by the user.
        Used by the SearchAndReplaceView to decide which models / fields to target.
        """
        results = []
        for model, fields in self.models_and_fields:
            selected = []
            for field in fields:
                form_field_name = self._get_form_field_name(model, field)
                if self.cleaned_data[form_field_name]:
                    selected.append(field)
            if selected:
                results.append((model, selected))
        return results

    def __init__(self, models_and_fields, data=None, files=None, **kwargs):
        self.models_and_fields = models_and_fields
        super().__init__(data, files, **kwargs)
        for model, fields in models_and_fields:
            for field in fields:
                form_field_name = self._get_form_field_name(model, field)
                field_label = self._get_field_label(model, field)
                self.fields[form_field_name] = forms.BooleanField(
                    required=False, label=field_label, initial=True
                )
