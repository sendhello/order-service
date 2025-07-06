from datetime import datetime

from .base import Model


class HistoryInDB(Model):
    """Модель истории в БД."""

    created_at: datetime
    user_agent: str
