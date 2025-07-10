import uuid
from datetime import datetime, timezone
from typing import Self

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Time,
    select,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import joinedload, relationship

from constants.order import ContentType, DeliveryServiceLevel, OrderStatus, PackageType, PaymentMethod
from db.postgres import Base, async_session

from .mixins import CRUDMixin, IDMixin


class PackageDetail(Base, IDMixin, CRUDMixin):
    """Package details."""

    __tablename__ = "package_details"

    type = Column(Enum(PackageType, name="package_type", native_enum=True), default=PackageType.PACKAGE, nullable=False)
    content_type = Column(
        Enum(ContentType, name="content_type", native_enum=True), default=ContentType.OTHER, nullable=False
    )
    description = Column(Text, nullable=True)
    length = Column(Float, nullable=True)  # in cm
    width = Column(Float, nullable=True)  # in cm
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    is_fragile = Column(Boolean, default=False, nullable=False)

    order_id = Column(UUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    order = relationship("Order", back_populates="package_details")


class Party(Base, IDMixin, CRUDMixin):
    """Party (sender and recipient)."""

    __tablename__ = "parties"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company = Column(String(255), nullable=True)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    additional = Column(Text, nullable=True)

    sent_orders = relationship("Order", foreign_keys="Order.sender_id", back_populates="sender")
    received_orders = relationship("Order", foreign_keys="Order.recipient_id", back_populates="recipient")

    __table_args__ = (
        Index("ix_parties_address", "address"),
        Index("ix_parties_company", "company"),
        Index("uq_parties_phone", "phone", unique=True),
    )


class DeliveryWindow(Base, IDMixin, CRUDMixin):
    """Delivery time window."""

    __tablename__ = "delivery_windows"

    day = Column(Date, nullable=False)
    time_from = Column(Time, nullable=True)
    time_to = Column(Time, nullable=True)

    order_id = Column(UUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    order = relationship("Order", back_populates="delivery_windows")


class Order(Base, IDMixin, CRUDMixin):
    """Order model."""

    __tablename__ = "orders"

    # Main order information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(OrderStatus, name="order_status", native_enum=True), default=OrderStatus.CREATED, nullable=False
    )
    source = Column(String(100), nullable=True)
    delivery_service_level = Column(
        Enum(DeliveryServiceLevel, name="delivery_service_level", native_enum=True),
        default=DeliveryServiceLevel.STANDARD,
        nullable=False,
    )
    tracking_id = Column(UUID, default=lambda: str(uuid.uuid4()), nullable=False, unique=True)
    payment_method = Column(
        Enum(PaymentMethod, name="payment_method", native_enum=True),
        default=PaymentMethod.CASH_ON_DELIVERY,
        nullable=False,
    )
    payment_status = Column(Boolean, default=False, nullable=False)
    payment_amount = Column(Numeric(10, 2), nullable=True)
    insurance_number = Column(String(100), nullable=True)
    special_instructions = Column(Text, nullable=True)
    additional = Column(Text, nullable=True)

    # Relations with other tables
    sender_id = Column(UUID, ForeignKey("parties.id", ondelete="RESTRICT"), nullable=True)
    recipient_id = Column(UUID, ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False)

    # Delivery information
    courier_id = Column(UUID, nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Delivery confirmation
    delivery_photo_url = Column(String(500), nullable=True)
    recipient_signature = Column(Text, nullable=True)

    # Relationships
    sender = relationship("Party", foreign_keys=[sender_id], back_populates="sent_orders")
    recipient = relationship("Party", foreign_keys=[recipient_id], back_populates="received_orders")
    package_details = relationship("PackageDetail", back_populates="order", passive_deletes=True)
    delivery_windows = relationship("DeliveryWindow", back_populates="order", passive_deletes=True)

    __table_args__ = (Index("ix_orders_courier_id", "courier_id"),)

    def __init__(
        self,
        title: str,
        recipient_id: uuid.UUID,
        description: str = None,
        source: str = None,
        delivery_service_level: str = DeliveryServiceLevel.STANDARD,
        sender_id: uuid.UUID = None,
        payment_method: str = PaymentMethod.CASH_ON_DELIVERY,
        payment_status: bool = False,
        payment_amount: float = None,
        insurance_number: str = None,
        special_instructions: str = None,
        additional: str = None,
    ) -> None:
        self.title = title
        self.description = description
        self.source = source
        self.delivery_service_level = delivery_service_level
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.payment_amount = payment_amount
        self.insurance_number = insurance_number
        self.special_instructions = special_instructions
        self.additional = additional

    @classmethod
    def _get_dependency_field_options(cls) -> tuple:
        return (
            joinedload(cls.sender),
            joinedload(cls.recipient),
            joinedload(cls.package_details),
            joinedload(cls.delivery_windows),
        )

    @classmethod
    async def get_by_tracking_id(cls, tracking_id: uuid.UUID) -> Self:
        """Get order by tracking ID."""

        async with async_session() as session:
            request = select(cls).options(*cls._get_dependency_field_options()).where(cls.tracking_id == tracking_id)
            result = await session.execute(request)
            order = result.scalars().unique().first()
        return order

    @classmethod
    async def get_by_status(cls, status: OrderStatus, page: int = 1, page_size: int = 20) -> list[Self]:
        """Get orders by status."""

        async with async_session() as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .where(cls.status == status)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            orders = result.scalars().unique().all()
        return orders

    @classmethod
    async def get_by_courier(cls, courier_id: UUID, page: int = 1, page_size: int = 20) -> list[Self]:
        """Get courier orders."""

        async with async_session() as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .where(cls.courier_id == courier_id)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            orders = result.scalars().all()
        return orders

    @classmethod
    async def get_by_status_and_courier(
        cls, status: OrderStatus, courier_id: UUID, page: int = 1, page_size: int = 20
    ) -> list[Self]:
        """Get courier orders in a status."""

        async with async_session() as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .where(cls.courier_id == courier_id)
                .where(cls.status == status)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            orders = result.scalars().all()
        return orders

    @classmethod
    async def get_all(cls, page: int = 1, page_size: int = 20) -> list[Self]:
        async with async_session() as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            entities = result.scalars().unique().all()

        return entities

    @classmethod
    async def get_by_id(cls, id_: UUID) -> Self:
        async with async_session() as session:
            request = select(cls).options(*cls._get_dependency_field_options()).where(cls.id == id_)
            result = await session.execute(request)
            entity = result.scalars().unique().first()

        return entity

    async def assign_courier(self, courier_id: UUID, commit: bool = True) -> bool:
        """Assign a courier to order."""

        self.courier_id = courier_id
        self.status = OrderStatus.ASSIGNED
        self.assigned_at = datetime.now(timezone.utc)
        return await self.save(commit=commit)

    async def start_delivery(self, commit: bool = True) -> bool:
        """Start delivery."""

        self.status = OrderStatus.IN_PROGRESS
        return await self.save(commit=commit)

    async def complete_delivery(
        self, delivery_photo_url: str = None, recipient_signature: str = None, commit: bool = True
    ) -> bool:
        """Complete delivery."""

        self.status = OrderStatus.DELIVERED
        self.delivered_at = datetime.now(timezone.utc)
        if delivery_photo_url:
            self.delivery_photo_url = delivery_photo_url
        if recipient_signature:
            self.recipient_signature = recipient_signature
        return await self.save(commit=commit)

    async def cancel_order(self, commit: bool = True) -> bool:
        """Cancel order."""

        self.status = OrderStatus.CANCELLED
        return await self.save(commit=commit)

    def __repr__(self) -> str:
        return f"<Order {self.tracking_id}>"
