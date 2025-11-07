from fastapi import UploadFile
import pandas as pd

from app.controllers.crud import upsert_customer, upsert_order, insert_items
from app.utils.utils import normalize_str, parse_date_any, basic_email_check, VALID_STATUS, VALID_SHIPPING, is_empty
from app.models.models import OrderItem
from sqlalchemy.orm import Session
from typing import Tuple, Dict, List, Any

EXPECTED_COLS = [
  "order_id", "order_date", "customer_id", "customer_name", "customer_email",
  "phone", "address_line", "city", "state", "country", "postal_code",
  "status", "shipping_method", "coupon_code",
  "item_sku_1", "item_qty_1", "item_price_1",
  "item_sku_2", "item_qty_2", "item_price_2"
]

def read_excel_file(upload_file):
  if isinstance(upload_file, str):
    return pd.read_excel(upload_file, engine="openpyxl", dtype=object)
  else:
    return pd.read_excel(upload_file.file, engine="openpyxl", dtype=object)

def validate_and_normalize_row(row: pd.Series, row_num: int) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
  errors = []

  def val(col): return row.get(col, None) if col in row.index else None

  # Normalización básica
  order_id = val("order_id")
  customer_name = normalize_str(val("customer_name"))
  customer_email = normalize_str(val("customer_email"))
  status = normalize_str(val("status"))
  shipping_method = normalize_str(val("shipping_method"))
  order_date = parse_date_any(val("order_date"))

  # Validaciones mínimas requeridas
  if is_empty(order_id):
    errors.append({"sheet": None, "row": row_num, "field": "order_id", "message": "order_id missing", "value": order_id})

  if is_empty(customer_name):
    errors.append({"sheet": None, "row": row_num, "field": "customer_name", "message": "customer_name missing", "value": customer_name})

  if not basic_email_check(customer_email):
    errors.append({"sheet": None, "row": row_num, "field": "customer_email", "message": "invalid email format", "value": customer_email})

  if not is_empty(status) and status.lower() not in VALID_STATUS:
    errors.append({"sheet": None, "row": row_num, "field": "status", "message": f"invalid status (allowed: {','.join(VALID_STATUS)})", "value": status})

  if not is_empty(shipping_method) and shipping_method.lower() not in VALID_SHIPPING:
    errors.append({"sheet": None, "row": row_num, "field": "shipping_method", "message": f"invalid shipping_method (allowed: {','.join(VALID_SHIPPING)})", "value": shipping_method})

  # Items: se aceptan vacíos o incompletos
  items = []
  item_sku = normalize_str(val("item_sku"))
  quantity = val("quantity")

  if not is_empty(item_sku) or not is_empty(quantity):
    try:
      quantity_v = int(quantity) if not is_empty(quantity) else None
    except Exception:
      quantity_v = None

    if is_empty(item_sku):
      errors.append({"sheet": None, "row": row_num, "field": "item_sku", "message": "item sku missing", "value": item_sku})
    if quantity_v is None or quantity_v <= 0:
      errors.append({"sheet": None, "row": row_num, "field": "quantity", "message": "qty must be > 0", "value": quantity})

    if item_sku and quantity_v and quantity_v > 0:
      items.append({
        "sku": item_sku,
        "qty": quantity_v,
        "unit_price": 0.0,
        "line_total": 0.0
      })

  customer = {
    "name": customer_name,
    "email": customer_email
  }

  order = {
    "order_id": int(order_id) if not is_empty(order_id) else None,
    "order_date": order_date,
    "status": status.lower() if status else None,
    "shipping_method": shipping_method.lower() if shipping_method else None
  }

  return customer, order, items, errors

def ingest_file(upload_file: UploadFile, db: Session):
  df = read_excel_file(upload_file)
  # verify columns
  missing = [c for c in EXPECTED_COLS if c not in df.columns]
  if missing:
    raise ValueError(f"Missing expected columns: {missing}")

  rows_read = len(df)
  errors = []
  inserted_customers = inserted_orders = inserted_items = 0
  updated_customers = updated_orders = 0

  # Start outer transaction so DB remains consistent
  with db.begin():
    for idx, row in df.iterrows():
      row_num = int(idx) + 2  # approximate Excel row (header + 1)
      # create nested transaction (savepoint) per row
      with db.begin_nested():
        cust, order, items, row_errors = validate_and_normalize_row(row, row_num)
        if row_errors:
          errors.extend(row_errors)
          # rollback this savepoint by raising an exception and catching below, or just rollback:
          # we rollback by explicitly rolling back the nested transaction
          # but using begin_nested + context manager will roll back on exception
          # so we can simply skip DB work for rows with errors
          continue

        # upsert customer and order and insert items
        try:
          # UPSERT customer
          upsert_customer(db, cust)
          # upsert order
          upsert_order(db, order)
          # remove existing items for the order to avoid duplicates (idempotency)
          db.query(OrderItem).filter(OrderItem.order_id == order["order_id"]).delete()
          # insert items
          for it in items:
            it_record = {
              "order_id": order["order_id"],
              "sku": it["sku"],
              "qty": it["qty"],
              "unit_price": it["unit_price"],
              "line_total": it["line_total"]
            }
            db.add(OrderItem(**it_record))
            inserted_items += 1
          inserted_customers += 0  # we can't reliably decide insert vs update with merge
          inserted_orders += 1
        except Exception as e:
          # record DB level error for this row and rollback nested by re-raising
          errors.append({"sheet": None, "row": row_num, "field": None, "message": f"DB error: {str(e)}", "value": None})
          # re-raise to ensure savepoint rollback
          raise

  summary = {
    "rows_read": rows_read,
    "inserted_customers": inserted_customers,
    "inserted_orders": inserted_orders,
    "inserted_items": inserted_items,
    "updated_customers": updated_customers,
    "updated_orders": updated_orders,
    "errors": errors
  }
  return summary
