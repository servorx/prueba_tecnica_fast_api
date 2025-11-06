from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class OrderItemSchema(BaseModel):
    sku: str
    qty: int
    unit_price: float
    line_total: float

class OrderSchema(BaseModel):
    order_id: int
    order_date: date
    customer_id: int
    status: str
    shipping_method: Optional[str] = None
    coupon_code: Optional[str] = None
    items: List[OrderItemSchema]

class IngestResultRowError(BaseModel):
    sheet: Optional[str]
    row: int
    field: Optional[str]
    message: str
    value: Optional[str]

class IngestSummary(BaseModel):
    rows_read: int
    inserted_customers: int
    inserted_orders: int
    inserted_items: int
    updated_customers: int
    updated_orders: int
    errors: List[IngestResultRowError]
