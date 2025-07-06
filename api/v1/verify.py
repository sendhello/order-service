from typing import Annotated
from uuid import uuid4

from async_fastapi_jwt_auth import AuthJWT
from constants import ANONYMOUS, Action, Resource, Service
from db.redis_db import get_redis
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer
from models import History, Rules, User
from pydantic import EmailStr, ValidationError
from redis.asyncio import Redis
from schemas import Rule, UserInDB, UserLogin, UserResponse
from security import PART_PROTECTED
from services.rules import rules
from starlette import status


router = APIRouter()


@router.get("/token", response_model=UserResponse, dependencies=PART_PROTECTED)
async def verify(
    service: Annotated[
        Service | None,
        Query(
            title="Сервис",
            description="Имя сервиса куда запрашивается доступ",
        ),
    ] = None,
    resource: Annotated[
        Resource | None,
        Query(
            title="Ресурс",
            description="Название ресурса, к которому запрашивается доступ",
        ),
    ] = None,
    action: Annotated[
        Action | None,
        Query(
            title="Действие",
            description="Право на действие с ресурсом",
        ),
    ] = None,
    user_agent: str = Header(default=None),
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> UserResponse:
    anonymous = UserResponse(
        id=uuid4(),
        login=ANONYMOUS,
        email=EmailStr(f"{ANONYMOUS}@{ANONYMOUS}.email"),
        first_name=ANONYMOUS,
        last_name=ANONYMOUS,
        role=ANONYMOUS,
        rules=[Rules.anonymous_rules],
    )
    user_claim = await authorize.get_raw_jwt()
    current_user = UserResponse.parse_obj(user_claim) if user_claim else anonymous

    # Аутентификация без проверки прав
    if service is None and resource is None and action is None:
        return UserResponse.parse_obj(current_user)

    try:
        checked_entity = Rule(
            service=service,
            resource=resource,
            action=action,
        )
    # Если запрос содержит неполный набор параметров - отдаем "Доступ запрещен"
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    # Проверка прав
    for rule in current_user.rules:
        rule_model = rules.get(rule)
        if checked_entity in rule_model.rules:
            return UserResponse.parse_obj(current_user)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/login", response_model=UserResponse)
async def login(
    user_login: UserLogin,
    user_agent: str = Header(default=None),
) -> UserResponse:
    db_user = await User.get_by_email(email=user_login.email)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not db_user.check_password(user_login.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    db_history = History(
        user_id=db_user.id,
        user_agent=user_agent,
    )
    await db_history.save()

    current_user = UserInDB.from_orm(db_user)
    return UserResponse.parse_obj(current_user)
