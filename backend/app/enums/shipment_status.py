from enum import Enum


class ShipmentStatus(str, Enum):
    PREPARING = "Preparing"
    DISPATCHED = "Dispatched"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"