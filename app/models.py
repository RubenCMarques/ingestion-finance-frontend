# app/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Date

from .database import Base



# ---------- LOOKUP / DIM TABLES ----------

class MovementType(Base):
    __tablename__ = "movement_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # "Expense", "Income"

    # backref: transactions = relationship("Transaction", back_populates="movement_type")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # "Restaurante", ...

    # Opcional: category_type = "expense"/"income"/"both"
    # type_scope = Column(String(20), nullable=True)


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # "MBWay", "Card", ...


class ProductType(Base):
    __tablename__ = "product_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # "Ação", "ETF", "Cripto", ...


# ---------- FACT TABLES ----------

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # DATE YOU SELECT IN THE FORM
    transaction_date = Column(Date, nullable=False)

    # DATE THE ROW WAS INSERTED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # instead of type="Expense"/"Income", we point to a movement_types row
    movement_type_id = Column(Integer, ForeignKey("movement_types.id"), nullable=False)
    movement_type = relationship("MovementType")

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="EUR")

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category")

    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"), nullable=True)
    payment_method = relationship("PaymentMethod")

    source = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)

    investment_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticker = Column(String(50), nullable=False)     # ex: AAPL, VWCE, BTC

    product_type_id = Column(Integer, ForeignKey("product_types.id"), nullable=False)
    product_type = relationship("ProductType")

    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    total_value = Column(Numeric(12, 2), nullable=False)

    currency = Column(String(10), nullable=False, default="EUR")
    notes = Column(String(500), nullable=True)
