from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums.payment_status import PaymentStatus


class Payment(Base):

    payment_reference: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False
    )

    payment_method: Mapped[str] = mapped_column(
        String(50)
    )

    payment_status: Mapped[str] = mapped_column(
        String(50),
        default=PaymentStatus.PENDING.value
    )

    amount: Mapped[float] = mapped_column(
        Float
    )

    payment_date: Mapped[date] = mapped_column(
        Date
    )

    transaction_id: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    order = relationship(
        "Order",
        back_populates="payment"
    )