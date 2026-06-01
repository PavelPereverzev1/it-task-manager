from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Position, Project, Task, TaskType, Worker


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("position",)

    list_filter = UserAdmin.list_filter + ("position",)

    fieldsets = UserAdmin.fieldsets + (
        (("Additional info", {"fields": ("position",)}),)
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (("Additional info", {"fields": ("position",)}),)
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "deadline", "is_completed", "priority", "task_type")

    list_filter = ("is_completed", "priority", "task_type", "deadline")

    search_fields = ("name", "description")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "deadline")

    search_fields = ("name", "description")

    list_filter = ("deadline", "manager")

    date_hierarchy = "deadline"


admin.site.register(Position)
admin.site.register(TaskType)
