# imports de librerías y dependencias
from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import Dict, Any

# imports de módulos internos
from app.models.models import OrderItem
from app.controllers.crud import upsert_customer, upsert_items, upsert_order
from app.controllers.ingest.read_excel import read_excel_file
from app.controllers.ingest.validate_row import validate_and_normalize_row
from app.controllers.ingest.constants import EXPECTED_COLS

# esta funcion recibe un archivo Excel y lo carga en la base de datos
def ingest_file(upload_file: UploadFile, db: Session) -> Dict[str, Any]:
  df = read_excel_file(upload_file)

  # Verificar columnas esperadas
  missing = [c for c in EXPECTED_COLS if c not in df.columns]
  if missing:
    # si faltan columnas esperadas, lanzar un error
    raise ValueError(f"Missing expected columns: {missing}")

  rows_read = len(df)
  errors = []
  inserted_customers = inserted_orders = inserted_items = 0
  updated_customers = updated_orders = 0

  try:
    # iterar por cada fila del archivo Excel
    for idx, row in df.iterrows():
      row_num = int(idx) + 2  # Excel row number (1 header + 1 offset)

      # Validar y normalizar fila
      cust, order, items, row_errors = validate_and_normalize_row(row, row_num)
      if row_errors:
        errors.extend(row_errors)
        continue

      try:
        # si el cliente no existe, lo inserta, si existe, lo actualiza
        customer_obj = upsert_customer(db, cust)
        order["customer_id"] = customer_obj.customer_id

        # Insertar o actualizar orden (idempotencia parcial)
        order_obj = upsert_order(db, order)
        order_id = order_obj.order_id  # id garantizado
        # garantiza indempotencia parcial

        # Borrar ítems previos antes de insertar los nuevos
        db.query(OrderItem).filter(OrderItem.order_id == order["order_id"]).delete()

        # preparar lista de dicts con order_id incluido para upsert_items
        items_to_insert = []
        for it in items:
          items_to_insert.append({
            "order_id": order_id,
            "sku": it["sku"],
            "qty": it["qty"],
            "unit_price": it["unit_price"],
            "line_total": it["line_total"]
          })

        # usar la función upsert_items
        inserted_items_list = upsert_items(db, items_to_insert)
        inserted_items += len(inserted_items_list)

        inserted_orders += 1
      except Exception as e:
        db.rollback()
        errors.append({"row": row_num, "message": f"DB error: {str(e)}"})
        continue

    db.commit()

  # si hay un error general, hacer rollback
  except Exception as e:
    db.rollback()
    raise e

  # retornar resultados
  return {
    "rows_read": rows_read,
    "inserted_customers": inserted_customers,
    "inserted_orders": inserted_orders,
    "inserted_items": inserted_items,
    "updated_customers": updated_customers,
    "updated_orders": updated_orders,
    "errors": errors
  }
