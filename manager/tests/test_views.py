from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from manager.models import Position, Project, Task, TaskType

Worker = get_user_model()


class BaseManagerTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.dev_position = Position.objects.create(name="Developer")
        self.manager_position = Position.objects.create(name="Manager")

        self.manager = Worker.objects.create_user(
            username="manager",
            password="password",
            is_manager=True,
            position=self.manager_position,
        )
        self.worker = Worker.objects.create_user(
            username="worker",
            password="password",
            is_manager=False,
            position=self.dev_position,
        )

        manager_group, _ = Group.objects.get_or_create(name="Managers")

        content_type = ContentType.objects.get_for_model(TaskType)

        codenames = [
            "add_project",
            "change_project",
            "delete_project",
            "add_task",
            "change_task",
            "delete_task",
            "add_position",
            "add_tasktype",
        ]

        permissions = Permission.objects.filter(codename__in=codenames)
        manager_group.permissions.set(permissions)


class IndexViewTests(BaseManagerTestCase):
    def test_index_view_returns_correct_context(self):
        self.client.login(username="manager", password="password")
        response = self.client.get(reverse("manager:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "manager/index.html")

        self.assertEqual(response.context["num_workers"], 2)
        self.assertEqual(response.context["num_positions"], 2)


class TaskListViewTests(BaseManagerTestCase):
    def setUp(self):
        super().setUp()
        self.task_type = TaskType.objects.create(name="QA")
        self.task = Task.objects.create(
            name="Test Task",
            created_by=self.manager,
            deadline=timezone.now() + timedelta(days=2),
            task_type=self.task_type,
        )
        self.task.assignees.add(self.worker)

    def test_manager_sees_created_tasks(self):
        self.client.login(username="manager", password="password")
        response = self.client.get(reverse("manager:task-list"))
        self.assertIn(self.task, response.context["task_list"])

    def test_worker_sees_assigned_tasks(self):
        self.client.login(username="worker", password="password")
        response = self.client.get(reverse("manager:task-list"))
        self.assertIn(self.task, response.context["task_list"])


class TaskCreateViewTests(BaseManagerTestCase):
    def setUp(self):
        super().setUp()
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


class TaskTypeCreateAjaxViewTests(BaseManagerTestCase):
    def test_ajax_create_task_type_success(self):
        self.client.login(username="manager", password="password")
        response = self.client.post(
            reverse("manager:task-type-create-ajax"),
            data={"name": "Bugfix"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTemplateUsed(response, "includes/task_type_option.html")
        self.assertContains(response, "Bugfix", status_code=201)

    def test_ajax_create_task_type_invalid(self):
        self.client.login(username="manager", password="password")
        response = self.client.post(
            reverse("manager:task-type-create-ajax"),
            data={"name": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(response.content.decode().strip(), "")


class ProjectCRUDViewTests(BaseManagerTestCase):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(
            name="Testing Project", manager=self.manager, deadline="2026-12-31"
        )

    def test_foreign_user_cannot_edit_project(self):
        self.client.login(username="worker", password="password")
        response = self.client.get(
            reverse("manager:project-update", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_creator_can_edit_project(self):
        self.client.login(username="manager", password="password")
        response = self.client.get(
            reverse("manager:project-update", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
