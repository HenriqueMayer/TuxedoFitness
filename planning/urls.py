from django.urls import path

from planning import views

app_name = "planning"
urlpatterns = [
    path("", views.GenerateView.as_view(), name="generate"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("generations/", views.GenerationListView.as_view(), name="generations"),
    path("generations/<uuid:pk>/", views.GenerationView.as_view(), name="generation"),
    path("routines/import/", views.ImportView.as_view(), name="import"),
    path(
        "routines/proposals/<uuid:pk>/", views.ProposalView.as_view(), name="proposal"
    ),
]
