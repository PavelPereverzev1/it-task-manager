from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


class CheckPermissionRequiredMixin(AccessMixin):
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.permission_required and not request.user.has_perm(
            self.permission_required
        ):
            raise PermissionDenied(
                "You do not have the required permissions to perform this action."
            )

        return super().dispatch(request, *args, **kwargs)


class OnlyObjectOwnerRequiredMixin:
    owner_field = None

    def dispatch(self, request, *args, **kwargs):
        if self.owner_field and hasattr(self, "get_object"):
            obj = self.get_object()

            if self.owner_field == "self":
                owner = obj
            else:
                owner = getattr(obj, self.owner_field, None)

            if owner != request.user:
                raise PermissionDenied(
                    "You are not authorized to modify or view this resource."
                )

        return super().dispatch(request, *args, **kwargs)
