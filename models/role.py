from enum import Enum

from db.postgres import Base
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from .mixins import CRUDMixin, IDMixin


class Rules(str, Enum):
    anonymous_rules = "anonymous_rules"
    user_rules = "user_rules"
    subscription_rules = "subscription_rules"
    admin_rules = "admin_rules"


class Role(Base, IDMixin, CRUDMixin):
    __tablename__ = "roles"

    title = Column(String(255), unique=True, nullable=False)
    rules = Column(ARRAY(String), nullable=False, default=[])
    users = relationship("User", back_populates="role")

    def __init__(self, title: str) -> None:
        self.title = title

    def __repr__(self) -> str:
        return f"<Role {self.title}>"
