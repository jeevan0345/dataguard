from sqlalchemy import Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Employee(Base):

    employee_code: Mapped[str] = mapped_column(
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

    department: Mapped[str] = mapped_column(
        String(100)
    )

    designation: Mapped[str] = mapped_column(
        String(100)
    )

    salary: Mapped[float] = mapped_column(
        Float
    )

    hire_date: Mapped[Date] = mapped_column(
        Date
    )

    manager_name: Mapped[str] = mapped_column(
        String(100)
    )