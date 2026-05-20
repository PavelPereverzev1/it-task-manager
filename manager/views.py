from django.shortcuts import render
from django.views import generic

from .models import Position, Task, TaskType, Worker


def index(request):
    """View function for the home page of the site."""

    num_tasks = Task.objects.count()
    num_critical_tasks = Task.objects.filter(priority="critical").count()
    num_workers = Worker.objects.count()
    num_positions = Position.objects.count()

    context = {
        "num_tasks": num_tasks,
        "num_critical_tasks": num_critical_tasks,
        "num_workers": num_workers,
        "num_positions": num_positions,
    }

    return render(request, "manager/index.html", context=context)


class TaskListView(generic.ListView):
    model = Task
    context_object_name = "task_list"
    template_name = "manager/task_list.html"

    queryset = Task.objects.order_by("is_completed", "deadline")
