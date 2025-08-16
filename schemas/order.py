from datetime import date, datetime, time, timezone
import zoneinfo
from decimal import Decimal
from uuid import UUID

from pydantic import Field
from core.settings import settings
from constants.order import ContentType, DeliveryServiceLevel, OrderStatus, PackageType, PaymentMethod, OrderType

from .base import Model
from .mixins import IdMixin


# Schemas for new models
class PackageDetailsBase(Model):
    """Base package details model."""

    type: PackageType = Field(default=PackageType.PACKAGE, description="Package type")
    content_type: ContentType = Field(default=ContentType.LETTER, description="Content type")
    description: str | None = Field(None, description="Description")
    length: float | None = Field(None, description="Length in cm")
    width: float | None = Field(None, description="Width in cm")
    height: float | None = Field(None, description="Height in cm")
    weight: float | None = Field(None, description="Weight in kg")
    is_fragile: bool = Field(default=False, description="Fragile")


class PackageDetailsCreate(PackageDetailsBase):
    """Model for creating package details."""

    pass


class PackageDetailsResponse(PackageDetailsBase, IdMixin):
    """Package details response model."""

    pass


class PartyBase(Model):
    """Base party model (sender/recipient)."""

    company: str | None = Field(None, description="Company")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    address: str = Field(..., description="Address")
    lon: float = Field(..., description="Longitude")
    lat: float = Field(..., description="Latitude")
    phone: str = Field(..., description="Phone")
    email: str | None = Field(None, description="Email")
    additional: str | None = Field(None, description="Additional information")


class PartyCreate(PartyBase):
    """Model for creating party."""

    pass


class PartyResponse(PartyBase, IdMixin):
    """Party response model."""

    pass


class TimeWindowBase(Model):
    """Base delivery window model."""

    day: date = Field(default_factory=lambda: datetime.now(tz=zoneinfo.ZoneInfo(settings.timezone)).date(), description="Date")
    time_from: time = Field(default_factory=lambda: time.min, description="Time from")
    time_to: time = Field(default_factory=lambda: time.max, description="Time to")


class TimeWindowCreate(TimeWindowBase):
    """Model for creating delivery window."""

    pass


class TimeWindowResponse(TimeWindowBase, IdMixin):
    """Delivery window response model."""

    pass


class PaymentBase(Model):
    """Base payment model."""

    method: str = Field(default=PaymentMethod.PREPAID, description="Payment method")
    sum: float = Field(..., description="Amount")


class PaymentCreate(PaymentBase):
    """Model for creating payment."""

    pass


class PaymentResponse(PaymentBase, IdMixin):
    """Payment response model."""

    pass


class BaseOrder(Model):
    """Base order model."""

    title: str = Field(..., description="Order title")
    description: str | None = Field(None, description="Order description")


class OrderCreate(BaseOrder):
    """Model for creating order."""

    source: str | None = Field(None, description="Order source")
    delivery_service_level: DeliveryServiceLevel = Field(default=DeliveryServiceLevel.STANDARD, description="Delivery service level")
    payment_method: str = Field(default=PaymentMethod.CASH_ON_DELIVERY, description="Payment method")
    payment_status: bool = Field(default=False, description="Payment status")
    payment_amount: Decimal | None = Field(None, description="Payment amount")
    insurance_number: str | None = Field(None, description="Insurance number")
    special_instructions: str | None = Field(None, description="Special instructions")
    additional: str | None = Field(None, description="Additional information")

    # Related objects data
    package_details: list[PackageDetailsCreate] | None = Field(None, description="Package details")
    sender: PartyCreate | None = Field(None, description="Sender")
    recipient: PartyCreate = Field(..., description="Recipient")
    time_windows: list[TimeWindowCreate] = Field(default_factory=list, description="Delivery time windows")


class OrderUpdate(Model):
    """Model for updating order."""

    title: str | None = Field(None, description="Order title")
    description: str | None = Field(None, description="Order description")
    source: str | None = Field(None, description="Order source")
    delivery_service_level: DeliveryServiceLevel = Field(default=DeliveryServiceLevel.STANDARD, description="Delivery service level")
    payment_method: str | None = Field(None, description="Payment method")
    payment_status: bool | None = Field(None, description="Payment status")
    payment_amount: Decimal | None = Field(None, description="Payment amount")
    insurance_number: str | None = Field(None, description="Insurance number")
    special_instructions: str | None = Field(None, description="Special instructions")
    additional: str | None = Field(None, description="Additional information")


class OrderResponse(BaseOrder, IdMixin):
    """Order response model."""

    type: OrderType = Field(..., description="Order type")
    status: OrderStatus = Field(..., description="Order status")
    source: str | None = Field(None, description="Order source")
    delivery_service_level: DeliveryServiceLevel = Field(default=DeliveryServiceLevel.STANDARD, description="Delivery service level")
    tracking_id: UUID = Field(..., description="Tracking ID")
    payment_method: str = Field(..., description="Payment method")
    payment_status: bool = Field(..., description="Payment status")
    payment_amount: Decimal | None = Field(None, description="Payment amount")
    insurance_number: str | None = Field(None, description="Insurance number")
    special_instructions: str | None = Field(None, description="Special instructions")
    additional: str | None = Field(None, description="Additional information")

    # Related objects
    sender: PartyResponse | None = Field(None, description="Sender")
    recipient: PartyResponse | None = Field(None, description="Recipient")
    package_details: list[PackageDetailsResponse] = Field(default_factory=list, description="Package details")
    time_windows: list[TimeWindowResponse] = Field(default_factory=list, description="Delivery time window")

    # Delivery info
    courier_id: UUID | None = Field(None, description="Courier ID")
    assigned_at: datetime | None = Field(None, description="Courier assignment time")
    delivered_at: datetime | None = Field(None, description="Delivery time")
    delivery_photo_url: str | None = Field(None, description="Delivery photo URL")
    recipient_signature: str | None = Field(None, description="Recipient signature")


class OrderInDB(OrderResponse):
    """Order model in database."""

    pass


class OrderAssign(Model):
    """Model for courier assignment."""

    courier_id: UUID = Field(..., description="Courier ID")


class OrderDeliveryComplete(Model):
    """Model for delivery completion."""

    delivery_photo_url: str | None = Field(None, description="Delivery photo URL")
    recipient_signature: str | None = Field(None, description="Recipient signature")


class OrderStatusUpdate(Model):
    """Model for order status update."""

    status: OrderStatus = Field(..., description="New order status")


class OrderList(Model):
    """Model for order list."""

    orders: list[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")
    page: int = Field(..., description="Page number")
    page_size: int = Field(..., description="Page size")
