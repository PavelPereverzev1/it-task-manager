from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from manager.models import Project, Task, TaskType

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

        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "position": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.is_manager:
            del self.fields["position"]


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
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "task_type": forms.Select(attrs={"class": "form-control"}),
            "assignees": forms.CheckboxSelectMultiple(
                attrs={"class": "task-assignees-checkboxes"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignees"].required = False


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
        fields = ["is_completed"]

        widgets = {
            "is_completed": forms.Select(
                choices=[(False, "In Progress"), (True, "Completed")],
                attrs={"class": "form-select"},
            ),
        }


class TaskTypeForm(forms.ModelForm):
    class Meta:
        model = TaskType
        fields = ["name"]


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "deadline"]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter project title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the project goals...",
                }
            ),
            "deadline": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class AttachTasksForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if project:
            self.fields["tasks"].initial = project.tasks.all()

        if user:
            from django.db.models import Q

            self.fields["tasks"].queryset = Task.objects.filter(created_by=user).filter(
                Q(project__isnull=True) | Q(project=project)
            )
