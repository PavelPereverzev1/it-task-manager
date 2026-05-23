from django.urls import path

from .views import (
    PositionListView,
    TaskAllListView,
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskListView,
    TaskUpdateStatusView,
    TaskUpdateView,
    WorkerDetailView,
    WorkerListView,
    WorkerRegisterView,
    WorkerUpdateView,
    index,
)

urlpatterns = [
    path("", index, name="index"),
    path("register/", WorkerRegisterView.as_view(), name="worker-register"),
    path("tasks/all/", TaskAllListView.as_view(), name="task-all-list"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/create/", TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/update/", TaskUpdateView.as_view(), name="task-update"),
    path(
        "tasks/<int:pk>/update-status/",
        TaskUpdateStatusView.as_view(),
        name="task-update-status",
    ),
    path("tasks/<int:pk>/delete/", TaskDeleteView.as_view(), name="task-delete"),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
    path("workers/<int:pk>/", WorkerDetailView.as_view(), name="worker-detail"),
    path("workers/<int:pk>/update/", WorkerUpdateView.as_view(), name="worker-update"),
    path("positions/", PositionListView.as_view(), name="position-list"),
]

app_name = "manager"
