from uuid import UUID

from constants import SocialType

from .base import Model


class SocialDB(Model):
    id: UUID
    social_id: str
    type: SocialType
    user_id: UUID
