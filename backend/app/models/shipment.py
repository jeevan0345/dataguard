from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums.shipment_status import ShipmentStatus


class Shipment(Base):

    shipment_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False
    )

    carrier: Mapped[str] = mapped_column(
        String(100)
    )

    tracking_number: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    shipment_status: Mapped[str] = mapped_column(
        String(50),
        default=ShipmentStatus.PREPARING.value
    )

    shipped_date: Mapped[date] = mapped_column(
        Date
    )

    delivered_date: Mapped[date] = mapped_column(
        Date
    )

    order = relationship(
        "Order",
        back_populates="shipment"
    )