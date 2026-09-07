"""Keep an open HTMX tab on the same frontend revision as its HTML."""

from django.http import HttpResponse
from django.utils.cache import patch_vary_headers
from django.utils.http import escape_leading_slashes

from core.assets import frontend_version


class FrontendVersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == "GET"
            and request.headers.get("HX-Request") == "true"
            and request.headers.get("X-Frontend-Version") != frontend_version()
        ):
            # Only safe navigation is repeated. Never replay a submitted form.
            response = HttpResponse()
            response["HX-Redirect"] = escape_leading_slashes(request.get_full_path())
            response["Cache-Control"] = "no-store"
        else:
            response = self.get_response(request)
        patch_vary_headers(response, ("HX-Request", "X-Frontend-Version"))
        return response
