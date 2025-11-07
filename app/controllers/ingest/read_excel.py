import pandas as pd
from fastapi import UploadFile

def read_excel_file(upload_file: UploadFile | str):
  # Lee un archivo Excel y devuelve un DataFrame.
  # Soporta tanto rutas locales (str) como UploadFile de FastAPI.
  if isinstance(upload_file, str):
    return pd.read_excel(upload_file, engine="openpyxl", dtype=object)
  else:
    return pd.read_excel(upload_file.file, engine="openpyxl", dtype=object)
