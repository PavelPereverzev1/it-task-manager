from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from .forms import TaskForm, WorkerCreationForm
from .models import Position, Task, Worker


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


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    context_object_name = "task_list"
    template_name = "manager/task_list.html"
    queryset = Task.objects.order_by("is_completed", "deadline")
    paginate_by = 5


class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"
    success_url = reverse_lazy("manager:task-list")

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_manager


class WorkerListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    context_object_name = "worker_list"
    template_name = "manager/worker_list.html"

    queryset = Worker.objects.select_related("position")


class WorkerRegisterView(generic.CreateView):
    model = Worker
    form_class = WorkerCreationForm
    template_name = "registration/register.html"

    success_url = reverse_lazy("login")


class PositionListView(LoginRequiredMixin, generic.ListView):
    model = Position
    context_object_name = "position_list"
    template_name = "manager/position_list.html"

    queryset = Position.objects.annotate(workers_count=Count("workers"))


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    template_name = "manager/task_detail.html"
    context_object_name = "task"

    queryset = Task.objects.prefetch_related("assignees").select_related("task_type")
