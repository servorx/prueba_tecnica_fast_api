from sqlalchemy.orm import Session
from app.models.models import Customer, Order, OrderItem
from datetime import date

# funciones para insertar o actualizar registros en la base de datos
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

# esta función actualiza un registro de orden en la base de datos
def upsert_order(session: Session, order_obj: dict):
  instance = Order(**order_obj)
  # hacer un merge para actualizar el registro si existe pero no lo guarda
  merged = session.merge(instance)
  # guardar los cambios en la base de datos sin hacer commit
  session.flush()
  # retornar el registro actualizado
  return merged
