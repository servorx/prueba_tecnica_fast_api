from sqlalchemy import Column, BigInteger, String, Date, Numeric, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.config.db import Base

# los modelos de la base de datos representan las tablas de la base de datos con ORM
class Customer(Base):
  __tablename__ = "customers"
  __table_args__ = {"extend_existing": True}  # permite extender tablas existentes sin errores
  customer_id = Column(BigInteger, primary_key=True)
  name = Column(String(180), nullable=False)
  email = Column(String(180))
  phone = Column(String(40))
  address_line = Column(String(255))
  city = Column(String(120))
  state = Column(String(120))
  country = Column(String(120))
  postal_code = Column(String(20))

  orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

class Order(Base):
  __tablename__ = "orders"
  __table_args__ = {"extend_existing": True}  # permite extender tablas existentes sin errores
  order_id = Column(BigInteger, primary_key=True)
  order_date = Column(Date, nullable=False)
  customer_id = Column(BigInteger, ForeignKey("customers.customer_id"), nullable=False)
  status = Column(String(16), nullable=False)
  shipping_method = Column(String(16))
  coupon_code = Column(String(40))

  customer = relationship("Customer", back_populates="orders")
  items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
  __tablename__ = "order_items"
  __table_args__ = {"extend_existing": True}  # permite extender tablas existentes sin errores

  id = Column(BigInteger, primary_key=True, autoincrement=True)
  order_id = Column(BigInteger, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
  sku = Column(String(40), nullable=False)
  qty = Column(Integer, nullable=False)
  unit_price = Column(Numeric(12,2), nullable=False)
  line_total = Column(Numeric(12,2), nullable=False)

  order = relationship("Order", back_populates="items")
