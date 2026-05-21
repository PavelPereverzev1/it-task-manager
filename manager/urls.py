from django.urls import path

from .views import TaskListView, WorkerListView, index

urlpatterns = [
    path("", index, name="index"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
]

app_name = "manager"
