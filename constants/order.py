from enum import StrEnum


class OrderStatus(StrEnum):
    """Статусы заказа."""

    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryServiceLevel(StrEnum):
    """Уровни сервиса доставки."""

    STANDARD = "standard"
    EXPRESS = "express"


class PackageType(StrEnum):
    """Типы посылок."""

    BOX = "box"
    PACKAGE = "package"
    ENVELOPE = "envelope"
    OTHER = "other"


class ContentType(StrEnum):
    """Типы содержимого."""

    LETTER = "letter"
    FOOD = "food"
    GROCERY = "grocery"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    OTHER = "other"


class PaymentMethod(StrEnum):
    """Методы оплаты."""

    PREPAID = "prepaid"
    CASH_ON_DELIVERY = "cash_on_delivery"
    CARD_ON_DELIVERY = "card_on_delivery"
