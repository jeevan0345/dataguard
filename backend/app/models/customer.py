from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Customer(Base):

    customer_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(20)
    )

    address: Mapped[str] = mapped_column(
        String(255)
    )

    city: Mapped[str] = mapped_column(
        String(100)
    )

    state: Mapped[str] = mapped_column(
        String(100)
    )

    country: Mapped[str] = mapped_column(
        String(100)
    )

    postal_code: Mapped[str] = mapped_column(
        String(20)
    )

    loyalty_points: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # One Customer -> Many Orders
    orders = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan"
    )