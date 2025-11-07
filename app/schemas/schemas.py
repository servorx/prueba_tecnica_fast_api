from typing import List, Optional
from pydantic import BaseModel
from datetime import date

# esquemas que se utilizan en la base de datos para estructurar validaciones y respuestas de datos 
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
