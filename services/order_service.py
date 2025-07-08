import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status
from constants.order import PackageType, PaymentMethod, ContentType
from models.order import Order, OrderStatus, PackageDetail, Party, DeliveryWindow
from schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderList, PackageDetailsResponse, DeliveryWindowResponse
from sqlalchemy.exc import IntegrityError


class OrderService:
    """Service for working with orders."""

    @staticmethod
    async def create_order(order_data: OrderCreate) -> OrderResponse:
        """Create a new order."""

        sender = None
        if order_data.sender:
            sender = await Party.create(**order_data.sender.model_dump())

        recipient = await Party.create(**order_data.recipient.model_dump())

        order_db = await Order.create(
            **order_data.model_dump(exclude={'sender', 'recipient', 'package_details', 'delivery_window'}, exclude_none=True),
            sender_id=sender.id if sender is not None else None,
            recipient_id=recipient.id,
        )

        package_details_db = []
        for package_detail in order_data.package_details:
            package_details_db.append(
                PackageDetail.create(
                    **package_detail.model_dump(),
                    order_id=order_db.id,
                )
            )

        delivery_windows_db = []
        for delivery_window in order_data.delivery_windows:
            delivery_windows_db.append(
                DeliveryWindow.create(
                    **delivery_window.model_dump(),
                    order_id=order_db.id,
                )
            )

        order = OrderResponse.model_validate(order_db, from_attributes=True)
        order.package_details = [PackageDetailsResponse.model_validate(package_detail_db, from_attributes=True) for package_detail_db in package_details_db]
        order.delivery_windows = [DeliveryWindowResponse.model_validate(delivery_window_db, from_attributes=True) for delivery_window_db in delivery_windows_db]
        return order

    @staticmethod
    async def get_order_by_id(order_id: UUID) -> OrderResponse:
        """Get order by ID."""

        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return OrderResponse(order)

    @staticmethod
    async def get_order_by_tracking_id(tracking_id: UUID) -> OrderResponse:
        """Get order by tracking ID."""

        order = await Order.get_by_tracking_id(tracking_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return OrderResponse(order)

    @staticmethod
    async def get_orders(
        page: int = 1, 
        page_size: int = 20, 
        status: OrderStatus | None = None,
        courier_id: UUID | None = None
    ) -> OrderList:
        """Get list of orders with filtering."""

        if status:
            orders = await Order.get_by_status(status, page, page_size)
        elif courier_id:
            orders = await Order.get_by_courier(courier_id, page, page_size)
        else:
            orders = await Order.get_all(page, page_size)

        total = await Order.total_count()

        order_responses = [
            OrderResponse.model_validate(order, from_attributes=True) for order in orders
        ]

        return OrderList(
            orders=order_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    @staticmethod
    async def update_order(order_id: UUID, order_data: OrderUpdate) -> OrderResponse:
        """Update order."""

        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail="Cannot edit delivered or cancelled order"
            )

        # Update only provided fields
        update_data = order_data.model_dump(exclude_unset=True)
        order = await order.update(**update_data)

        return OrderResponse.model_validate(order, from_attributes=True)

    @staticmethod
    async def assign_courier(order_id: UUID, courier_id: UUID) -> OrderResponse:
        """Assign a courier to order."""

        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.CREATED:
            raise HTTPException(
                status_code=400, 
                detail="Can only assign courier to order with 'created' status"
            )

        order = await order.assign_courier(courier_id)
        return OrderResponse.model_validate(order, from_attributes=True)

    @staticmethod
    async def start_delivery(order_id: UUID) -> OrderResponse:
        """Start order delivery."""

        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.ASSIGNED:
            raise HTTPException(
                status_code=400, 
                detail="Can only start delivery for assigned order"
            )

        await order.start_delivery()
        return OrderResponse.model_validate(order, from_attributes=True)

    @staticmethod
    async def complete_delivery(
        order_id: UUID, 
        delivery_photo_url: Optional[str] = None,
        recipient_signature: Optional[str] = None
    ) -> OrderResponse:
        """Complete order delivery."""

        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400, 
                detail="Can only complete order that is in progress"
            )

        await order.complete_delivery(delivery_photo_url, recipient_signature)
        return OrderResponse.model_validate(order, from_attributes=True)

    @staticmethod
    async def cancel_order(order_id: UUID) -> OrderResponse:
        """Cancel order."""

        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail="Cannot cancel delivered or already cancelled order"
            )

        await order.cancel_order()
        return OrderResponse.model_validate(order, from_attributes=True)

    @staticmethod
    async def delete_order(order_id: UUID) -> bool:
        """Delete order."""

        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status not in [OrderStatus.CREATED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail="Can only delete created or cancelled order"
            )

        await order.delete()
        return True
