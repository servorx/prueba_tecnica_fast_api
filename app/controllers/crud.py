from sqlalchemy.orm import Session
from app.models.models import Customer, Order, OrderItem
from datetime import date

def upsert_customer(session: Session, customer_obj: dict):
    instance = Customer(**customer_obj)
    merged = session.merge(instance)
    # flush to get DB to apply
    session.flush()
    # Can't easily tell insert vs update here; for metrics we'll treat merge as upsert and track heuristically
    return merged

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
