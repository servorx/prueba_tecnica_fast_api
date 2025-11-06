from fastapi import UploadFile
import pandas as pd

from . import crud
from ..utils.utils import *
from .. import models
from sqlalchemy.orm import Session
from typing import Tuple, Dict, List, Any

EXPECTED_COLS = [
  "order_id", "order_date", "customer_id", "customer_name", "customer_email",
  "phone", "address_line", "city", "state", "country", "postal_code",
  "status", "shipping_method", "coupon_code",
  "item_sku_1", "item_qty_1", "item_price_1",
  "item_sku_2", "item_qty_2", "item_price_2"
]

def read_excel_file(upload_file: UploadFile) -> pd.DataFrame:
  # pandas handles file-like objects
  df = pd.read_excel(upload_file.file, engine="openpyxl", dtype=object)
  return df

def validate_and_normalize_row(row: pd.Series, row_num: int) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:  
  errors = []
  # map and normalize
  def val(col): return row.get(col, None) if col in row.index else None

  # basic normalization
  order_id = val("order_id")
  customer_id = val("customer_id")

  # Common transforms
  order_date = parse_date_any(val("order_date"))
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
  coupon_code = normalize_str(val("coupon_code"))

  # Validations
  if order_id is None:
    errors.append({"sheet": None, "row": row_num, "field": "order_id", "message": "order_id missing", "value": order_id})
  if order_date is None:
    errors.append({"sheet": None, "row": row_num, "field": "order_date", "message": "invalid or missing date", "value": str(val("order_date"))})
  if customer_id is None:
    errors.append({"sheet": None, "row": row_num, "field": "customer_id", "message": "customer_id missing", "value": customer_id})
  if customer_name is None:
    errors.append({"sheet": None, "row": row_num, "field": "customer_name", "message": "customer_name missing", "value": customer_name})

  # status check
  if status is None or status.lower() not in VALID_STATUS:
    errors.append({"sheet": None, "row": row_num, "field": "status", "message": f"invalid status (allowed: {','.join(VALID_STATUS)})", "value": status})

  # shipping check
  if shipping_method and shipping_method.lower() not in VALID_SHIPPING:
    errors.append({"sheet": None, "row": row_num, "field": "shipping_method", "message": f"invalid shipping_method (allowed: {','.join(VALID_SHIPPING)})", "value": shipping_method})

  # email check
  if not basic_email_check(customer_email):
    errors.append({"sheet": None, "row": row_num, "field": "customer_email", "message": "invalid email format", "value": customer_email})

  # items
  items = []
  for i in (1,2):
    sku = normalize_str(val(f"item_sku_{i}"))
    qty = val(f"item_qty_{i}")
    price = val(f"item_price_{i}")

    # treat empty strings/nan as None
    if is_empty(sku) and is_empty(qty) and is_empty(price):
        continue  # no item in this slot

    # normalize numeric
    try:
      if is_empty(qty): qty_v = None
      else: qty_v = int(qty)
    except Exception:
        qty_v = None
    try:
      if is_empty(price): price_v = None
      else: price_v = float(price)
    except Exception:
      price_v = None

    if sku is None:
      errors.append({"sheet":None,"row":row_num,"field":f"item_sku_{i}","message":"item sku missing","value":sku})
    if qty_v is None or qty_v <= 0:
      errors.append({"sheet":None,"row":row_num,"field":f"item_qty_{i}","message":"qty must be > 0","value":qty})
    if price_v is None or price_v < 0:
      errors.append({"sheet":None,"row":row_num,"field":f"item_price_{i}","message":"unit price must be >= 0","value":price})

    if sku and qty_v and price_v is not None and qty_v > 0 and price_v >= 0:
      items.append({
        "sku": sku,
        "qty": int(qty_v),
        "unit_price": float(price_v),
        "line_total": round(int(qty_v) * float(price_v), 2)
      })

  customer = {
    "customer_id": int(customer_id) if customer_id is not None else None,
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
    "order_id": int(order_id) if order_id is not None else None,
    "order_date": order_date,
    "customer_id": int(customer_id) if customer_id is not None else None,
    "status": status.lower() if status is not None else None,
    "shipping_method": shipping_method.lower() if shipping_method is not None else None,
    "coupon_code": coupon_code
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
          crud.upsert_customer(db, cust)
          # upsert order
          crud.upsert_order(db, order)
          # remove existing items for the order to avoid duplicates (idempotency)
          db.query(models.OrderItem).filter(models.OrderItem.order_id == order["order_id"]).delete()
          # insert items
          for it in items:
            it_record = {
              "order_id": order["order_id"],
              "sku": it["sku"],
              "qty": it["qty"],
              "unit_price": it["unit_price"],
              "line_total": it["line_total"]
            }
            db.add(models.OrderItem(**it_record))
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
