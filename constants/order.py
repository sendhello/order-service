from enum import StrEnum


class OrderType(StrEnum):
    """Order types."""

    PICKUP = "pickup"
    DELIVERY = "delivery"
    SERVICE = "service"


class OrderStatus(StrEnum):
    """Order statuses."""

    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryServiceLevel(StrEnum):
    """Delivery service levels."""

    STANDARD = "standard"
    EXPRESS = "express"


class PackageType(StrEnum):
    """Package types."""

    BOX = "box"
    PACKAGE = "package"
    ENVELOPE = "envelope"
    OTHER = "other"


class ContentType(StrEnum):
    """Content types."""

    LETTER = "letter"
    FOOD = "food"
    GROCERY = "grocery"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    OTHER = "other"


class PaymentMethod(StrEnum):
    """Payment methods."""

    PREPAID = "prepaid"
    CASH_ON_DELIVERY = "cash_on_delivery"
    CARD_ON_DELIVERY = "card_on_delivery"
