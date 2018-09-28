# django-search-and-replace
A simple app that allows searching and replacing values in a specified set of models.

## Getting started
Add `search_and_replace` to your `INSTALLED_APPS` and add a url for the search and replace view.

```
from django.urls import path
from search_and_replace.views import SearchAndReplaceView
from example.models import Cat, Dog

urlpatterns += [
    path(
        "admin/search_and_replace/",
        SearchAndReplaceView.as_view(
            models_and_fields=[(Cat, ("name", "bio")), (Dog, ("name", "bark"))]
        ),
        name="search-and-replace",
    )
]
```
