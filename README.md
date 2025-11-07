# Proyecto prueba tecnica - Lectura de excel 

Este proyecto implementa un backend FastAPI para la ingestión, validación y persistencia de datos desde archivos Excel a una base de datos MySQL. Incluye validaciones por fila, manejo de sparse data, y persistencia de clientes, órdenes e items.

---

## 🔹 Estructura del repositorio
```
├── app
│   ├── config
│   │   ├── config.py
│   │   └── db.py
│   ├── controllers
│   │   ├── ingest
│   │   │   ├── __init__.py
│   │   │   ├── constants.py
│   │   │   ├── ingest_file.py
│   │   │   ├── read_excel.py
│   │   │   └── validate_row.py
│   │   └── crud.py
│   ├── data
│   │   ├── dll.sql
│   │   ├── orders_wide_clean_v3.xlsx
│   │   ├── orders_wide_dirty_v3.xlsx
│   │   └── orders_wide_sparse_v3.xlsx
│   ├── models
│   │   └── models.py
│   ├── routes
│   │   └── routes.py
│   ├── schemas
│   │   └── schemas.py
│   ├── utils
│   │   └── utils.py
│   └── main.py
├── docker
│   └── docker-compose.yml
├── .gitignore
├── README.md
└── requirements.txt
```

---

## ⚙️ Paso a paso para ejecutar el proyecto

### Clonar el repositorio
```bash
git clone https://github.com/servorx/prueba_tecnica_fast_api
cd prueba_tecnica
code . 
```

### Instalar dependencias
el entorno de desarrollo se requiere para poder instalar las dependencias de forma aislada
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### .env de prueba 
se realiza la conexion con el servidor de MySQL por lo que no se necesita XAMPP
```bash
DB_URL="mysql+pymysql://campus2023:campus2023@localhost:3306/prueba_tecnica"
DB_NAME="prueba_tecnica"
```
el proyecto crea la base de datos si no existe y se ejecuta con pymysql

### Ejecutar el proyecto
```bash
uvicorn app.main:app --reload
```
la api se ejecuta en http://localhost:8000

---

## 📑 Endpoints principales

| Método | Endpoint     | Descripción                                         |
| ------ | ------------ | --------------------------------------------------- |
| POST   | `/ingest`    | Cargar archivo Excel con clientes, órdenes e items. |
| GET    | `/health`    | Comprobar el estado de la API.                      |
| GET    | `/schema`    | Ejemplo de esquema estático para la ruta /schema.   |
| GET    | `/db/summary`| Obtener un resumen de la base de datos.             |

--- 

## 🧪 Validaciones implementadas
- Strings normalizados y trims aplicados.

- Fechas parseadas a YYYY-MM-DD (varios formatos soportados).

- status fuera de {"paid","pending","canceled"} → error por fila.

- shipping_method inválido → error por fila.

- quantity ≤ 0 → error por fila.

- unit_price < 0 → error por fila (puede agregarse si se extiende la lógica).

- Emails con regex básica (correo@dominio.com).

- Campos vacíos persistidos como NULL.

- Sparse data permitido: filas sin items no abortan carga.

---

## 📦 Persistencia y arquitectura

- SQLAlchemy + MySQL para persistencia.

- Patrón upsert para clientes y órdenes: si existe, se actualiza; si no, se inserta.

- Items asociados a órdenes; persistencia condicional si fila contiene SKU y cantidad válida.

- Estructura basada en hexagonal architecture: controllers, services, repositories, utils, routes.

--- 

## ⚡ Manejo de errores

- Errores de validación por fila se retornan como JSON:
```json
{
  "row": 10,
  "field": "customer_email",
  "message": "invalid email format"
}
```
- Errores de base de datos (constraint violations) se agregan al reporte de ingest:
```json
{
  "row": 10,
  "message": "DB error: Column 'order_date' cannot be null"
}
```

---

## 🗂️ Notas adicionales

- Se soporta sparse data, lo que significa que filas incompletas no bloquean la carga de otras filas válidas.

- La base de datos se puede crear automáticamente al iniciar db.py.

- Validaciones y limpieza se realizan en app/utils/utils.py y validate_row.py.

- Compatible con Python 3.12 y FastAPI 0.100+.

---

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para obtener más detalles.

## 📄 Autor

[Ángel David](https://github.com/servorx)