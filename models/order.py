import uuid
from datetime import UTC, datetime
from typing import Self

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Double,
    Enum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import joinedload, relationship

from constants import DEFAULT_ORG_ID
from constants.order import ContentType, DeliveryServiceLevel, OrderStatus, OrderType, PackageType, PaymentMethod
from db.postgres import Base, get_session

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

    org_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    order = relationship("Order", back_populates="package_details")

    __table_args__ = (UniqueConstraint("org_id", "order_id", name="uq_org_order_package_detail"),)


class Party(Base, IDMixin, CRUDMixin):
    """Party (sender and recipient)."""

    __tablename__ = "parties"

    # Multi-tenancy
    org_id = Column(UUID(as_uuid=True), nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company = Column(String(255), nullable=True)
    address = Column(Text, nullable=False)
    lon = Column(Double, nullable=False)
    lat = Column(Double, nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    additional = Column(Text, nullable=True)

    sent_orders = relationship("Order", foreign_keys="Order.sender_id", back_populates="sender")
    received_orders = relationship("Order", foreign_keys="Order.recipient_id", back_populates="recipient")

    __table_args__ = (
        Index("ix_org_parties_address", "org_id", "address"),
        Index("ix_org_parties_company", "org_id", "company"),
        UniqueConstraint("org_id", "phone", "address", "first_name", "last_name", name="uq_org_parties_unique"),
    )

    @classmethod
    async def get_by_filter(
        cls,
        phone: str,
        address: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        current_org: str = DEFAULT_ORG_ID,
    ) -> list[Self]:
        """Get parties by phone and optional filters."""

        async with get_session(current_org) as session:
            request = select(cls).where(cls.phone == phone)
            if address is not None:
                request = request.where(cls.address == address)
            if first_name is not None:
                request = request.where(cls.first_name == first_name)
            if last_name is not None:
                request = request.where(cls.last_name == last_name)

            result = await session.execute(request)
            return result.scalars().all()

    @classmethod
    async def get_one_by_filter(
        cls,
        phone: str,
        address: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        current_org: str = DEFAULT_ORG_ID,
    ) -> list[Self]:
        """Get party by phone and optional filters."""

        async with get_session(current_org) as session:
            request = select(cls).where(cls.phone == phone)
            if address is not None:
                request = request.where(cls.address == address)
            if first_name is not None:
                request = request.where(cls.first_name == first_name)
            if last_name is not None:
                request = request.where(cls.last_name == last_name)

            result = await session.execute(request)
            return result.scalars().first()


class TimeWindow(Base, IDMixin, CRUDMixin):
    """Delivery time window."""

    __tablename__ = "time_windows"

    day = Column(Date, nullable=False)
    time_from = Column(Time, nullable=True)
    time_to = Column(Time, nullable=True)

    org_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    order = relationship("Order", back_populates="time_windows")

    __table_args__ = (Index("ix_org_order_time_window", "org_id", "order_id"),)


class Order(Base, IDMixin, CRUDMixin):
    """Order model."""

    __tablename__ = "orders"

    # Multi-tenancy
    org_id = Column(UUID(as_uuid=True), nullable=False)

    # Main order information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(OrderType, name="order_type", native_enum=True), default=OrderType.SERVICE, nullable=False)
    status = Column(
        Enum(OrderStatus, name="order_status", native_enum=True), default=OrderStatus.CREATED, nullable=False
    )
    source = Column(String(100), nullable=True)
    delivery_service_level = Column(
        Enum(DeliveryServiceLevel, name="delivery_service_level", native_enum=True),
        default=DeliveryServiceLevel.STANDARD,
        nullable=False,
    )
    tracking_id = Column(UUID, default=lambda: str(uuid.uuid4()), nullable=False)
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
    time_windows = relationship("TimeWindow", back_populates="order", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("org_id", "tracking_id", name="uq_org_tracking_id"),
        Index("ix_org_orders_courier_id", "org_id", "courier_id"),
        Index("ix_org_orders_status", "org_id", "status"),
    )

    def __init__(
        self,
        title: str,
        recipient_id: uuid.UUID,
        org_id: uuid.UUID,
        description: str | None = None,
        source: str | None = None,
        delivery_service_level: str = DeliveryServiceLevel.STANDARD,
        sender_id: uuid.UUID | None = None,
        payment_method: str = PaymentMethod.CASH_ON_DELIVERY,
        payment_status: bool = False,
        payment_amount: float | None = None,
        insurance_number: str | None = None,
        special_instructions: str | None = None,
        additional: str | None = None,
    ) -> None:
        self.org_id = org_id
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
            joinedload(cls.time_windows),
        )

    @classmethod
    async def get_by_tracking_id(cls, tracking_id: uuid.UUID, current_org: str = DEFAULT_ORG_ID) -> Self:
        """Get order by tracking ID."""

        async with get_session(current_org) as session:
            request = select(cls).options(*cls._get_dependency_field_options()).where(cls.tracking_id == tracking_id)
            result = await session.execute(request)
            return result.scalars().unique().first()

    @classmethod
    async def get_by_status(
        cls, status: OrderStatus, page: int = 1, page_size: int = 20, current_org: str = DEFAULT_ORG_ID
    ) -> tuple[list[Self], int]:
        """Get orders by status."""

        async with get_session(current_org) as session:
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

            # Count total number
            total_query = select(func.count(cls.id)).where(cls.status == status)
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return orders, total

    @classmethod
    async def get_by_courier(
        cls, courier_id: UUID, page: int = 1, page_size: int = 20, current_org: str = DEFAULT_ORG_ID
    ) -> tuple[list[Self], int]:
        """Get courier orders."""

        async with get_session(current_org) as session:
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

            # Count total number
            total_query = select(func.count(cls.id)).where(cls.courier_id == courier_id)
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return orders, total

    @classmethod
    async def get_by_status_and_courier(
        cls,
        status: OrderStatus,
        courier_id: UUID,
        page: int = 1,
        page_size: int = 20,
        current_org: str = DEFAULT_ORG_ID,
    ) -> tuple[list[Self], int]:
        """Get courier orders in a status."""

        async with get_session(current_org) as session:
            orders_query = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .where(cls.courier_id == courier_id)
                .where(cls.status == status)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            orders_result = await session.execute(orders_query)
            orders = orders_result.scalars().all()

            # Count total number
            total_query = select(func.count(cls.id)).where(cls.courier_id == courier_id).where(cls.status == status)
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return orders, total

    @classmethod
    async def get_all(
        cls, page: int = 1, page_size: int = 20, current_org: str = DEFAULT_ORG_ID
    ) -> tuple[list[Self], int]:
        async with get_session(current_org) as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            entities = result.scalars().unique().all()

            # Count total number
            total_query = select(func.count(cls.id))
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return entities, total

    @classmethod
    async def get_by_id(cls, id_: UUID, current_org: str = DEFAULT_ORG_ID) -> Self:
        async with get_session(current_org) as session:
            request = select(cls).options(*cls._get_dependency_field_options()).where(cls.id == id_)
            result = await session.execute(request)
            return result.scalars().unique().first()

    async def assign_courier(self, courier_id: UUID, commit: bool = True, current_org: str = DEFAULT_ORG_ID) -> bool:
        """Assign a courier to order."""

        self.courier_id = courier_id
        self.status = OrderStatus.ASSIGNED
        self.assigned_at = datetime.now(UTC)
        return await self.save(commit=commit, current_org=current_org)

    async def start_delivery(self, commit: bool = True, current_org: str = DEFAULT_ORG_ID) -> bool:
        """Start delivery."""

        self.status = OrderStatus.IN_PROGRESS
        return await self.save(commit=commit, current_org=current_org)

    async def complete_delivery(
        self,
        delivery_photo_url: str | None = None,
        recipient_signature: str | None = None,
        commit: bool = True,
        current_org: str = DEFAULT_ORG_ID,
    ) -> bool:
        """Complete delivery."""

        self.status = OrderStatus.DELIVERED
        self.delivered_at = datetime.now(UTC)
        if delivery_photo_url:
            self.delivery_photo_url = delivery_photo_url
        if recipient_signature:
            self.recipient_signature = recipient_signature
        return await self.save(commit=commit, current_org=current_org)

    async def cancel_order(self, commit: bool = True, current_org: str = DEFAULT_ORG_ID) -> bool:
        """Cancel order."""

        self.status = OrderStatus.CANCELLED
        return await self.save(commit=commit, current_org=current_org)

    def __repr__(self) -> str:
        return f"<Order {self.tracking_id}>"
