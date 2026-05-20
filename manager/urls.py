from django.urls import path

from .views import TaskListView, index

urlpatterns = [
    path("", index, name="index"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
]

app_name = "manager"
