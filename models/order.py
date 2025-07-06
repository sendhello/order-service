import uuid
from datetime import datetime, date, time
from enum import Enum
from typing import Self

from db.postgres import Base, async_session
from sqlalchemy import Column, String, DateTime, Text, select, ForeignKey, Boolean, Float, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .mixins import CRUDMixin, IDMixin


class OrderStatus(str, Enum):
    """Статусы заказа."""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryServiceLevel(str, Enum):
    """Уровни сервиса доставки."""
    STANDARD = "standard"
    EXPRESS = "express"


class PackageType(str, Enum):
    """Типы посылок."""
    BOX = "box"
    PACKAGE = "package"
    ENVELOPE = "envelope"
    OTHER = "other"


class ContentType(str, Enum):
    """Типы содержимого."""
    LETTER = "letter"
    FOOD = "food"
    GROCERY = "grocery"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    OTHER = "other"


class PaymentMethod(str, Enum):
    """Методы оплаты."""
    PREPAID = "prepaid"
    CASH_ON_DELIVERY = "cash_on_delivery"
    CARD = "card"


class PackageDetails(Base, IDMixin, CRUDMixin):
    """Детали посылки."""

    __tablename__ = "package_details"

    type = Column(String(20), default=PackageType.PACKAGE, nullable=False)
    content_type = Column(String(20), default=ContentType.OTHER, nullable=False)
    description = Column(Text, nullable=True)
    length = Column(Float, nullable=True)  # в см
    width = Column(Float, nullable=True)   # в см
    height = Column(Float, nullable=True)  # в см
    weight = Column(Float, nullable=True)  # в кг
    is_fragile = Column(Boolean, default=False, nullable=False)


class Parties(Base, IDMixin, CRUDMixin):
    """Стороны (отправитель и получатель)."""

    __tablename__ = "parties"

    company = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    additional = Column(Text, nullable=True)


class DeliveryWindow(Base, IDMixin, CRUDMixin):
    """Временное окно доставки."""

    __tablename__ = "delivery_windows"

    date = Column(Date, nullable=False)
    time_from = Column(Time, nullable=True)
    time_to = Column(Time, nullable=True)


class Payment(Base, IDMixin, CRUDMixin):
    """Информация об оплате."""

    __tablename__ = "payments"

    method = Column(String(20), default=PaymentMethod.PREPAID, nullable=False)
    sum = Column(Float, nullable=False)


class Order(Base, IDMixin, CRUDMixin):
    """Модель заказа."""

    __tablename__ = "orders"

    # Основная информация о заказе
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=OrderStatus.CREATED, nullable=False)
    source = Column(String(100), nullable=True)
    delivery_service_level = Column(String(20), default=DeliveryServiceLevel.STANDARD, nullable=False)
    tracking_id = Column(UUID, default=lambda: str(uuid.uuid4()), nullable=False, unique=True)
    insurance_number = Column(String(100), nullable=True)
    special_instructions = Column(Text, nullable=True)
    additional = Column(Text, nullable=True)

    # Связи с другими таблицами
    package_details_id = Column(UUID, ForeignKey('package_details.id'), nullable=True)
    sender_id = Column(UUID, ForeignKey('parties.id'), nullable=True)
    recipient_id = Column(UUID, ForeignKey('parties.id'), nullable=False)
    delivery_window_id = Column(UUID, ForeignKey('delivery_windows.id'), nullable=True)
    payment_id = Column(UUID, ForeignKey('payments.id'), nullable=True)

    # Информация о доставке
    courier_id = Column(UUID, nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    # Подтверждение доставки
    delivery_photo_url = Column(String(500), nullable=True)
    recipient_signature = Column(Text, nullable=True)

    # Relationships
    package_details = relationship("PackageDetails", backref="orders")
    sender = relationship("Parties", foreign_keys=[sender_id], backref="sent_orders")
    recipient = relationship("Parties", foreign_keys=[recipient_id], backref="received_orders")
    delivery_window = relationship("DeliveryWindow", backref="orders")
    payment = relationship("Payment", backref="orders")

    def __init__(
        self,
        title: str,
        recipient_id: uuid.UUID,
        description: str = None,
        source: str = None,
        delivery_service_level: str = DeliveryServiceLevel.STANDARD,
        package_details_id: uuid.UUID = None,
        sender_id: uuid.UUID = None,
        delivery_window_id: uuid.UUID = None,
        payment_id: uuid.UUID = None,
        insurance_number: str = None,
        special_instructions: str = None,
        additional: str = None,
    ) -> None:
        self.title = title
        self.description = description
        self.source = source
        self.delivery_service_level = delivery_service_level
        self.package_details_id = package_details_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.delivery_window_id = delivery_window_id
        self.payment_id = payment_id
        self.insurance_number = insurance_number
        self.special_instructions = special_instructions
        self.additional = additional

    @classmethod
    async def get_by_tracking_id(cls, tracking_id: uuid.UUID) -> Self:
        """Получить заказ по tracking ID."""
        async with async_session() as session:
            request = select(cls).where(cls.tracking_id == tracking_id)
            result = await session.execute(request)
            order = result.scalars().first()
        return order

    @classmethod
    async def get_by_status(cls, status: OrderStatus, page: int = 1, page_size: int = 20) -> list[Self]:
        """Получить заказы по статусу."""
        async with async_session() as session:
            request = (
                select(cls)
                .where(cls.status == status)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            orders = result.scalars().all()
        return orders

    @classmethod
    async def get_by_courier(cls, courier_id: UUID, page: int = 1, page_size: int = 20) -> list[Self]:
        """Получить заказы курьера."""
        async with async_session() as session:
            request = (
                select(cls)
                .where(cls.courier_id == courier_id)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            orders = result.scalars().all()
        return orders

    async def assign_courier(self, courier_id: UUID, commit: bool = True) -> bool:
        """Назначить курьера на заказ."""
        self.courier_id = courier_id
        self.status = OrderStatus.ASSIGNED
        self.assigned_at = datetime.utcnow()
        return await self.save(commit=commit)

    async def start_delivery(self, commit: bool = True) -> bool:
        """Начать доставку."""
        self.status = OrderStatus.IN_PROGRESS
        return await self.save(commit=commit)

    async def complete_delivery(
        self, 
        delivery_photo_url: str = None, 
        recipient_signature: str = None, 
        commit: bool = True
    ) -> bool:
        """Завершить доставку."""
        self.status = OrderStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
        if delivery_photo_url:
            self.delivery_photo_url = delivery_photo_url
        if recipient_signature:
            self.recipient_signature = recipient_signature
        return await self.save(commit=commit)

    async def cancel_order(self, commit: bool = True) -> bool:
        """Отменить заказ."""
        self.status = OrderStatus.CANCELLED
        return await self.save(commit=commit)

    def __repr__(self) -> str:
        return f"<Order {self.tracking_id}>"
