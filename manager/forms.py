from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from manager.models import Task, TaskType

Worker = get_user_model()


class WorkerCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta(UserCreationForm.Meta):
        model = Worker
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "position",
            "is_manager",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_manager":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})


class WorkerUpdateForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ["first_name", "last_name", "email", "position"]

        # Красиво стилизуем поля под Bootstrap
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-select" if False else "form-control"}
            ),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "position": forms.Select(attrs={"class": "form-select"}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "deadline",
            "priority",
            "task_type",
            "assignees",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter task title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the task...",
                }
            ),
            "deadline": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "task_type": forms.Select(attrs={"class": "form-control"}),
            "assignees": forms.CheckboxSelectMultiple(
                attrs={"class": "task-assignees-checkboxes"}
            ),
        }


class SearchForm(forms.Form):
    search_query = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        placeholder_text = kwargs.pop("placeholder_text", "Search...")
        super().__init__(*args, **kwargs)
        self.fields["search_query"].widget.attrs.update(
            {"placeholder": placeholder_text}
        )


class TaskStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        # Используем только реальное поле из модели
        fields = ["is_completed"]

        # Настраиваем виджет именно для поля is_completed
        widgets = {
            "is_completed": forms.Select(attrs={"class": "form-select"}),
        }


class TaskTypeForm(forms.ModelForm):
    class Meta:
        model = TaskType
        fields = ["name"]
