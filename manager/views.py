from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View, generic

from .forms import (
    AttachTasksForm,
    ProjectForm,
    SearchForm,
    TaskForm,
    TaskStatusUpdateForm,
    TaskTypeForm,
    WorkerCreationForm,
    WorkerUpdateForm,
)
from .mixins import CheckPermissionRequiredMixin, OnlyObjectOwnerRequiredMixin
from .models import Position, Project, Task

Worker = get_user_model()


class IndexView(generic.TemplateView):
    template_name = "manager/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "num_tasks": Task.objects.count(),
                "num_projects": Project.objects.count(),
                "num_workers": Worker.objects.count(),
                "num_positions": Position.objects.count(),
            }
        )
        return context


class TaskAllListView(LoginRequiredMixin, generic.ListView):
    model = Task
    context_object_name = "task_list"
    template_name = "manager/task_list.html"
    paginate_by = 5

    def get_queryset(self):
        queryset = Task.objects.select_related("task_type", "project")
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
        queryset = Task.objects.select_related("task_type", "project")

        if self.request.user.is_manager:
            return queryset.filter(created_by=self.request.user)
        return queryset.filter(assignees=self.request.user)


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    template_name = "manager/task_detail.html"
    context_object_name = "task"
    queryset = Task.objects.prefetch_related("assignees").select_related(
        "task_type", "created_by"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        referer = self.request.META.get("HTTP_REFERER")
        default_url = reverse_lazy("manager:task-list")

        if referer:
            referer_path = urlparse(referer).path

            if self.request.path in referer_path:
                context["back_url"] = default_url
            else:
                context["back_url"] = referer_path
        else:
            context["back_url"] = default_url

        return context


class TaskCreateView(
    LoginRequiredMixin, CheckPermissionRequiredMixin, generic.CreateView
):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"
    success_url = reverse_lazy("manager:task-list")

    permission_required = "manager.add_task"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class TaskUpdateView(
    LoginRequiredMixin,
    CheckPermissionRequiredMixin,
    OnlyObjectOwnerRequiredMixin,
    generic.UpdateView,
):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"

    permission_required = "manager.change_task"
    owner_field = "created_by"

    def get_success_url(self):
        return reverse_lazy("manager:task-detail", kwargs={"pk": self.object.pk})


class TaskUpdateStatusView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskStatusUpdateForm
    raise_exception = True

    def get_success_url(self):
        return reverse_lazy("manager:task-detail", kwargs={"pk": self.object.pk})


class TaskDeleteView(
    LoginRequiredMixin,
    CheckPermissionRequiredMixin,
    OnlyObjectOwnerRequiredMixin,
    generic.DeleteView,
):
    model = Task
    template_name = "manager/task_confirm_delete.html"
    success_url = reverse_lazy("manager:task-list")

    permission_required = "manager.delete_task"
    owner_field = "created_by"


class WorkerListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    context_object_name = "worker_list"
    template_name = "manager/worker_list.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = queryset = (
            Worker.objects.select_related("position").all().order_by("username")
        )
        form = SearchForm(self.request.GET)

        if form.is_valid() and form.cleaned_data["search_query"]:
            query = form.cleaned_data["search_query"]
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = SearchForm(
            self.request.GET, placeholder_text="Search workers by name or username..."
        )
        return context


class WorkerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Worker
    context_object_name = "worker"
    template_name = "manager/worker_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        worker = self.get_object()

        worker_tasks = worker.tasks.select_related("task_type")

        context["in_progress_tasks"] = worker_tasks.filter(is_completed=False).order_by(
            "deadline"
        )
        context["completed_tasks"] = worker_tasks.filter(is_completed=True).order_by(
            "-deadline"
        )

        return context


class WorkerRegisterView(generic.CreateView):
    model = Worker
    form_class = WorkerCreationForm
    template_name = "registration/register.html"

    success_url = reverse_lazy("login")


class WorkerUpdateView(
    LoginRequiredMixin, OnlyObjectOwnerRequiredMixin, generic.UpdateView
):
    model = Worker
    form_class = WorkerUpdateForm
    template_name = "manager/worker_form.html"

    owner_field = "self"

    def get_success_url(self):
        return reverse_lazy("manager:worker-detail", kwargs={"pk": self.object.pk})


class PositionListView(LoginRequiredMixin, generic.ListView):
    model = Position
    context_object_name = "position_list"
    template_name = "manager/position_list.html"
    paginate_by = 5

    def get_queryset(self):
        queryset = Position.objects.annotate(workers_count=Count("workers")).order_by(
            "name"
        )

        form = SearchForm(self.request.GET)

        if form.is_valid() and form.cleaned_data["search_query"]:
            query = form.cleaned_data["search_query"]
            queryset = queryset.filter(name__icontains=query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = SearchForm(
            self.request.GET, placeholder_text="Search positions by name..."
        )
        return context


class PositionCreateView(
    LoginRequiredMixin, CheckPermissionRequiredMixin, generic.CreateView
):
    model = Position
    fields = ["name"]
    template_name = "manager/position_form.html"
    success_url = reverse_lazy("manager:position-list")

    permission_required = "manager.add_position"


class TaskTypeCreateAjaxView(LoginRequiredMixin, CheckPermissionRequiredMixin, View):
    permission_required = "manager.add_tasktype"

    def post(self, request, *args, **kwargs):
        form = TaskTypeForm(request.POST)

        if form.is_valid():
            task_type = form.save()
            return render(
                request,
                "includes/task_type_option.html",
                {"task_type": task_type},
                status=201,
            )

        error_message = form.errors.get("name", ["Invalid data"])[0]
        return HttpResponse(error_message, status=400)


class ProjectAllListView(LoginRequiredMixin, generic.ListView):
    model = Project
    context_object_name = "project_list"
    template_name = "manager/project_list.html"
    paginate_by = 6

    def get_queryset(self):
        queryset = Project.objects.select_related("manager")
        form = SearchForm(self.request.GET)

        if form.is_valid() and form.cleaned_data["search_query"]:
            queryset = queryset.filter(
                name__icontains=form.cleaned_data["search_query"]
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = SearchForm(
            self.request.GET, placeholder_text="Search projects by title..."
        )
        context["show_all_projects"] = True
        return context


class ProjectListView(LoginRequiredMixin, generic.ListView):
    model = Project
    context_object_name = "project_list"
    template_name = "manager/project_list.html"
    paginate_by = 6

    def get_queryset(self):
        if self.request.user.is_manager:
            return Project.objects.select_related("manager").filter(
                manager=self.request.user
            )
        return (
            Project.objects.select_related("manager")
            .filter(tasks__assignees=self.request.user)
            .distinct()
        )


class ProjectCreateView(
    LoginRequiredMixin, CheckPermissionRequiredMixin, generic.CreateView
):
    model = Project
    form_class = ProjectForm
    template_name = "manager/project_form.html"
    success_url = reverse_lazy("manager:project-list")

    permission_required = "manager.add_project"

    def form_valid(self, form):
        form.instance.manager = self.request.user
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    model = Project
    template_name = "manager/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_tasks"] = self.object.tasks.select_related("task_type")
        return context


class ProjectAttachTasksView(
    LoginRequiredMixin,
    CheckPermissionRequiredMixin,
    OnlyObjectOwnerRequiredMixin,
    generic.FormView,
):
    form_class = AttachTasksForm
    template_name = "manager/project_attach_tasks.html"

    permission_required = "manager.change_project"
    owner_field = "manager"

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(Project, pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project = self.get_object()
        kwargs["initial"] = {"tasks": project.tasks.all()}
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_object()
        form.fields["tasks"].queryset = Task.objects.filter(
            created_by=self.request.user
        ).filter(Q(project__isnull=True) | Q(project=project))
        return form

    def form_valid(self, form):
        project = self.get_object()
        selected_tasks = form.cleaned_data["tasks"]
        available_tasks = form.fields["tasks"].queryset

        for task in selected_tasks:
            task.project = project
            task.save()

        unselected_tasks = available_tasks.exclude(
            id__in=[t.id for t in selected_tasks]
        )
        for task in unselected_tasks:
            if task.project == project:
                task.project = None
                task.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_object()
        return context

    def get_success_url(self):
        return reverse("manager:project-detail", kwargs={"pk": self.kwargs["pk"]})


class ProjectTaskCreateView(
    LoginRequiredMixin,
    CheckPermissionRequiredMixin,
    OnlyObjectOwnerRequiredMixin,
    generic.CreateView,
):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"

    permission_required = "manager.add_task"
    owner_field = "manager"

    def get_object(self):
        if not hasattr(self, "project_object"):
            self.project_object = get_object_or_404(
                Project, pk=self.kwargs["project_id"]
            )
        return self.project_object

    def get_success_url(self):
        return reverse(
            "manager:project-detail", kwargs={"pk": self.kwargs["project_id"]}
        )

    def form_valid(self, form):
        project = self.get_object()
        form.instance.project = project
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(
    LoginRequiredMixin,
    CheckPermissionRequiredMixin,
    OnlyObjectOwnerRequiredMixin,
    generic.UpdateView,
):
    model = Project
    form_class = ProjectForm
    template_name = "manager/project_form.html"

    permission_required = "manager.change_project"
    owner_field = "manager"

    def get_success_url(self):
        return reverse_lazy("manager:project-detail", kwargs={"pk": self.object.pk})


class ProjectDeleteView(
    LoginRequiredMixin,
    CheckPermissionRequiredMixin,
    OnlyObjectOwnerRequiredMixin,
    generic.DeleteView,
):
    model = Project
    template_name = "manager/project_confirm_delete.html"
    success_url = reverse_lazy("manager:project-list")

    permission_required = "manager.delete_project"
    owner_field = "manager"
