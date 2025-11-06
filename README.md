# Proycto prueba tecnica lectura de excel 

## Paso a paso para ejecutar el proyecto

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

## .env de prueba 
se realiza la conexion con el servidor de MySQL por lo que no se necesita XAMPP
```bash
DB_URL="mysql://campus2023:campus2023@localhost:3306/prueba_tecnica?schema=public"
```

## Ejecutar el proyecto
```bash
uvicorn app.main:app --reload
```

