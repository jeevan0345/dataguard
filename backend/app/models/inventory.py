from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Inventory(Base):

    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )

    warehouse_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    available_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    minimum_stock: Mapped[int] = mapped_column(
        Integer,
        default=10
    )

    maximum_stock: Mapped[int] = mapped_column(
        Integer,
        default=1000
    )

    product = relationship(
        "Product",
        back_populates="inventories"
    )

    warehouse = relationship(
        "Warehouse",
        back_populates="inventories"
    )