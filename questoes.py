import os
import re
import json
import psycopg2
from google import genai
from dotenv import load_dotenv
from cursos import cursos
from rapidfuzz import fuzz

load_dotenv()

# Chave de API
ia_api_key = os.getenv('API_KEY')
client = genai.Client(api_key=ia_api_key)

# Conexão com o banco de dados
db_name = os.getenv('DB_NAME')
db_host = os.getenv('DB_HOST')
db_port = int(os.getenv('DB_PORT'))
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# Função para deixar texto como JSON
def normalizar_texto(texto):
    texto = re.sub(r'```json', '', texto)
    texto_normalizado = re.sub(r'```', '', texto).strip()
    texto_normalizado = json.loads(texto_normalizado)
    return texto_normalizado