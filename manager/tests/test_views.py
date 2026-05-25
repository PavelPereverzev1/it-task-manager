from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from manager.models import Position, Project, Task, TaskType

Worker = get_user_model()


class IndexViewTests(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.user = Worker.objects.create_user(
            username="testuser", password="password123", position=self.position
        )
        self.client.login(username="testuser", password="password123")

    def test_index_view_returns_correct_context(self):
        response = self.client.get(reverse("manager:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "manager/index.html")

        self.assertEqual(response.context["num_workers"], 1)
        self.assertEqual(response.context["num_positions"], 1)


class TaskListViewTests(TestCase):
    def setUp(self):
        # 1. Сначала создаем должность (она нужна для воркеров)
        self.position = Position.objects.create(name="Developer")

        # 2. Затем создаем пользователей (чтобы менеджер существовал до создания задачи)
        self.manager = Worker.objects.create_user(
            username="manager",
            password="password",
            is_manager=True,
            position=self.position,
        )
        self.worker = Worker.objects.create_user(
            username="worker",
            password="password",
            is_manager=False,
            position=self.position,
        )

        # 3. Создаем тип задачи (он обязателен для модели Task)
        self.task_type = TaskType.objects.create(name="QA")

        # 4. И только теперь ОДИН РАЗ создаем задачу со всеми обязательными полями
        self.task = Task.objects.create(
            name="Test Task",
            created_by=self.manager,
            deadline=timezone.now() + timedelta(days=2),
            task_type=self.task_type,
        )

        # Назначаем воркера исполнителем
        self.task.assignees.add(self.worker)

    def test_manager_sees_created_tasks(self):
        self.client.login(username="manager", password="password")
        response = self.client.get(reverse("manager:task-list"))
        self.assertIn(self.task, response.context["task_list"])

    def test_worker_sees_assigned_tasks(self):
        self.client.login(username="worker", password="password")
        response = self.client.get(reverse("manager:task-list"))
        self.assertIn(self.task, response.context["task_list"])


class TaskCreateViewTests(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="Manager")
        self.manager = Worker.objects.create_user(
            username="manager",
            password="password",
            is_manager=True,
            position=self.position,
        )
        self.worker = Worker.objects.create_user(
            username="worker",
            password="password",
            is_manager=False,
            position=self.position,
        )

        self.task_type = TaskType.objects.create(name="Bugfix")

    def test_worker_cannot_create_task(self):
        self.client.login(username="worker", password="password")
        response = self.client.post(
            reverse("manager:task-create"), data={"name": "New Task"}
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_task(self):
        self.client.login(username="manager", password="password")

        future_deadline = (timezone.now() + timedelta(days=5)).strftime(
            "%Y-%m-%dT%H:%M"
        )

        form_data = {
            "name": "Brand New Task",
            "description": "Some test description",
            "deadline": future_deadline,
            "priority": "high",
            "task_type": self.task_type.id,
            "assignees": [],
        }

        response = self.client.post(reverse("manager:task-create"), data=form_data)

        self.assertEqual(response.status_code, 302)

        task = Task.objects.get(name="Brand New Task")
        self.assertEqual(task.created_by, self.manager)


class TaskTypeCreateAjaxViewTests(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="Manager")
        self.manager = Worker.objects.create_user(
            username="manager",
            password="password",
            is_manager=True,
            position=self.position,
        )
        self.client.login(username="manager", password="password")

    def test_ajax_create_task_type_success(self):
        response = self.client.post(
            reverse("manager:task-type-create-ajax"),  # подставь имя своего урла
            data={"name": "Bugfix"},
        )

        self.assertEqual(response.status_code, 201)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["name"], "Bugfix")

    def test_ajax_create_task_type_invalid(self):
        response = self.client.post(
            reverse("manager:task-type-create-ajax"), data={"name": ""}
        )

        self.assertEqual(response.status_code, 400)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertIn("error", json_data)


class ProjectCRUDViewTests(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="Manager")
        self.manager = Worker.objects.create_user(
            username="manager1",
            password="password",
            is_manager=True,
            position=self.position,
        )
        self.hacker = Worker.objects.create_user(
            username="worker1",
            password="password",
            is_manager=False,
            position=self.position,
        )
        self.project = Project.objects.create(
            name="Testing Project", manager=self.manager, deadline="2026-12-31"
        )

    def test_foreign_user_cannot_edit_project(self):
        self.client.login(username="worker1", password="password")
        response = self.client.get(
            reverse("manager:project-update", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_creator_can_edit_project(self):
        self.client.login(username="manager1", password="password")
        response = self.client.get(
            reverse("manager:project-update", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
