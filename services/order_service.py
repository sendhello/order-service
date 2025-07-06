import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from models.order import Order, OrderStatus, PackageDetails, Parties, DeliveryWindow, Payment
from schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderList
from sqlalchemy.exc import IntegrityError


class OrderService:
    """Сервис для работы с заказами."""

    @staticmethod
    async def create_order(order_data: OrderCreate) -> OrderResponse:
        """Создание нового заказа."""
        try:
            # Create related objects first
            package_details_id = None
            if order_data.package_details:
                package_details = await PackageDetails.create(**order_data.package_details.dict())
                package_details_id = package_details.id

            sender_id = None
            if order_data.sender:
                sender = await Parties.create(**order_data.sender.dict())
                sender_id = sender.id

            recipient = await Parties.create(**order_data.recipient.dict())
            recipient_id = recipient.id

            delivery_window_id = None
            if order_data.delivery_window:
                delivery_window = await DeliveryWindow.create(**order_data.delivery_window.dict())
                delivery_window_id = delivery_window.id

            payment_id = None
            if order_data.payment:
                payment = await Payment.create(**order_data.payment.dict())
                payment_id = payment.id

            # Create the order
            order = await Order.create(
                title=order_data.title,
                description=order_data.description,
                source=order_data.source,
                delivery_service_level=order_data.delivery_service_level,
                insurance_number=order_data.insurance_number,
                special_instructions=order_data.special_instructions,
                additional=order_data.additional,
                package_details_id=package_details_id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                delivery_window_id=delivery_window_id,
                payment_id=payment_id,
            )

            return await OrderService._build_order_response(order)

        except IntegrityError:
            raise HTTPException(status_code=400, detail="Ошибка при создании заказа")

    @staticmethod
    async def _build_order_response(order: Order) -> OrderResponse:
        """Построение ответа с загруженными связанными объектами."""
        # Load related objects
        package_details = None
        if order.package_details_id:
            package_details = await PackageDetails.get_by_id(order.package_details_id)

        sender = None
        if order.sender_id:
            sender = await Parties.get_by_id(order.sender_id)

        recipient = None
        if order.recipient_id:
            recipient = await Parties.get_by_id(order.recipient_id)

        delivery_window = None
        if order.delivery_window_id:
            delivery_window = await DeliveryWindow.get_by_id(order.delivery_window_id)

        payment = None
        if order.payment_id:
            payment = await Payment.get_by_id(order.payment_id)

        # Build response
        order_dict = {
            "id": order.id,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "title": order.title,
            "description": order.description,
            "status": order.status,
            "source": order.source,
            "delivery_service_level": order.delivery_service_level,
            "tracking_id": order.tracking_id,
            "insurance_number": order.insurance_number,
            "special_instructions": order.special_instructions,
            "additional": order.additional,
            "courier_id": order.courier_id,
            "assigned_at": order.assigned_at,
            "delivered_at": order.delivered_at,
            "delivery_photo_url": order.delivery_photo_url,
            "recipient_signature": order.recipient_signature,
            "package_details": package_details.__dict__ if package_details else None,
            "sender": sender.__dict__ if sender else None,
            "recipient": recipient.__dict__ if recipient else None,
            "delivery_window": delivery_window.__dict__ if delivery_window else None,
            "payment": payment.__dict__ if payment else None,
        }

        return OrderResponse(**order_dict)

    @staticmethod
    async def get_order_by_id(order_id: UUID) -> OrderResponse:
        """Получение заказа по ID."""
        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        return await OrderService._build_order_response(order)

    @staticmethod
    async def get_order_by_tracking_id(tracking_id: UUID) -> OrderResponse:
        """Получение заказа по tracking ID."""
        order = await Order.get_by_tracking_id(tracking_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        return await OrderService._build_order_response(order)

    @staticmethod
    async def get_orders(
        page: int = 1, 
        page_size: int = 20, 
        status: Optional[str] = None,
        courier_id: Optional[UUID] = None
    ) -> OrderList:
        """Получение списка заказов с фильтрацией."""
        if status:
            if status not in [OrderStatus.CREATED, OrderStatus.ASSIGNED, OrderStatus.IN_PROGRESS, 
                            OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
                raise HTTPException(status_code=400, detail="Недопустимый статус заказа")
            orders = await Order.get_by_status(status, page, page_size)
        elif courier_id:
            orders = await Order.get_by_courier(courier_id, page, page_size)
        else:
            orders = await Order.get_all(page, page_size)

        # Подсчет общего количества (упрощенная версия)
        total = len(orders) if len(orders) < page_size else (page * page_size)

        order_responses = []
        for order in orders:
            order_response = await OrderService._build_order_response(order)
            order_responses.append(order_response)

        return OrderList(
            orders=order_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    @staticmethod
    async def update_order(order_id: UUID, order_data: OrderUpdate) -> OrderResponse:
        """Обновление заказа."""
        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        # Проверяем, что заказ можно редактировать
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail="Нельзя редактировать доставленный или отмененный заказ"
            )

        # Обновляем только переданные поля
        update_data = order_data.dict(exclude_unset=True)
        await order.update(**update_data)

        return await OrderService._build_order_response(order)

    @staticmethod
    async def assign_courier(order_id: UUID, courier_id: UUID) -> OrderResponse:
        """Назначение курьера на заказ."""
        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.status != OrderStatus.CREATED:
            raise HTTPException(
                status_code=400, 
                detail="Можно назначить курьера только на заказ со статусом 'создан'"
            )

        await order.assign_courier(courier_id)
        return await OrderService._build_order_response(order)

    @staticmethod
    async def start_delivery(order_id: UUID) -> OrderResponse:
        """Начало доставки заказа."""
        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.status != OrderStatus.ASSIGNED:
            raise HTTPException(
                status_code=400, 
                detail="Можно начать доставку только назначенного заказа"
            )

        await order.start_delivery()
        return await OrderService._build_order_response(order)

    @staticmethod
    async def complete_delivery(
        order_id: UUID, 
        delivery_photo_url: Optional[str] = None,
        recipient_signature: Optional[str] = None
    ) -> OrderResponse:
        """Завершение доставки заказа."""
        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.status != OrderStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400, 
                detail="Можно завершить только заказ в процессе доставки"
            )

        await order.complete_delivery(delivery_photo_url, recipient_signature)
        return await OrderService._build_order_response(order)

    @staticmethod
    async def cancel_order(order_id: UUID) -> OrderResponse:
        """Отмена заказа."""
        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail="Нельзя отменить доставленный или уже отмененный заказ"
            )

        await order.cancel_order()
        return await OrderService._build_order_response(order)

    @staticmethod
    async def delete_order(order_id: UUID) -> bool:
        """Удаление заказа."""
        order = await Order.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.status not in [OrderStatus.CREATED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail="Можно удалить только созданный или отмененный заказ"
            )

        await order.delete()
        return True
