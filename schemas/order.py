from datetime import datetime, date, time
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from .base import Model
from .mixins import IdMixin
from constants.order import PackageType, ContentType, OrderStatus, DeliveryServiceLevel, PaymentMethod


# Schemas for new models
class PackageDetailsBase(Model):
    """Base package details model."""

    type: str = Field(default=PackageType.PACKAGE, description="Package type")
    content_type: str = Field(default=ContentType.OTHER, description="Content type")
    description: Optional[str] = Field(None, description="Description")
    length: Optional[float] = Field(None, description="Length in cm")
    width: Optional[float] = Field(None, description="Width in cm")
    height: Optional[float] = Field(None, description="Height in cm")
    weight: Optional[float] = Field(None, description="Weight in kg")
    is_fragile: bool = Field(default=False, description="Fragile")


class PackageDetailsCreate(PackageDetailsBase):
    """Model for creating package details."""

    pass


class PackageDetailsResponse(PackageDetailsBase, IdMixin):
    """Package details response model."""

    pass


class PartiesBase(Model):
    """Base party model (sender/recipient)."""

    company: Optional[str] = Field(None, description="Company")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    address: str = Field(..., description="Address")
    phone: str = Field(..., description="Phone")
    email: Optional[str] = Field(None, description="Email")
    additional: Optional[str] = Field(None, description="Additional information")


class PartiesCreate(PartiesBase):
    """Model for creating party."""

    pass


class PartiesResponse(PartiesBase, IdMixin):
    """Party response model."""

    pass


class DeliveryWindowBase(Model):
    """Base delivery window model."""

    date: date = Field(..., description="Date")
    time_from: Optional[time] = Field(None, description="Time from")
    time_to: Optional[time] = Field(None, description="Time to")


class DeliveryWindowCreate(DeliveryWindowBase):
    """Model for creating delivery window."""

    pass


class DeliveryWindowResponse(DeliveryWindowBase, IdMixin):
    """Delivery window response model."""

    pass


class PaymentBase(Model):
    """Base payment model."""

    method: str = Field(default=PaymentMethod.PREPAID, description="Payment method")
    sum: float = Field(..., description="Amount")


class PaymentCreate(PaymentBase):
    """Модель для создания оплаты."""

    pass


class PaymentResponse(PaymentBase, IdMixin):
    """Модель оплаты для ответа."""

    pass


class BaseOrder(Model):
    """Базовая модель заказа."""

    title: str = Field(..., description="Название заказа")
    description: Optional[str] = Field(None, description="Описание заказа")


class OrderCreate(BaseOrder):
    """Модель для создания заказа."""

    source: Optional[str] = Field(None, description="Источник заказа")
    delivery_service_level: str = Field(default=DeliveryServiceLevel.STANDARD, description="Уровень сервиса доставки")
    insurance_number: Optional[str] = Field(None, description="Номер страховки")
    special_instructions: Optional[str] = Field(None, description="Специальные инструкции")
    additional: Optional[str] = Field(None, description="Дополнительная информация")

    # Related objects data
    package_details: Optional[PackageDetailsCreate] = Field(None, description="Детали посылки")
    sender: Optional[PartiesCreate] = Field(None, description="Отправитель")
    recipient: PartiesCreate = Field(..., description="Получатель")
    delivery_window: Optional[DeliveryWindowCreate] = Field(None, description="Временное окно доставки")
    payment: Optional[PaymentCreate] = Field(None, description="Информация об оплате")


class OrderUpdate(Model):
    """Модель для обновления заказа."""

    title: Optional[str] = Field(None, description="Название заказа")
    description: Optional[str] = Field(None, description="Описание заказа")
    source: Optional[str] = Field(None, description="Источник заказа")
    delivery_service_level: Optional[str] = Field(None, description="Уровень сервиса доставки")
    insurance_number: Optional[str] = Field(None, description="Номер страховки")
    special_instructions: Optional[str] = Field(None, description="Специальные инструкции")
    additional: Optional[str] = Field(None, description="Дополнительная информация")


class OrderResponse(BaseOrder, IdMixin):
    """Модель заказа для ответа."""

    status: str = Field(..., description="Статус заказа")
    source: Optional[str] = Field(None, description="Источник заказа")
    delivery_service_level: str = Field(..., description="Уровень сервиса доставки")
    tracking_id: UUID = Field(..., description="ID отслеживания")
    insurance_number: Optional[str] = Field(None, description="Номер страховки")
    special_instructions: Optional[str] = Field(None, description="Специальные инструкции")
    additional: Optional[str] = Field(None, description="Дополнительная информация")

    # Related objects
    package_details: Optional[PackageDetailsResponse] = Field(None, description="Детали посылки")
    sender: Optional[PartiesResponse] = Field(None, description="Отправитель")
    recipient: Optional[PartiesResponse] = Field(None, description="Получатель")
    delivery_window: Optional[DeliveryWindowResponse] = Field(None, description="Временное окно доставки")
    payment: Optional[PaymentResponse] = Field(None, description="Информация об оплате")

    # Delivery info
    courier_id: Optional[UUID] = Field(None, description="ID курьера")
    assigned_at: Optional[datetime] = Field(None, description="Время назначения курьера")
    delivered_at: Optional[datetime] = Field(None, description="Время доставки")
    delivery_photo_url: Optional[str] = Field(None, description="URL фото доставки")
    recipient_signature: Optional[str] = Field(None, description="Подпись получателя")


class OrderInDB(OrderResponse):
    """Модель заказа в БД."""

    pass


class OrderAssign(Model):
    """Модель для назначения курьера."""

    courier_id: UUID = Field(..., description="ID курьера")


class OrderDeliveryComplete(Model):
    """Модель для завершения доставки."""

    delivery_photo_url: Optional[str] = Field(None, description="URL фото доставки")
    recipient_signature: Optional[str] = Field(None, description="Подпись получателя")


class OrderStatusUpdate(Model):
    """Модель для обновления статуса заказа."""

    status: str = Field(..., description="Новый статус заказа")

    @field_validator('status')
    def validate_status(cls, v):
        valid_statuses = [
            OrderStatus.CREATED,
            OrderStatus.ASSIGNED,
            OrderStatus.IN_PROGRESS,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED
        ]
        if v not in valid_statuses:
            raise ValueError(f'Недопустимый статус. Допустимые значения: {", ".join(valid_statuses)}')
        return v


class OrderList(Model):
    """Модель для списка заказов."""

    orders: list[OrderResponse] = Field(..., description="Список заказов")
    total: int = Field(..., description="Общее количество заказов")
    page: int = Field(..., description="Номер страницы")
    page_size: int = Field(..., description="Размер страницы")
