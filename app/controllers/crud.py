from sqlalchemy.orm import Session
from app.models.models import Customer, Order, OrderItem
from datetime import date

def upsert_customer(session: Session, customer_obj: dict):
  existing = None
  # buscar por email si existe
  if customer_obj.get("email"):
    existing = session.query(Customer).filter(Customer.email == customer_obj["email"]).first()
  # si no tiene email, buscar por nombre
  elif customer_obj.get("name"):
    existing = session.query(Customer).filter(Customer.name == customer_obj["name"]).first()

  if existing:
    # Actualizamos datos
    for k, v in customer_obj.items():
      setattr(existing, k, v)
    session.flush()
    return existing  # ya tiene customer_id
  else:
    # Insertamos nuevo
    instance = Customer(**customer_obj)
    session.add(instance)
    # enviar datos de forma temporal
    session.flush() 
    return instance

def upsert_order(session: Session, order_obj: dict):
  instance = Order(**order_obj)
  merged = session.merge(instance)
  session.flush()
  return merged

def insert_items(session: Session, items_objs: list):
  inserted = []
  for it in items_objs:
    oi = OrderItem(**it)
    session.add(oi)
    inserted.append(oi)
  session.flush()
  return inserted
