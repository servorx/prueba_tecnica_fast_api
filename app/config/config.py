import os
from dotenv import load_dotenv

load_dotenv()

# obitener la URL de la base de datos desde las variables de entorno o usar una por defecto si no está definida 
DB_URL = os.getenv("DB_URL", "sqlite:///./test.db") 
