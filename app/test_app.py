# importar dependencias
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# importar desde la aplicación
from models.models import Base, Order
from controllers.ingest import validate_and_normalize_row, ingest_file
from main import app

client = TestClient(app)

def test_clean_load(tmp_path):
    # Simula Excel limpio
    data = {
        "customer_name": ["Alice", "Bob"],
        "order_id": [1, 2],
        "item_sku": ["A1", "B1"],
        "quantity": [2, 3]
    }
    df = pd.DataFrame(data)

    valid_rows = []
    for i, row in df.iterrows():
        result = validate_and_normalize_row(row, i)
        valid_rows.append(result)

    customers = {r[0]['name'] for r in valid_rows}
    assert len(customers) == 2
    assert all(len(r[3]) == 0 for r in valid_rows)  # sin errores

def test_dirty_load(tmp_path):
    df = pd.DataFrame({
        "customer_name": ["Alice", None, "Bob"],
        "order_id": [1, 2, 3],
        "item_sku": ["A1", "B1", None],
        "quantity": [2, 3, 1]
    })

    valid, invalid = 0, 0
    for i, row in df.iterrows():
        customer, order, items, errors = validate_and_normalize_row(row, i)
        if errors:
            invalid += 1
        else:
            valid += 1
    assert valid == 2
    assert invalid == 1

def test_sparse_load():
    df = pd.DataFrame({
        "customer_name": ["Alice"],
        "order_id": [1],
        "item_sku": [None],  # vacío permitido
        "quantity": [None]
    })
    _, _, _, errors = validate_and_normalize_row(df.iloc[0], 0)
    assert errors == []  # no debe fallar

def test_db_summary():
    response = client.get("/db/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_customers" in data
    assert isinstance(data["total_orders"], int)

def test_idempotency(db_session):
    # Primera carga
    ingest_file("data_clean.xlsx", db_session)
    count_1 = db_session.query(Order).count()

    # Segunda carga del mismo archivo
    ingest_file("data_clean.xlsx", db_session)
    count_2 = db_session.query(Order).count()

    assert count_2 == count_1  # no debe duplicar

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    # Limpia la metadata previa antes de recrear
    Base.metadata.clear()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()