from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Warehouse(Base):

    warehouse_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    warehouse_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
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

    manager_name: Mapped[str] = mapped_column(
        String(150)
    )

    capacity: Mapped[int] = mapped_column(
        Integer
    )

    current_utilization: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    inventories = relationship(
        "Inventory",
        back_populates="warehouse",
        cascade="all, delete-orphan"
    )