from django import forms
from django.contrib import admin
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import path
from django.db import models
from django.test import TestCase, RequestFactory

from search_and_replace.forms import SearchAndReplaceForm
from search_and_replace.views import SearchAndReplaceView


urlpatterns = [path("admin/", admin.site.urls)]  # noqa, used for runtests.py


class Cat(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(verbose_name="Biography")

    def __str__(self):
        return self.name


class Dog(models.Model):
    name = models.CharField(max_length=255)
    bark = models.TextField(verbose_name="Bark")

    def __str__(self):
        return self.name


class SearchAndReplaceFormTest(TestCase):
    def setUp(self):
        self.models_and_fields = [(Cat, ("name", "bio")), (Dog, ("name", "bark"))]
        self.form = SearchAndReplaceForm(self.models_and_fields)

    def test_form_field_name(self):
        self.assertEqual(
            self.form._get_form_field_name(Cat, "name"), "search_and_replace_cat_name"
        )

    def test_form_field_label(self):
        self.assertEqual(self.form._get_field_label(Cat, "bio"), "Biography")

    def test_get_form_fields_by_model(self):
        (cat, cat_fields), (dog, dog_fields) = self.form.get_form_fields_by_model()
        self.assertEqual(cat, Cat)
        self.assertEqual(dog, Dog)

        self.assertEqual(cat_fields[0].name, "search_and_replace_cat_name")
        self.assertEqual(cat_fields[1].name, "search_and_replace_cat_bio")

        self.assertEqual(dog_fields[0].name, "search_and_replace_dog_name")
        self.assertEqual(dog_fields[1].name, "search_and_replace_dog_bark")

    def test_get_extra_form_fields_is_empty_by_default(self):
        self.assertEqual(self.form.get_extra_form_fields(), [])

    def test_get_extra_form_fields_has_additional_fields(self):
        class ExtendedForm(SearchAndReplaceForm):
            extra_1 = forms.CharField()
            extra_2 = forms.CharField()

        first, second = ExtendedForm(self.models_and_fields).get_extra_form_fields()
        self.assertEqual(first.name, "extra_1")
        self.assertEqual(second.name, "extra_2")

    def test_get_selected_fields(self):
        form = SearchAndReplaceForm(
            self.models_and_fields,
            data={
                "search": "term",
                "search_and_replace_dog_bark": True,
                "search_and_replace_dog_name": False,
                "search_and_replace_cat_name": True,
                "wrong_name": True,
            },
        )
        assert form.is_valid()

        selected = form.get_selected_fields()
        self.assertEqual(selected, [(Cat, ["name"]), (Dog, ["bark"])])


class SearchAndReplaceViewTest(TestCase):
    def setUp(self):
        self.models_and_fields = [(Cat, ("name", "bio")), (Dog, ("name", "bark"))]

        self.lucy = Cat.objects.create(name="Lucy", bio="Grew up in the deep south.")
        self.peter = Cat.objects.create(name="Peter", bio="Child of the north.")
        self.momo = Cat.objects.create(name="Momo the first.", bio="You know me.")
        self.george = Dog.objects.create(name="George", bark="Whoof!")
        self.adam = Dog.objects.create(name="Adam", bark="Whef, the whef!")

    def test_render_search_and_replace_form(self):
        request = RequestFactory().get("/")

        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertContains(response, "search_and_replace_dog_name")
        self.assertContains(response, "search_and_replace_dog_bark")

    def test_search_and_replace_form_without_preview_does_not_contain_preview_id(self):
        request = RequestFactory().get("/")

        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertNotContains(response, "preview_id")

    def test_search_and_replace_after_submit_contains_preview_id(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "the",
                "search_and_replace_dog_bark": "true",
                "search_and_replace_dog_name": "true",
                "search_and_replace_cat_bio": "true",
                "search_and_replace_cat_name": "true",
            },
        )
        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertContains(response, 'name="preview_id" value="')

    def test_render_search_and_replace_form_preview_contains_the_right_instances(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "the",
                "search_and_replace_dog_bark": "true",
                "search_and_replace_dog_name": "true",
                "search_and_replace_cat_bio": "true",
                "search_and_replace_cat_name": "true",
            },
        )

        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertContains(response, "Lucy")
        self.assertContains(response, "Peter")
        self.assertContains(response, "Momo")
        self.assertContains(response, "Adam")
        self.assertNotContains(response, "George")

    def test_render_search_and_replace_form_preview_matches_the_right_fields(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "the",
                "search_and_replace_dog_bark": "true",
                "search_and_replace_dog_name": "true",
                "search_and_replace_cat_bio": "true",
                "search_and_replace_cat_name": "false",
            },
        )

        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertContains(response, "Lucy")
        self.assertContains(response, "Peter")
        self.assertContains(response, "Adam")
        self.assertNotContains(response, "Momo")
        self.assertNotContains(response, "George")

    def test_render_search_and_replace_form_preview_contains_the_right_values(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "the",
                "replace": "teh",
                "search_and_replace_dog_bark": "true",
                "search_and_replace_dog_name": "true",
                "search_and_replace_cat_bio": "true",
                "search_and_replace_cat_name": "true",
            },
        )

        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertContains(response, "the deep south")
        self.assertContains(response, "teh deep south")
        self.assertContains(response, "the north")
        self.assertContains(response, "teh north")
        self.assertContains(response, "the first")
        self.assertContains(response, "teh first")
        self.assertContains(response, "the whef")
        self.assertContains(response, "teh whef")

    def test_preview_does_not_change_values(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "the",
                "replace": "teh",
                "search_and_replace_dog_bark": "true",
                "search_and_replace_dog_name": "true",
                "search_and_replace_cat_bio": "true",
                "search_and_replace_cat_name": "true",
            },
        )

        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)

        self.lucy.refresh_from_db()

        self.assertContains(response, "the deep south")
        self.assertContains(response, "teh deep south")
        self.assertIn("the", self.lucy.bio)
        self.assertNotIn("teh", self.lucy.bio)

    def test_render_invalid_form(self):
        request = RequestFactory().post("/", {})
        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertContains(response, "form")

    def test_missing_preview_id_replaces_nothing(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "the",
                "replace": "teh",
                "search_and_replace_dog_bark": "true",
                "search_and_replace_dog_name": "true",
                "search_and_replace_cat_bio": "true",
                "search_and_replace_cat_name": "true",
                "apply": "true",
            },
        )
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)

        SearchAndReplaceView.as_view(models_and_fields=self.models_and_fields)(request)

        self.lucy.refresh_from_db()

        self.assertEqual(self.lucy.bio, "Grew up in the deep south.")

    def test_replace_text_replaces_text(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "the",
                "replace": "teh",
                "search_and_replace_dog_bark": "true",
                "search_and_replace_dog_name": "true",
                "search_and_replace_cat_bio": "true",
                "search_and_replace_cat_name": "true",
                "apply": "true",
                "preview_id": "an-id-used-to-prevent-double-submit",
            },
        )
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)

        SearchAndReplaceView.as_view(models_and_fields=self.models_and_fields)(request)

        self.lucy.refresh_from_db()
        self.momo.refresh_from_db()
        self.adam.refresh_from_db()

        self.assertEqual(self.lucy.bio, "Grew up in teh deep south.")
        self.assertEqual(self.momo.name, "Momo teh first.")
        self.assertEqual(self.adam.bark, "Whef, teh whef!")

    def test_replace_text_preserves_whitespace(self):
        request = RequestFactory().post(
            "/",
            {
                "search": " the ",
                "replace": "X  ",
                "search_and_replace_cat_bio": "true",
                "apply": "true",
                "preview_id": "more-ids-used-to-prevent-double-submit",
            },
        )
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)

        SearchAndReplaceView.as_view(models_and_fields=self.models_and_fields)(request)

        self.lucy.refresh_from_db()

        self.assertEqual(self.lucy.bio, "Grew up inX  deep south.")

    def test_search_is_case_sensitive(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "South",
                "replace": "east",
                "search_and_replace_cat_bio": "true",
            },
        )
        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertNotContains(response, "Lucy")

        request = RequestFactory().post(
            "/",
            {
                "search": "south",
                "replace": "east",
                "search_and_replace_cat_bio": "true",
            },
        )
        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)
        self.assertContains(response, "Lucy")

    def test_prevent_double_submit(self):
        request = RequestFactory().post(
            "/",
            {
                "search": "Lucy",
                "replace": "Lucy Lucy",
                "search_and_replace_cat_name": "true",
                "apply": "true",
                "preview_id": "another-id-used-in-a-double-submit",
            },
        )
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)

        self.assertEqual(response.status_code, 302)

        self.lucy.refresh_from_db()
        self.assertEqual(self.lucy.name, "Lucy Lucy")

        request = RequestFactory().post(
            "/",
            {
                "search": "Lucy",
                "replace": "Lucy Lucy",
                "search_and_replace_cat_name": "true",
                "apply": "true",
                "preview_id": "another-id-used-in-a-double-submit",
            },
        )
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        response = SearchAndReplaceView.as_view(
            models_and_fields=self.models_and_fields
        )(request)

        self.assertEqual(response.status_code, 200)

        self.lucy.refresh_from_db()
        self.assertEqual(self.lucy.name, "Lucy Lucy")
