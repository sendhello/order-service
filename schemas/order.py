from datetime import datetime, date, time
from typing import Optional
from uuid import UUID

from pydantic import Field, validator

from .base import Model
from .mixins import IdMixin


class OrderStatus:
    """Статусы заказа."""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryServiceLevel:
    """Уровни сервиса доставки."""
    STANDARD = "standard"
    EXPRESS = "express"


class PackageType:
    """Типы посылок."""
    BOX = "box"
    PACKAGE = "package"
    ENVELOPE = "envelope"
    OTHER = "other"


class ContentType:
    """Типы содержимого."""
    LETTER = "letter"
    FOOD = "food"
    GROCERY = "grocery"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    OTHER = "other"


class PaymentMethod:
    """Методы оплаты."""
    PREPAID = "prepaid"
    CASH_ON_DELIVERY = "cash_on_delivery"
    CARD = "card"


# Schemas for new models
class PackageDetailsBase(Model):
    """Базовая модель деталей посылки."""
    type: str = Field(default=PackageType.PACKAGE, description="Тип посылки")
    content_type: str = Field(default=ContentType.OTHER, description="Тип содержимого")
    description: Optional[str] = Field(None, description="Описание")
    length: Optional[float] = Field(None, description="Длина в см")
    width: Optional[float] = Field(None, description="Ширина в см")
    height: Optional[float] = Field(None, description="Высота в см")
    weight: Optional[float] = Field(None, description="Вес в кг")
    is_fragile: bool = Field(default=False, description="Хрупкое")


class PackageDetailsCreate(PackageDetailsBase):
    """Модель для создания деталей посылки."""
    pass


class PackageDetailsResponse(PackageDetailsBase, IdMixin):
    """Модель деталей посылки для ответа."""
    pass


class PartiesBase(Model):
    """Базовая модель стороны (отправитель/получатель)."""
    company: Optional[str] = Field(None, description="Компания")
    first_name: str = Field(..., description="Имя")
    last_name: str = Field(..., description="Фамилия")
    address: str = Field(..., description="Адрес")
    phone: str = Field(..., description="Телефон")
    email: Optional[str] = Field(None, description="Email")
    additional: Optional[str] = Field(None, description="Дополнительная информация")


class PartiesCreate(PartiesBase):
    """Модель для создания стороны."""
    pass


class PartiesResponse(PartiesBase, IdMixin):
    """Модель стороны для ответа."""
    pass


class DeliveryWindowBase(Model):
    """Базовая модель временного окна доставки."""
    date: date = Field(..., description="Дата")
    time_from: Optional[time] = Field(None, description="Время с")
    time_to: Optional[time] = Field(None, description="Время до")


class DeliveryWindowCreate(DeliveryWindowBase):
    """Модель для создания временного окна доставки."""
    pass


class DeliveryWindowResponse(DeliveryWindowBase, IdMixin):
    """Модель временного окна доставки для ответа."""
    pass


class PaymentBase(Model):
    """Базовая модель оплаты."""
    method: str = Field(default=PaymentMethod.PREPAID, description="Метод оплаты")
    sum: float = Field(..., description="Сумма")


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

    @validator('status')
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
