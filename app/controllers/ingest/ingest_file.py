from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import Dict, Any

from app.models.models import OrderItem
from app.controllers.crud import upsert_customer, upsert_order
from app.controllers.ingest.read_excel import read_excel_file
from app.controllers.ingest.validate_row import validate_and_normalize_row
from app.controllers.ingest.constants import EXPECTED_COLS
from app.utils.utils import is_empty

def ingest_file(upload_file: UploadFile, db: Session) -> Dict[str, Any]:
  # Procesa el archivo Excel, valida los datos y ejecuta las operaciones de inserción/actualización.
  df = read_excel_file(upload_file)

  # Verificación de columnas
  missing = [c for c in EXPECTED_COLS if c not in df.columns]
  if missing:
    raise ValueError(f"Missing expected columns: {missing}")

  rows_read = len(df)
  errors = []
  inserted_customers = inserted_orders = inserted_items = 0
  updated_customers = updated_orders = 0

  # Transacción principal
  with db.begin():
    for idx, row in df.iterrows():
      row_num = int(idx) + 2  # Excel row (1 header + 1 base)
      with db.begin_nested():
        cust, order, items, row_errors = validate_and_normalize_row(row, row_num)
        if row_errors:
          errors.extend(row_errors)
          continue

        try:
          upsert_customer(db, cust)
          upsert_order(db, order)
          db.query(OrderItem).filter(OrderItem.order_id == order["order_id"]).delete()
          for it in items:
            db.add(OrderItem(
              order_id=order["order_id"],
              sku=it["sku"],
              qty=it["qty"],
              unit_price=it["unit_price"],
              line_total=it["line_total"]
            ))
            inserted_items += 1
          inserted_orders += 1
        except Exception as e:
          errors.append({"row": row_num, "message": f"DB error: {str(e)}"})
          raise

  return {
    "rows_read": rows_read,
    "inserted_customers": inserted_customers,
    "inserted_orders": inserted_orders,
    "inserted_items": inserted_items,
    "updated_customers": updated_customers,
    "updated_orders": updated_orders,
    "errors": errors
  }
