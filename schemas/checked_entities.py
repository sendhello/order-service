from constants import Action, Resource, Service

from .base import Model


class Rule(Model):
    """Право доступа."""

    service: Service
    resource: Resource
    action: Action
