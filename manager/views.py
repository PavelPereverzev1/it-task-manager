from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View, generic

from .forms import (
    SearchForm,
    TaskForm,
    TaskStatusUpdateForm,
    TaskTypeForm,
    WorkerCreationForm,
    WorkerUpdateForm,
)
from .models import Position, Task

Worker = get_user_model()


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


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    template_name = "manager/task_detail.html"
    context_object_name = "task"

    # Твой оптимизированный запрос (убирает проблему N+1 для типов задач и исполнителей)
    queryset = Task.objects.prefetch_related("assignees").select_related(
        "task_type", "created_by"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем страницу, с которой пришел пользователь
        referer = self.request.META.get("HTTP_REFERER")
        default_url = reverse_lazy("manager:task-list")

        # Если реферер ведет на саму себя (например, после обновления статуса через модалку),
        # сбрасываем на дефолтный список, чтобы избежать бесконечного цикла
        if referer and self.request.path in referer:
            context["back_url"] = default_url
        else:
            context["back_url"] = referer or default_url

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
        return self.request.user in task.assignees.all()

    def get_success_url(self):
        # После изменения статуса возвращаем воркера на ту же страницу деталей задачи
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
        queryset = Worker.objects.all().order_by("username")
        form = SearchForm(self.request.GET)

        if form.is_valid() and form.cleaned_data["search_query"]:
            query = form.cleaned_data["search_query"]
            # Ищем совпадения по username, имени или фамилии (без учета регистра)
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

        # Получаем все задачи, закрепленные за этим сотрудником
        worker_tasks = (
            worker.tasks.all()
        )  # Предполагаем, что related_name="tasks" у связи assignees в модели Task

        # Если related_name не задан, Django по умолчанию использует task_set:
        # worker_tasks = worker.task_set.all()

        # Делим задачи на две категории для красивого отображения в табах или списках
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
        # Добавляем аннотацию workers_count.
        # Django автоматически свяжет её с твоей моделью Worker (по умолчанию через 'worker_set' или твой related_name)
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
        # Строгая проверка твоего кастомного флага из модели Worker
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
