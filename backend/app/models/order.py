from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums.order_status import OrderStatus


class Order(Base):

    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False
    )

    order_date: Mapped[date] = mapped_column(
        Date
    )

    total_amount: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    order_status: Mapped[str] = mapped_column(
        String(50),
        default=OrderStatus.PENDING.value
    )

    payment_status: Mapped[str] = mapped_column(
        String(50),
        default="Pending"
    )

    customer = relationship(
        "Customer",
        back_populates="orders"
    )

    order_items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    payment = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )

    shipment = relationship(
        "Shipment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )