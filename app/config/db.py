from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# importar del archivo config.py
from .config import DB_URL

# crea la conexion a la base de datos
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_session():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
