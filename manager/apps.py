from django.apps import AppConfig


class ManagerConfig(AppConfig):
    name = "manager"

    def ready(self):
        import manager.signals  # noqa: F401
