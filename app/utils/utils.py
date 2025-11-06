# regular expressions para manipular cadenas de texto
import re
import pandas as pd
from typing import Optional
from datetime import datetime
import math

# validaciones y utilidades del email
EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

# validaciones y utilidades del status y shipping
VALID_STATUS = {"paid", "pending", "canceled"}
VALID_SHIPPING = {"standard", "express", "pickup"}

# define si un valor es nulo o vacio y no es un NaN
def is_empty(x):
  return x is None or (isinstance(x, float) and math.isnan(x)) or (isinstance(x, str) and x.strip() == "")

def normalize_str(x: Optional[str]) -> Optional[str]:
  if x is None:
    return None
  if isinstance(x, str):
    s = x.strip()
    return s if s != "" else None
  return str(x)

def parse_date_any(x):
  if is_empty(x):
    return None
  # usar pandas para parsear fechas en varios formatos
  try:
    dt = pd.to_datetime(x, errors="coerce")
    if pd.isna(dt):
      return None
    return dt.date()
  except Exception:
    return None

def basic_email_check(email: Optional[str]) -> bool:
  if email is None:
    return True  # nullable allowed
  return EMAIL_RE.match(email.strip()) is not None
