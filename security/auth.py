from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from db.redis_db import get_redis
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer
from models.role import Rules
from redis.asyncio import Redis
from schemas import UserResponse
from security.rate_limit import is_rate_limit_exceeded
from starlette import status


async def full_protected(
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> AuthJWT:
    try:
        await authorize.jwt_required()

    except AuthJWTException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    current_access_token = credentials.credentials
    if await is_rate_limit_exceeded(current_access_token):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    access_key = await authorize.get_jwt_subject()
    blocked_access_tokens = await redis.smembers(access_key)
    if not blocked_access_tokens:
        return authorize

    if current_access_token not in blocked_access_tokens:
        return authorize

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature has blocked")


async def partial_protected(
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> AuthJWT:
    try:
        await authorize.jwt_optional()

    except AuthJWTException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    current_access_token = credentials.credentials
    if await is_rate_limit_exceeded(current_access_token):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    access_key = await authorize.get_jwt_subject()
    if access_key is None:
        return authorize

    blocked_access_tokens = await redis.smembers(access_key)
    if not blocked_access_tokens:
        return authorize

    if current_access_token not in blocked_access_tokens:
        return authorize

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature has blocked")


async def refresh_protected(
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> AuthJWT:
    try:
        await authorize.jwt_refresh_token_required()
    except AuthJWTException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    current_refresh_token = credentials.credentials
    refresh_key = await authorize.get_jwt_subject()
    active_refresh_token = await redis.get(name=refresh_key)
    if current_refresh_token == active_refresh_token:
        return authorize

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Signature has blocked",
    )


async def admin_protected(
    authorize: AuthJWT = Depends(),
    redis: Redis = Depends(get_redis),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> AuthJWT:
    try:
        await authorize.jwt_required()

    except AuthJWTException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    access_key = await authorize.get_jwt_subject()
    blocked_access_tokens = await redis.smembers(access_key)
    current_access_token = credentials.credentials

    if blocked_access_tokens and current_access_token in blocked_access_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature has blocked")

    user_claim = await authorize.get_raw_jwt()
    current_user = UserResponse.parse_obj(user_claim)
    if current_user.role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    if Rules.admin_rules not in current_user.rules:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return authorize
