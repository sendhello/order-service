from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from models import History, User
from schemas import HistoryInDB, UserChangePassword, UserResponse, UserUpdate
from sqlalchemy.exc import IntegrityError
from starlette import status

from ..utils import PaginateQueryParams


router = APIRouter()


@router.get("/", response_model=UserResponse)
async def user(authorize: AuthJWT = Depends()):
    user_claim = await authorize.get_raw_jwt()
    current_user = UserResponse.parse_obj(user_claim)
    return current_user


@router.get("/history", response_model=list[HistoryInDB])
async def history(
    paginate: Annotated[PaginateQueryParams, Depends(PaginateQueryParams)],
    authorize: AuthJWT = Depends(),
) -> list[History]:
    user_claim = await authorize.get_raw_jwt()
    current_user = UserResponse.parse_obj(user_claim)
    histories = await History.get_by_user_id(
        user_id=current_user.id,
        page=paginate.page,
        page_size=paginate.page_size,
    )
    return histories


@router.post("/update", response_model=UserResponse)
async def change_user(user_update: UserUpdate, authorize: AuthJWT = Depends()):
    user_claim = await authorize.get_raw_jwt()
    current_user = UserResponse.parse_obj(user_claim)

    db_user = await User.get_by_email(email=current_user.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect userdata")

    if not db_user.check_password(user_update.current_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    user_dto = jsonable_encoder(user_update)
    user_dto.pop("current_password")
    try:
        user = await db_user.update(**user_dto)

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such login is registered already",
        )

    return user


@router.post("/change_password", response_model=UserResponse)
async def change_password(user_change_password: UserChangePassword, authorize: AuthJWT = Depends()):
    user_claim = await authorize.get_raw_jwt()
    current_user = UserResponse.parse_obj(user_claim)

    db_user = await User.get_by_email(email=current_user.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect userdata")

    if not db_user.check_password(user_change_password.current_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    user_dto = jsonable_encoder(user_change_password)
    user_dto.pop("current_password")
    try:
        user = await db_user.change_password(user_change_password.new_password)

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such login is registered already",
        )

    return user
