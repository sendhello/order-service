import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from db.postgres import async_session
from models.order import TimeWindow, Order, OrderStatus, PackageDetail, Party
from schemas.order import (
    TimeWindowResponse,
    OrderCreate,
    OrderList,
    OrderResponse,
    OrderUpdate,
    PackageDetailsResponse,
    PartyCreate,
    PartyResponse,
)


logger = logging.getLogger(__name__)


class OrderService:
    """Service for working with orders."""

    def __init__(self):
        """Initialize the OrderService."""

        self.model = Order

    @staticmethod
    async def _get_or_update_party(party_data: PartyCreate, session) -> Party:
        """Get or update a party based on provided data."""

        party = await Party.get_one_by_filter(
            phone=party_data.phone,
            address=party_data.address,
            first_name=party_data.first_name,
            last_name=party_data.last_name,
        )
        if party:
            party.company = party_data.company
            party.email = party_data.email
            party.additional = party_data.additional
        else:
            party = Party(**party_data.model_dump())
            session.add(party)
            await session.flush()

        return party

    async def create_order(self, order_data: OrderCreate) -> OrderResponse:
        """Create a new order."""

        async with async_session() as session:
            sender = None
            if order_data.sender:
                sender = await self._get_or_update_party(order_data.sender, session)

            recipient = await self._get_or_update_party(order_data.recipient, session)

            order_db = self.model(
                **order_data.model_dump(
                    exclude={"sender", "recipient", "package_details", "time_windows"}, exclude_none=True
                ),
                sender_id=sender.id if sender is not None else None,
                recipient_id=recipient.id,
            )
            session.add(order_db)
            await session.flush()

            package_details_db = []
            for package_detail in order_data.package_details:
                package_detail_db = PackageDetail(
                    **package_detail.model_dump(),
                    order_id=order_db.id,
                )
                session.add(package_detail_db)
                package_details_db.append(package_detail_db)

            time_windows_db = []
            for time_window in order_data.time_windows:
                time_window_db = TimeWindow(
                    **time_window.model_dump(),
                    order_id=order_db.id,
                )
                session.add(time_window_db)
                time_windows_db.append(time_window_db)

            await session.commit()
            await session.refresh(order_db)

            # Преобразуем в Pydantic модель
            order_response = OrderResponse(
                id=order_db.id,
                title=order_db.title,
                description=order_db.description,
                status=order_db.status,
                source=order_db.source,
                delivery_service_level=order_db.delivery_service_level,
                tracking_id=order_db.tracking_id,
                payment_method=order_db.payment_method,
                payment_status=order_db.payment_status,
                payment_amount=order_db.payment_amount,
                insurance_number=order_db.insurance_number,
                special_instructions=order_db.special_instructions,
                additional=order_db.additional,
                sender=PartyResponse.model_validate(sender, from_attributes=True) if sender else None,
                recipient=PartyResponse.model_validate(recipient, from_attributes=True),
                package_details=[
                    PackageDetailsResponse.model_validate(pkg, from_attributes=True) for pkg in package_details_db
                ],
                time_windows=[
                    TimeWindowResponse.model_validate(win, from_attributes=True) for win in time_windows_db
                ],
                courier_id=order_db.courier_id,
                assigned_at=order_db.assigned_at,
                delivered_at=order_db.delivered_at,
                delivery_photo_url=order_db.delivery_photo_url,
                recipient_signature=order_db.recipient_signature,
            )

        return order_response

    async def get_order_by_id(self, order_id: UUID) -> OrderResponse:
        """Get order by ID."""

        order = await self.model.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return OrderResponse.model_validate(order, from_attributes=True)

    async def get_order_by_tracking_id(self, tracking_id: UUID) -> OrderResponse:
        """Get order by tracking ID."""

        order = await self.model.get_by_tracking_id(tracking_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return OrderResponse.model_validate(order, from_attributes=True)

    async def get_orders(
        self, page: int = 1, page_size: int = 20, status: OrderStatus | None = None, courier_id: UUID | None = None
    ) -> OrderList:
        """Get list of orders with filtering."""

        if status and courier_id:
            orders = await self.model.get_by_status_and_courier(status, courier_id, page, page_size)
        elif status:
            orders = await self.model.get_by_status(status, page, page_size)
        elif courier_id:
            orders = await self.model.get_by_courier(courier_id, page, page_size)
        else:
            orders = await self.model.get_all(page, page_size)

        total = await self.model.total_count()

        order_responses = [OrderResponse.model_validate(order, from_attributes=True) for order in orders]

        return OrderList(orders=order_responses, total=total, page=page, page_size=page_size)

    async def update_order(self, order_id: UUID, order_data: OrderUpdate) -> OrderResponse:
        """Update order."""

        order = await self.model.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Cannot edit delivered or cancelled order")

        # Update only provided fields
        update_data = order_data.model_dump(exclude_unset=True)
        order = await order.update(**update_data)

        return OrderResponse.model_validate(order, from_attributes=True)

    async def assign_courier(self, order_id: UUID, courier_id: UUID) -> OrderResponse:
        """Assign a courier to order."""

        order = await self.model.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.CREATED:
            raise HTTPException(status_code=400, detail="Can only assign courier to order with 'created' status")

        order = await order.assign_courier(courier_id)
        return OrderResponse.model_validate(order, from_attributes=True)

    async def start_delivery(self, order_id: UUID) -> OrderResponse:
        """Start order delivery."""

        order = await self.model.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.ASSIGNED:
            raise HTTPException(status_code=400, detail="Can only start delivery for assigned order")

        await order.start_delivery()
        return OrderResponse.model_validate(order, from_attributes=True)

    async def complete_delivery(
        self, order_id: UUID, delivery_photo_url: Optional[str] = None, recipient_signature: Optional[str] = None
    ) -> OrderResponse:
        """Complete order delivery."""

        order = await self.model.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Can only complete order that is in progress")

        await order.complete_delivery(delivery_photo_url, recipient_signature)
        return OrderResponse.model_validate(order, from_attributes=True)

    async def cancel_order(self, order_id: UUID) -> OrderResponse:
        """Cancel order."""

        order = await self.model.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Cannot cancel delivered or already cancelled order")

        await order.cancel_order()
        return OrderResponse.model_validate(order, from_attributes=True)

    async def delete_order(self, order_id: UUID) -> bool:
        """Delete order."""

        order = await self.model.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status not in [OrderStatus.CREATED, OrderStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Can only delete created or cancelled order")

        await order.delete()
        return True


order_service = OrderService()
