from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from .forms import SearchForm, TaskForm, WorkerCreationForm
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


class TaskAllListView(LoginRequiredMixin, generic.ListView):
    model = Task
    context_object_name = "task_list"
    template_name = "manager/task_list.html"
    paginate_by = 5

    def get_queryset(self):
        queryset = Task.objects.all()
        form = SearchForm(self.request.GET)

        if form.is_valid() and form.cleaned_data["search_query"]:
            queryset = queryset.filter(
                name__icontains=form.cleaned_data["search_query"]
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_form"] = SearchForm(
            self.request.GET, placeholder_text="Search tasks by title..."
        )
        context["show_all_tasks"] = True
        return context


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    context_object_name = "task_list"
    template_name = "manager/task_list.html"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_manager:
            return queryset.filter(created_by=self.request.user)

        return queryset.filter(assignees=self.request.user)


class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"
    success_url = reverse_lazy("manager:task-list")

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_manager

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


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
