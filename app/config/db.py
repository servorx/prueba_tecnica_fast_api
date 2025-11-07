# app/config/db.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import ProgrammingError
from app.config.config import DB_URL, DB_NAME  

# Crear engine de conexión al servidor MySQL (sin especificar DB para poder crearla)
engine_no_db = create_engine(DB_URL.rsplit("/", 1)[0], pool_pre_ping=True, future=True)

# Crear la base de datos si no existe
with engine_no_db.connect() as conn:
  try:
    # ejecutar comandos SQL para crear la DB
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
    conn.commit()
    print(f"Database '{DB_NAME}' created or already exists")
  except ProgrammingError as e:
    print(f"Error creating database: {e}")

# Engine final apuntando a la DB correcta
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
# Crear el sessionmaker
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
# Base declarativa para modelos
Base = declarative_base()

# Obtener una sesión de la base de datos 
def get_session():
  db = SessionLocal()
  try:
    yield db  # ejecutar el bloque de código dentro del contexto de la sesión de la base de datos, se usa yield para retornar el objeto de la sesión
  finally:
    db.close()
