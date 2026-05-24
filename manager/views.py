from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import JsonResponse
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
from .models import Position, Project, Task

Worker = get_user_model()


def index(request):
    """View function for the home page of the site."""

    num_tasks = Task.objects.count()
    num_projects = Project.objects.count()
    num_workers = Worker.objects.count()
    num_positions = Position.objects.count()

    context = {
        "num_tasks": num_tasks,
        "num_projects": num_projects,
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


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm  # Твоя полная форма
    template_name = "manager/task_form.html"

    def test_func(self):
        # Доступ к полной форме имеет ТОЛЬКО создатель-менеджер
        return self.get_object().created_by == self.request.user

    def get_success_url(self):
        return reverse_lazy("manager:task-detail", kwargs={"pk": self.object.pk})


class TaskUpdateStatusView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Task
    form_class = TaskStatusUpdateForm

    def test_func(self):
        # Сюда пускаем только закрепленных исполнителей
        task = self.get_object()
        return (
            self.request.user in task.assignees.all()
            or task.created_by == self.request.user
        )

    def get_success_url(self):
        return reverse_lazy("manager:task-detail", kwargs={"pk": self.object.pk})


class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Task
    template_name = "manager/task_confirm_delete.html"
    success_url = reverse_lazy("manager:task-list")

    def test_func(self):
        task = self.get_object()
        # Удалять может ТОЛЬКО менеджер, который создал эту задачу
        return task.created_by == self.request.user


class WorkerListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    context_object_name = "worker_list"
    template_name = "manager/worker_list.html"
    paginate_by = 10  # Пагинация по 10 пользователей

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
        # Переиспользуем форму и динамически передаем ей новый плейсхолдер!
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


class WorkerUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Worker
    form_class = WorkerUpdateForm
    template_name = (
        "manager/worker_form.html"  # Используем стандартное имя для форм воркера
    )

    def test_func(self):
        # Получаем воркера, которого пытаются редактировать
        worker = self.get_object()
        # Проверяем: совпадает ли он с текущим залогиненным пользователем
        return worker == self.request.user

    def get_success_url(self):
        # После успешного редактирования возвращаем пользователя в его же обновленный профиль
        return reverse_lazy("manager:worker-detail", kwargs={"pk": self.object.pk})


class PositionListView(LoginRequiredMixin, generic.ListView):
    model = Position
    context_object_name = "position_list"
    template_name = "manager/position_list.html"
    paginate_by = 5

    def get_queryset(self):
        queryset = Position.objects.annotate(
            workers_count=Count(
                "workers"
            )  # Если в модели Worker поле имеет стандартный откат, пишем "worker"
        ).order_by("name")

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


class PositionCreateView(LoginRequiredMixin, generic.CreateView):
    model = Position
    fields = ["name"]
    template_name = "manager/position_form.html"
    success_url = reverse_lazy("manager:position-list")


class TaskTypeCreateAjaxView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_manager

    def post(self, request, *args, **kwargs):
        form = TaskTypeForm(request.POST)

        if form.is_valid():
            task_type = form.save()
            return JsonResponse(
                {"success": True, "id": task_type.id, "name": task_type.name},
                status=201,
            )

        # Если валидация провалена (например, имя дублируется)
        # Достаем саму строку ошибки из списка ошибок поля 'name'
        error_message = form.errors.get("name", ["Invalid data"])[0]
        return JsonResponse(
            {
                "success": False,
                "error": error_message,  # Теперь это строка, её легко прочитать в JS
            },
            status=400,
        )


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
        # Кастомный плейсхолдер для поиска по проектам
        context["search_form"] = SearchForm(
            self.request.GET, placeholder_text="Search projects by title..."
        )
        context["show_all_projects"] = True  # флаг для шаблона
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
            # Для исполнителей: выбираем проекты, где они участвуют в задачах
        return (
            Project.objects.select_related("manager")
            .filter(tasks__assignees=self.request.user)
            .distinct()
        )


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "manager/project_form.html"
    success_url = reverse_lazy("manager:project-list")

    def test_func(self):
        return self.request.user.is_manager

    def form_valid(self, form):
        # Автоматически назначаем текущего менеджера автором проекта
        form.instance.manager = self.request.user
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    model = Project
    template_name = "manager/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем в контекст все задачи, связанные с этим проектом
        context["project_tasks"] = self.object.tasks.select_related("task_type")
        return context


class ProjectAttachTasksView(LoginRequiredMixin, generic.FormView):
    form_class = AttachTasksForm
    template_name = "manager/project_attach_tasks.html"

    def get_object(self):
        return get_object_or_404(Project, pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project = self.get_object()
        kwargs["initial"] = {
            "tasks": project.tasks.all()  # подставь project.task_set.all(), если будет ошибка
        }
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_object()
        form.fields["tasks"].queryset = Task.objects.filter(
            created_by=self.request.user
        ).filter(Q(project__isnull=True) | Q(project=project))
        return form

    # --- ДОБАВЛЯЕМ ЭТОТ МЕТОД ДЛЯ СОХРАНЕНИЯ ---
    def form_valid(self, form):
        project = self.get_object()

        # 1. Получаем список задач, которые менеджер ОТМЕТИЛ галочками
        selected_tasks = form.cleaned_data["tasks"]

        # 2. Получаем список ВСЕХ задач этого менеджера, которые В ПРИНЦИПЕ были доступны в форме
        # (это нужно, чтобы понять, какие задачи менеджер СНЯЛ с галочки, чтобы отвязать их)
        available_tasks = form.fields["tasks"].queryset

        # 3. Для всех отмеченных задач устанавливаем этот проект
        for task in selected_tasks:
            task.project = project
            task.save()

        # 4. Для тех задач, с которых галочку СНЯЛИ, убираем привязку к проекту (ставим NULL)
        # Мы ищем задачи, которые были доступны, но не попали в список выбранных
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
    LoginRequiredMixin, UserPassesTestMixin, generic.CreateView
):
    model = Task
    form_class = TaskForm
    template_name = "manager/task_form.html"

    def test_func(self):
        return self.request.user.is_manager

    def get_success_url(self):
        return reverse(
            "manager:project-detail", kwargs={"pk": self.kwargs["project_id"]}
        )

    def form_valid(self, form):
        # Находим проект по ID из URL и привязываем его к задаче ДО сохранения в базу
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        form.instance.project = project
        form.instance.created_by = self.request.user
        return super().form_valid(form)
