# stacks/urls.py
from django.urls import path
from .views import (
    AddUserStackView,
    StackListCreateView,
    UserStackListCreateView,
    UserStackDetailView,
)

app_name = "stacks"

urlpatterns = [
    path("stacks/", StackListCreateView.as_view(), name="stack-list"),
    path("user-stacks/", UserStackListCreateView.as_view(), name="user-stack-list"),
    path(
        "user-stacks/<int:pk>/", UserStackDetailView.as_view(), name="user-stack-detail"
    ),
    path("user-stacks/add/", AddUserStackView.as_view(), name="add-user-stack"),
]
