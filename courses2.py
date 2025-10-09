import os
import re
import json
import psycopg2
from google import genai
from dotenv import load_dotenv
from rapidfuzz import fuzz

load_dotenv()

# Chave de API
ia_api_key = os.getenv('API_KEY')

# Conexão com o banco de dados
db_name = os.getenv('DB_NAME')
db_host = os.getenv('DB_HOST')
db_port = int(os.getenv('DB_PORT'))
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

client = genai.Client(api_key=ia_api_key)

# Cursos a serem implementados
cursos = [
    'Geografia',
]

def normalizar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

txt = '''```json
[
    {
        "discipline_name": "nome da disciplina",
        "discipline_description": "descrição curta"
    }
]
```'''

txt2 = txt

normalizar_texto(txt)

def normalizar_texto(texto):
    texto_normalizado = re.sub(r'```json', '', texto)
    texto_normalizado = re.sub(r'```', '', texto_normalizado).strip()
    return texto

print(txt)
print(normalizar_texto(txt2))