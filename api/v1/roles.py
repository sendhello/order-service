from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from models import Role, Rules
from schemas import RoleCreate, RoleInDB, RoleUpdate
from sqlalchemy.exc import IntegrityError
from starlette import status

from ..utils import PaginateQueryParams


router = APIRouter()


@router.get("/", response_model=list[RoleInDB])
async def get_roles(paginate: Annotated[PaginateQueryParams, Depends(PaginateQueryParams)]) -> list[Role]:
    roles = await Role.get_all(page=paginate.page, page_size=paginate.page_size)
    return roles


@router.post("/", response_model=RoleInDB)
async def create_role(role_in: RoleCreate) -> Role:
    role_dto = jsonable_encoder(role_in)
    try:
        role = await Role.create(**role_dto)

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role with such title already exists",
        )

    return role


@router.get("/{id}", response_model=RoleInDB)
async def get_role(id: UUID) -> Role:
    role = await Role.get_by_id(id_=id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role doesn't exists")

    return role


@router.put("/{id}", response_model=RoleInDB)
async def update_role(id: UUID, role_in: RoleUpdate) -> Role:
    role = await Role.get_by_id(id_=id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role doesn't exists")

    role_dto = jsonable_encoder(role_in)
    role = await role.update(**role_dto)
    return role


@router.delete("/{id}", response_model=RoleInDB)
async def delete_role(id: UUID) -> Role:
    role = await Role.get_by_id(id_=id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role doesn't exists")

    return await role.delete()


@router.post("/{id}/set_rule", response_model=RoleInDB)
async def set_rule(id: UUID, rule: Rules) -> Role:
    role = await Role.get_by_id(id_=id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role doesn't exists")

    current_rules = role.rules
    if rule.value in current_rules:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role has this rule already")

    role.rules = [*current_rules, rule.value]
    await role.save()

    return role


@router.post("/{id}/remove_rule", response_model=RoleInDB)
async def remove_rule(id: UUID, rule: Rules) -> Role:
    role = await Role.get_by_id(id_=id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role doesn't exists")

    current_rules = [*role.rules]
    if rule.value not in current_rules:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role doesn't have this rule")

    current_rules.remove(rule.value)
    role.rules = current_rules
    await role.save()

    return role
