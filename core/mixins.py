from rest_framework import status
from rest_framework.response import Response

from core.utils import get_actor_email


class ActorContextMixin:
    """Shared helper for extracting actor identity in API views/viewsets."""

    def actor_email(self, request=None) -> str:
        req = request or getattr(self, 'request', None)
        user = getattr(req, 'user', None)
        return get_actor_email(user)


class SoftDeleteMixin:
    """Reusable soft-delete behavior for models with an ``is_active`` flag."""

    soft_delete_field = 'is_active'
    soft_delete_value = False
    soft_delete_response_message = 'Resource deactivated successfully.'

    def get_soft_delete_response_data(self, instance):
        return {'detail': self.soft_delete_response_message}

    def perform_soft_delete(self, instance):
        setattr(instance, self.soft_delete_field, self.soft_delete_value)
        instance.save(update_fields=[self.soft_delete_field])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_soft_delete(instance)
        return Response(
            self.get_soft_delete_response_data(instance),
            status=status.HTTP_200_OK,
        )
