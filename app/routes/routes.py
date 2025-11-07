# importaciones de librerías y dependencias
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# importaciones de módulos internos
from app.config.db import engine, Base, get_session
from app.controllers.ingest.ingest_file import ingest_file
from app.schemas.schemas import IngestSummary
from app.models.models import Customer, Order, OrderItem

def create_app() -> FastAPI:
  # Crear app
  app = FastAPI(title="Excel Ingest API")

  # Solo para desarrollo: crear tablas automáticamente
  Base.metadata.create_all(bind=engine)

  # Rutas
  @app.get("/health")
  def health():
    return {"status": "ok"}

  @app.post("/ingest", response_model=IngestSummary)
  async def ingest(file: UploadFile = File(...), db: Session = Depends(get_session)):
    try:
      result = ingest_file(file, db)
    except ValueError as ve:
      raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(content=jsonable_encoder(result))

  @app.get("/schema")
  def schema_example():
    example = {
      "order_id": 12345,
      "order_date": "2023-08-01",
      "customer_id": 987,
      "status": "paid",
      "shipping_method": "express",
      "coupon_code": None,
      "items": [
        {"sku": "SKU-111", "qty": 2, "unit_price": 12.50, "line_total": 25.00},
        {"sku": "SKU-222", "qty": 1, "unit_price": 5.00, "line_total": 5.00}
      ]
    }
    return example

  @app.get("/db/summary")
  def db_summary(db: Session = Depends(get_session)):
    total_customers = db.query(func.count(Customer.customer_id)).scalar()
    total_orders = db.query(func.count(Order.order_id)).scalar()
    total_items = db.query(func.count(OrderItem.id)).scalar()

    revenue_q = db.query(
      Order.status,
      func.sum(OrderItem.line_total).label("sum_total")
    ).join(
      OrderItem, Order.order_id == OrderItem.order_id
    ).group_by(Order.status)

    revenue = {"paid": 0.0, "pending": 0.0, "canceled": 0.0}
    for status, s in revenue_q:
      revenue[status] = float(s or 0.0)

    return {
      "total_customers": total_customers,
      "total_orders": total_orders,
      "total_items": total_items,
      "revenue": revenue
    }

  return app
