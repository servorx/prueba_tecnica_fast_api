# imports de librerías y dependencias
import pandas as pd
from typing import Tuple, Dict, List, Any
# imports de módulos internos (validaciones)
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
  phone = normalize_str(val("phone"))
  address_line = normalize_str(val("address_line")) 
  city = normalize_str(val("city")) 
  state = normalize_str(val("state")) 
  country = normalize_str(val("country")) 
  postal_code = normalize_str(val("postal_code"))
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
  # Validar nombre del cliente
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
  # Validar método de envío
  if not is_empty(shipping_method) and shipping_method.lower() not in VALID_SHIPPING:
    errors.append({
      "row": row_num,
      "field": "shipping_method",
      "message": f"invalid shipping_method (allowed: {', '.join(VALID_SHIPPING)})"
    })
  # validaciones de fecha
  if order_date is None:
    errors.append({
      "row": row_num,
      "field": "order_date",
      "message": "order_date missing"
    })
  # --- Normalizar cliente y orden ---
  customer = {
    "name": customer_name,
    "email": customer_email,
    "phone": phone,
    "address_line": address_line,
    "city": city,
    "state": state,
    "country": country,
    "postal_code": postal_code
  }
  order = {
    "order_id": int(order_id) if not is_empty(order_id) else None,
    "order_date": order_date,
    "status": status.lower() if status else None,
    "shipping_method": shipping_method.lower() if shipping_method else None,
    "customer_id": None,
    "coupon_code": normalize_str(val("coupon_code"))
  }
  # --- Validación y normalización de items ---
  items = []
  # soporte para múltiples columnas de items si existieran: item_sku_1, item_qty_1, etc.
  item_columns = [c for c in row.index if "item_sku" in c]
  for sku_col in item_columns:
    suffix = sku_col.split("item_sku")[-1]  # "_1", "_2", etc.
    qty_col = f"item_qty{suffix}"
    price_col = f"item_price{suffix}"

    sku = normalize_str(val(sku_col))
    qty = val(qty_col)
    price = val(price_col)

    if is_empty(sku) and not is_empty(qty):
      errors.append({"row": row_num, "field": sku_col, "message": "item sku missing"})
    if not is_empty(sku):
      try:
        qty_v = int(qty) if not is_empty(qty) else None
      except Exception:
        qty_v = None
      if qty_v is None or qty_v <= 0:
        errors.append({"row": row_num, "field": qty_col, "message": "qty must be > 0"})
      else:
        items.append({
          "sku": sku,
          "qty": qty_v,
          "unit_price": float(price) if not is_empty(price) else 0.0,
          "line_total": (float(price) * qty_v) if not is_empty(price) else 0.0
        })

  return customer, order, items, errors