from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("register/", views.WorkerRegisterView.as_view(), name="worker-register"),
    path("tasks/all/", views.TaskAllListView.as_view(), name="task-all-list"),
    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/update/", views.TaskUpdateView.as_view(), name="task-update"),
    path(
        "tasks/<int:pk>/update-status/",
        views.TaskUpdateStatusView.as_view(),
        name="task-update-status",
    ),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task-delete"),
    path("workers/", views.WorkerListView.as_view(), name="worker-list"),
    path("workers/<int:pk>/", views.WorkerDetailView.as_view(), name="worker-detail"),
    path(
        "workers/<int:pk>/update/",
        views.WorkerUpdateView.as_view(),
        name="worker-update",
    ),
    path("positions/", views.PositionListView.as_view(), name="position-list"),
    path(
        "positions/create/", views.PositionCreateView.as_view(), name="position-create"
    ),
    path(
        "task-types/create-ajax/",
        views.TaskTypeCreateAjaxView.as_view(),
        name="task-type-create-ajax",
    ),
    path("projects/", views.ProjectListView.as_view(), name="project-list"),
    path("projects/all/", views.ProjectAllListView.as_view(), name="project-all-list"),
    path("projects/create/", views.ProjectCreateView.as_view(), name="project-create"),
    path(
        "projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project-detail"
    ),
    path(
        "projects/<int:pk>/attach-tasks/",
        views.ProjectAttachTasksView.as_view(),
        name="project-attach-tasks",
    ),
    path(
        "projects/<int:project_id>/tasks/create/",
        views.ProjectTaskCreateView.as_view(),
        name="project-task-create",
    ),
    path(
        "projects/<int:pk>/update/",
        views.ProjectUpdateView.as_view(),
        name="project-update",
    ),
    path(
        "projects/<int:pk>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project-delete",
    ),
]

app_name = "manager"
