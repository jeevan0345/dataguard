from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Product(Base):

    product_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(1000)
    )

    category: Mapped[str] = mapped_column(
        String(100)
    )

    brand: Mapped[str] = mapped_column(
        String(100)
    )

    price: Mapped[float] = mapped_column(
        Float
    )

    cost_price: Mapped[float] = mapped_column(
        Float
    )

    reorder_level: Mapped[int] = mapped_column(
        Integer,
        default=10
    )

    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id")
    )

    supplier = relationship(
        "Supplier",
        back_populates="products"
    )

    inventories = relationship(
        "Inventory",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    order_items = relationship(
        "OrderItem",
        back_populates="product"
    )