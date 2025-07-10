from typing import Annotated
from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, Path, Query

from api.utils import PaginateQueryParams
from constants.order import OrderStatus
from schemas.order import OrderAssign, OrderCreate, OrderDeliveryComplete, OrderList, OrderResponse, OrderUpdate
from services.order_service import OrderService


router = APIRouter()


@router.post("/", response_model=OrderResponse, summary="Create order")
async def create_order(order_data: OrderCreate, authorize: AuthJWT = Depends()) -> OrderResponse:
    """Create a new order."""

    return await OrderService.create_order(order_data)


@router.get("/", response_model=OrderList, summary="Get list of orders")
async def get_orders(
    paginate: Annotated[PaginateQueryParams, Depends(PaginateQueryParams)],
    status: OrderStatus = Query(None, description="Filter by status"),
    courier_id: UUID = Query(None, description="Filter by status"),
    authorize: AuthJWT = Depends(),
) -> OrderList:
    """Get list of orders with filtering options."""

    return await OrderService.get_orders(paginate.page, paginate.page_size, status, courier_id)


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order by ID")
async def get_order_by_id(
    order_id: UUID = Path(description="ID of the order to retrieve"), authorize: AuthJWT = Depends()
) -> OrderResponse:
    """Get order by ID."""

    return await OrderService.get_order_by_id(order_id)


@router.get("/tracking/{tracking_id}", response_model=OrderResponse, summary="Get order by tracking ID")
async def get_order_by_tracking_id(
    tracking_id: UUID = Path(description="Tracking ID of the order to retrieve"), authorize: AuthJWT = Depends()
) -> OrderResponse:
    """Get order by tracking ID."""

    return await OrderService.get_order_by_tracking_id(tracking_id)


@router.put("/{order_id}", response_model=OrderResponse, summary="Update order")
async def update_order(
    order_data: OrderUpdate,
    order_id: UUID = Path(description="ID of the order to update"),
    authorize: AuthJWT = Depends(),
) -> OrderResponse:
    """Update order data."""

    return await OrderService.update_order(order_id, order_data)


@router.post("/{order_id}/assign", response_model=OrderResponse, summary="Assign courier")
async def assign_courier(
    assign_data: OrderAssign,
    order_id: UUID = Path(description="ID of the order to assign courier"),
    authorize: AuthJWT = Depends(),
) -> OrderResponse:
    """Assign courier to order."""

    return await OrderService.assign_courier(order_id, assign_data.courier_id)


@router.post("/{order_id}/start", response_model=OrderResponse, summary="Start delivery")
async def start_delivery(
    order_id: UUID = Path(description="ID of the order to start delivery"), authorize: AuthJWT = Depends()
) -> OrderResponse:
    """Start order delivery."""

    return await OrderService.start_delivery(order_id)


@router.post("/{order_id}/complete", response_model=OrderResponse, summary="Complete delivery")
async def complete_delivery(
    completion_data: OrderDeliveryComplete,
    order_id: UUID = Path(description="ID of the order to complete delivery"),
    authorize: AuthJWT = Depends(),
) -> OrderResponse:
    """Complete order delivery."""

    return await OrderService.complete_delivery(
        order_id, completion_data.delivery_photo_url, completion_data.recipient_signature
    )


@router.post("/{order_id}/cancel", response_model=OrderResponse, summary="Cancel order")
async def cancel_order(
    order_id: UUID = Path(description="ID of the order to cancel"), authorize: AuthJWT = Depends()
) -> OrderResponse:
    """Cancel order."""

    return await OrderService.cancel_order(order_id)


@router.delete("/{order_id}", summary="Delete order")
async def delete_order(
    order_id: UUID = Path(description="ID of the order to delete"), authorize: AuthJWT = Depends()
) -> dict:
    """Delete order."""

    await OrderService.delete_order(order_id)
    return {"message": "Order successfully deleted"}
