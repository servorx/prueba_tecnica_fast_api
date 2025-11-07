# main.py
import uvicorn
from app.routes.routes import create_app

# crear la aplicación con la funcion create_app
app = create_app()


if __name__ == "__main__":
  # ejecutar la aplicación con uvicorn y configuraciones de host y puerto
  uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
