from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Supplier(Base):

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    contact_person: Mapped[str] = mapped_column(
        String(150),
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

    supplier_rating: Mapped[int] = mapped_column(
        default=5
    )

    gst_number: Mapped[str] = mapped_column(
        String(50),
        unique=True
    )

    website: Mapped[str] = mapped_column(
        String(255)
    )

    # One Supplier → Many Products
    products = relationship(
        "Product",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )