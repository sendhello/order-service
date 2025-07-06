from hashlib import md5
from typing import Self

import orjson
from async_fastapi_jwt_auth import AuthJWT
from core.settings import settings
from db.redis_db import get_redis

from .base import Model
from .user import UserResponse


class Tokens(Model):
    access_token: str
    refresh_token: str

    @classmethod
    async def create(cls, authorize: AuthJWT, user: UserResponse, user_agent: str) -> Self:
        user_claims = orjson.loads(user.json())
        user_agent_hash = md5(user_agent.encode()).hexdigest()

        access_key = f"access.{user.id}.{user_agent_hash}"
        access_token = await authorize.create_access_token(subject=access_key, user_claims=user_claims)

        refresh_key = f"refresh.{user.id}.{user_agent_hash}"
        refresh_token = await authorize.create_refresh_token(subject=refresh_key, user_claims=user_claims)

        redis = await get_redis()
        refresh_token_expires = settings.authjwt_refresh_token_expires
        await redis.setex(name=refresh_key, time=refresh_token_expires, value=refresh_token)

        return cls(access_token=access_token, refresh_token=refresh_token)
