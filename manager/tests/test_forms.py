from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from manager.forms import (
    ProjectForm,
    SearchForm,
    TaskStatusUpdateForm,
    WorkerCreationForm,
    WorkerUpdateForm,
)
from manager.models import Position, TaskType

Worker = get_user_model()


class FormsTests(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="Developer")
        self.task_type = TaskType.objects.create(name="Bugfix")

    def test_worker_creation_form_valid(self):
        secure_password = "wiLX269Yu5Bg"

        form_data = {
            "username": "new_worker",
            "first_name": "John",
            "last_name": "Doe",
            "position": self.position.id,
            "is_manager": False,
            "password1": secure_password,
            "password2": secure_password,
        }
        form = WorkerCreationForm(data=form_data)

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.fields["is_manager"].widget.attrs["class"], "form-check-input"
        )

    def test_search_form_custom_placeholder(self):
        form_default = SearchForm()
        self.assertEqual(
            form_default.fields["search_query"].widget.attrs["placeholder"], "Search..."
        )

        custom_text = "Search tasks by title..."
        form_custom = SearchForm(placeholder_text=custom_text)
        self.assertEqual(
            form_custom.fields["search_query"].widget.attrs["placeholder"], custom_text
        )

    def test_task_status_update_form(self):
        form_data = {"is_completed": True}
        form = TaskStatusUpdateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_project_form_valid(self):
        form_data = {
            "name": "New Great Project",
            "description": "Project description",
            "deadline": (timezone.now() + timedelta(days=10)).date(),
        }
        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_worker_update_form_removes_position_for_manager(self):
        manager = Worker.objects.create_user(
            username="manager_profile",
            password="password",
            is_manager=True,
            position=self.position,
        )

        form = WorkerUpdateForm(instance=manager)

        self.assertNotIn("position", form.fields)
