import pandas as pd
from typing import Tuple, Dict, List, Any
from app.utils.utils import (
  normalize_str, parse_date_any, basic_email_check,
  VALID_STATUS, VALID_SHIPPING, is_empty
)

def validate_and_normalize_row(row: pd.Series, row_num: int) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
  # Valida y normaliza una fila del DataFrame.
  # Devuelve tuplas con los datos de cliente, orden, items y errores.
  errors = []

  def val(col):
    return row[col] if col in row else None

  # Normalización
  order_id = val("order_id")
  customer_name = normalize_str(val("customer_name"))
  customer_email = normalize_str(val("customer_email"))
  status = normalize_str(val("status"))
  shipping_method = normalize_str(val("shipping_method"))
  order_date = parse_date_any(val("order_date"))

  # Validaciones mínimas
  if is_empty(order_id):
    errors.append({
      "row": row_num,
      "field": "order_id",
      "message": "order_id missing"
    })
  if is_empty(customer_name):
    errors.append({
      "row": row_num,
      "field": "customer_name",
      "message": "customer_name missing"
    })

  # Validación del email (solo si existe)
  if not is_empty(customer_email) and not basic_email_check(customer_email):
    errors.append({
      "row": row_num,
      "field": "customer_email",
      "message": "invalid email format"
    })
  # Validación de status y shipping
  if not is_empty(status) and status.lower() not in VALID_STATUS:
    errors.append({
      "row": row_num,
      "field": "status",
      "message": f"invalid status (allowed: {', '.join(VALID_STATUS)})"
    })
  if not is_empty(shipping_method) and shipping_method.lower() not in VALID_SHIPPING:
    errors.append({
      "row": row_num,
      "field": "shipping_method",
      "message": f"invalid shipping_method (allowed: {', '.join(VALID_SHIPPING)})"
    })

  # --- Validación de items ---
  items = []
  item_sku = normalize_str(val("item_sku"))
  quantity = val("quantity")

  # Permitir filas sin items (no se consideran error)
  if not is_empty(item_sku) or not is_empty(quantity):
    try:
      quantity_v = int(quantity) if not is_empty(quantity) else None
    except Exception:
      quantity_v = None

  # Validar items solo si uno de los dos campos está presente
  if not is_empty(item_sku) or not is_empty(quantity):
    try:
      quantity_v = int(quantity) if not is_empty(quantity) else None
    except Exception:
      quantity_v = None

    # Caso: hay cantidad pero no SKU
    if is_empty(item_sku) and not is_empty(quantity):
      errors.append({
        "row": row_num,
        "field": "item_sku",
        "message": "item sku missing"
      })

    # Caso: hay SKU pero cantidad inválida
    if not is_empty(item_sku) and (quantity_v is None or quantity_v <= 0):
      errors.append({
        "row": row_num,
        "field": "quantity",
        "message": "qty must be > 0"
      })

    # Solo si ambos están presentes correctamente, agregamos el item
    if not is_empty(item_sku) and quantity_v and quantity_v > 0:
      items.append({
        "sku": item_sku,
        "qty": quantity_v,
        "unit_price": 0.0,
        "line_total": 0.0
      })

    if item_sku and quantity_v and quantity_v > 0:
      items.append({
        "sku": item_sku,
        "qty": quantity_v,
        "unit_price": 0.0,
        "line_total": 0.0
      })

  # objetos normalizados 
  customer = {
    "name": customer_name,
    "email": customer_email
  }

  order = {
    "order_id": int(order_id) if not is_empty(order_id) else None,
    "order_date": order_date,
    "status": status.lower() if status else None,
    "shipping_method": shipping_method.lower() if shipping_method else None,
    "customer_id": None
  }

  return customer, order, items, errors
