import os
import psycopg2
from dotenv import load_dotenv
from google import genai
from re import sub
import json

load_dotenv()

# API Key
apiKey = os.getenv("API_KEY")

# Conexão com o banco
dbname = os.getenv("DB_NAME")
host = os.getenv("DB_HOST")
port = int(os.getenv("DB_PORT"))
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

client = genai.Client(api_key=apiKey)

lessons = [
    'Matemática',
    'História',
    'Português',
    'Geografia',
    'Análise e Desenvolvimento de Sistemas'
]

def create_courses(l):
    # Conexão com o banco
    con = psycopg2.connect(
        dbname = dbname,
        host = host,
        port = port,
        user = user,
        password = password
    )
    cursor = con.cursor()

    for lesson in l:
        # Verificar se já existe o curso
        sql_select_course = '''
            SELECT "Id" FROM quizz."Course" WHERE "CourseName" = %s
        '''
        cursor.execute(sql_select_course, (lesson,))
        exists = cursor.fetchone()

        if exists is not None:
            print('Curso a ser inserido já existe !\n', lesson)
            continue
        
        # Prompt da IA
        prompt = f"""
        Quero que me retorne 5 matérias básicas (nao podem ser tao dificeis pois vou por elas num quiz) do curso de {lesson} das ETEC's, se forem matérias do ensino médio comum, coloque matérias básicas do fundamental 2 e uma descrição para cada curso e cada matéria de no máximo 50 caracteres, nao precisa especificar nada da etec na descrição da seguinte forma em um json:
        [
            {{
                "course_name": {lesson},
                "course_description": "descricao do curso",
                "course_disciplines": [
                    {{
                        "discipline_name": "nome da disciplina",
                        "discipline_description": "descrição da disciplina"
                    }}
                ],
                "course_category": 'M-TEC' se o curso for técnico ou 'MÉDIO' se for padrão do ensino médio
            }}
        ]
        """
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        try:
            # Formatação da resposta da IA
            clean_text = sub(r'```json', '', response.text)
            clean_text = sub(r'```', '', clean_text)

            lessons = json.loads(clean_text)

            for lesson in lessons:
                course_name = lesson["course_name"]
                course_desc = lesson["course_description"]
                course_disc = lesson["course_disciplines"]
                course_category = lesson["course_category"]

                sql_insert_course = '''
                    INSERT INTO quizz."Course" ("Id", "CourseName", "Description", "Category") values (gen_random_uuid(), %s, %s, %s) RETURNING "Id"
                '''
                cursor.execute(sql_insert_course, (course_name, course_desc, course_category))
                
                # Retorno do ID do curso criado
                course_id = cursor.fetchone()[0]

                for discipline in course_disc:
                    disc_name = discipline["discipline_name"]
                    disc_desc = discipline["discipline_description"]
                    
                    sql_insert_disciplines = '''
                        INSERT INTO quizz."Discipline" ("Id", "DisciplineName", "CourseId", "Description") values (gen_random_uuid(), %s, %s, %s)
                    '''
                    cursor.execute(sql_insert_disciplines, (disc_name, course_id, disc_desc))
                
                print('Incrivelmente tudo funcionou')
                    
            con.commit()
            cursor.close()
            con.close()
        except Exception as e:
            print(f'Erro ao processar resposta da IA para {lesson}')
            continue

create_courses(lessons)