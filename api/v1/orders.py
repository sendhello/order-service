from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from async_fastapi_jwt_auth import AuthJWT
from security import PROTECTED
from services.order_service import OrderService
from schemas.order import (
    OrderCreate, 
    OrderUpdate, 
    OrderResponse, 
    OrderList, 
    OrderAssign, 
    OrderDeliveryComplete
)


router = APIRouter()


@router.post("/", response_model=OrderResponse, summary="Создать заказ")
async def create_order(
    order_data: OrderCreate,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Создание нового заказа."""

    return await OrderService.create_order(order_data)


@router.get("/", response_model=OrderList, summary="Получить список заказов")
async def get_orders(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    courier_id: Optional[UUID] = Query(None, description="Фильтр по курьеру"),
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderList:
    """Получение списка заказов с возможностью фильтрации."""
    return await OrderService.get_orders(page, page_size, status, courier_id)


@router.get("/{order_id}", response_model=OrderResponse, summary="Получить заказ по ID")
async def get_order_by_id(
    order_id: UUID,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Получение заказа по ID."""
    return await OrderService.get_order_by_id(order_id)


@router.get("/tracking/{tracking_id}", response_model=OrderResponse, summary="Получить заказ по tracking ID")
async def get_order_by_tracking_id(
    tracking_id: UUID,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Получение заказа по tracking ID."""
    return await OrderService.get_order_by_tracking_id(tracking_id)


@router.put("/{order_id}", response_model=OrderResponse, summary="Обновить заказ")
async def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Обновление данных заказа."""
    return await OrderService.update_order(order_id, order_data)


@router.post("/{order_id}/assign", response_model=OrderResponse, summary="Назначить курьера")
async def assign_courier(
    order_id: UUID,
    assign_data: OrderAssign,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Назначение курьера на заказ."""
    return await OrderService.assign_courier(order_id, assign_data.courier_id)


@router.post("/{order_id}/start", response_model=OrderResponse, summary="Начать доставку")
async def start_delivery(
    order_id: UUID,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Начало доставки заказа."""
    return await OrderService.start_delivery(order_id)


@router.post("/{order_id}/complete", response_model=OrderResponse, summary="Завершить доставку")
async def complete_delivery(
    order_id: UUID,
    completion_data: OrderDeliveryComplete,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Завершение доставки заказа."""
    return await OrderService.complete_delivery(
        order_id, 
        completion_data.delivery_photo_url, 
        completion_data.recipient_signature
    )


@router.post("/{order_id}/cancel", response_model=OrderResponse, summary="Отменить заказ")
async def cancel_order(
    order_id: UUID,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> OrderResponse:
    """Отмена заказа."""
    return await OrderService.cancel_order(order_id)


@router.delete("/{order_id}", summary="Удалить заказ")
async def delete_order(
    order_id: UUID,
    authorize: AuthJWT = Depends(PROTECTED[0])
) -> dict:
    """Удаление заказа."""
    await OrderService.delete_order(order_id)
    return {"message": "Заказ успешно удален"}
