from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer


async def protected(
    authorize: AuthJWT = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> AuthJWT:
    try:
        await authorize.jwt_required()

    except AuthJWTException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return authorize
