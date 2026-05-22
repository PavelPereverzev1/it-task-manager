from django.urls import path

from .views import (
    PositionListView,
    TaskCreateView,
    TaskDetailView,
    TaskListView,
    WorkerListView,
    WorkerRegisterView,
    index,
)

urlpatterns = [
    path("", index, name="index"),
    path("register/", WorkerRegisterView.as_view(), name="worker-register"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/create/", TaskCreateView.as_view(), name="task-create"),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
    path("positions/", PositionListView.as_view(), name="position-list"),
]

app_name = "manager"
