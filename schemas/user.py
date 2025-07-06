from pydantic import model_validator, EmailStr, Field

from .base import Model
from .mixins import IdMixin
from .roles import RoleInDB


class BaseUser(Model):
    email: EmailStr


class PersonalUser(Model):
    first_name: str
    last_name: str


class UserLogin(BaseUser):
    password: str


class UserCreate(UserLogin, PersonalUser):
    pass


class SocialUserCreate(BaseUser, PersonalUser):
    pass


class UserCreated(BaseUser, PersonalUser, IdMixin):
    """Модель пользователя при выводе после регистрации."""

    pass


class UserResponse(UserCreated):
    """Модель пользователя при авторизации.

    Умеет распаршивать модель UserInDB
    """

    login: str | None = None
    role: str | None = None
    rules: list[str] = Field(default_factory=list)

    @classmethod
    @model_validator(mode="before")
    def set_rules(cls, values: dict) -> dict:
        role = values.get("role", {})
        if isinstance(role, RoleInDB):
            values["rules"] = role.rules
            values["role"] = role.title

        return values


class UserInDB(UserCreated):
    """Модель пользователя в БД."""

    login: str | None = None
    role: RoleInDB | None = None


class UserUpdate(BaseUser, PersonalUser):
    """Модель пользователя для обновления данных."""

    current_password: str


class UserChangePassword(Model):
    """Модель пользователя для смены пароля."""

    current_password: str
    new_password: str
