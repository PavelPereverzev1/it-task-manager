from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from manager.models import Position, Project, Task, TaskType

Worker = get_user_model()


class TestModels(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.task_type = TaskType.objects.create(name="Bug")

        self.manager_user = Worker.objects.create_user(
            username="manager_bob", password="password123", is_manager=True
        )
        self.worker_user = Worker.objects.create_user(
            username="worker_alice",
            password="password123",
            position=self.position,
            is_manager=False,
        )
        self.project = Project.objects.create(
            name="Test Project",
            deadline=timezone.now().date(),
            manager=self.manager_user,
        )

    def test_position_str(self):
        self.assertEqual(str(self.position), "Developer")

    def test_position_name_unique(self):
        with self.assertRaises(IntegrityError):
            Position.objects.create(name="Developer")

    def test_worker_str(self):
        self.assertEqual(str(self.worker_user), "worker_alice")

    def test_worker_profile_data(self):
        self.assertTrue(self.manager_user.is_manager)
        self.assertFalse(self.worker_user.is_manager)
        self.assertEqual(self.worker_user.position, self.position)

    def test_project_str(self):
        self.assertEqual(str(self.project), "Test Project")

    def test_project_manager_relation(self):
        self.assertEqual(self.project.manager, self.manager_user)
        self.assertIn(self.project, self.manager_user.projects.all())

    def test_task_creation_and_str(self):
        task = Task.objects.create(
            name="Fix authentication bug",
            deadline=timezone.now(),
            task_type=self.task_type,
            created_by=self.manager_user,
            project=self.project,
        )
        expected_str = "Fix authentication bug (Completed: False)"
        self.assertEqual(str(task), expected_str)

    def test_task_assignees_many_to_many(self):
        task = Task.objects.create(
            name="Task with team",
            deadline=timezone.now(),
            task_type=self.task_type,
        )
        task.assignees.add(self.worker_user)

        self.assertIn(self.worker_user, task.assignees.all())
        self.assertIn(task, self.worker_user.tasks.all())

    def test_task_without_project_is_allowed(self):
        task = Task.objects.create(
            name="Standalone Task",
            deadline=timezone.now(),
            task_type=self.task_type,
            project=None,
        )
        self.assertIsNone(task.project)
