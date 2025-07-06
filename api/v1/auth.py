from hashlib import md5

from async_fastapi_jwt_auth import AuthJWT
from core.settings import settings
from db.redis_db import get_redis
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer
from models import History, User
from redis.asyncio import Redis
from schemas import Tokens, UserCreate, UserCreated, UserInDB, UserLogin, UserResponse
from security import PROTECTED, REFRESH_PROTECTED
from sqlalchemy.exc import IntegrityError
from starlette import status


router = APIRouter()


@router.post("/signup", response_model=UserCreated, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate) -> UserCreated:
    user_dto = jsonable_encoder(user_create)
    try:
        raw_user = await User.create(**user_dto)

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such login is registered already",
        )

    return raw_user


@router.post("/login", response_model=Tokens)
async def login(
    user_login: UserLogin,
    user_agent: str = Header(default=None),
    authorize: AuthJWT = Depends(),
) -> Tokens:
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

    user_in_db = UserInDB.from_orm(db_user)
    user = UserResponse.parse_obj(user_in_db)
    tokens = await Tokens.create(
        authorize=authorize,
        user=user,
        user_agent=user_agent,
    )

    db_history = History(
        user_id=db_user.id,
        user_agent=user_agent,
    )
    await db_history.save()

    return tokens


@router.post("/logout", dependencies=PROTECTED)
async def logout(
    user_agent: str = Header(default=None),
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> dict:
    access_key = await authorize.get_jwt_subject()
    access_token_expires = settings.authjwt_access_token_expires
    current_access_token = credentials.credentials
    await redis.sadd(access_key, current_access_token)
    await redis.expire(access_key, time=access_token_expires)

    user_claim = await authorize.get_raw_jwt()
    current_user = UserResponse.model_validate(user_claim)
    user_agent_hash = md5(user_agent.encode()).hexdigest()
    refresh_key = f"refresh.{current_user.id}.{user_agent_hash}"
    await redis.delete(refresh_key)
    return {}


@router.post("/refresh", dependencies=REFRESH_PROTECTED)
async def refresh(
    user_agent: str = Header(default=None),
    authorize: AuthJWT = REFRESH_PROTECTED[0],
    redis: Redis = Depends(get_redis),
):
    old_refresh_key = await authorize.get_jwt_subject()
    await redis.delete(old_refresh_key)

    user_claims = await authorize.get_raw_jwt()
    current_user = UserResponse.parse_obj(user_claims)
    tokens = await Tokens.create(authorize=authorize, user=current_user, user_agent=user_agent)
    return tokens
