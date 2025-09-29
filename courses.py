# import os
# import re
# import json
# import psycopg2
# from google import genai
# from dotenv import load_dotenv
# from rapidfuzz import fuzz

# load_dotenv()

# # API Key
# apiKey = os.getenv("API_KEY")

# # Conexão com o banco
# dbname = os.getenv("DB_NAME")
# host = os.getenv("DB_HOST")
# port = int(os.getenv("DB_PORT"))
# user = os.getenv("DB_USER")
# password = os.getenv("DB_PASSWORD")

# client = genai.Client(api_key=apiKey)

# lessons = [
#     # 'Matemática',
#     # 'História',
#     'Português',
#     # 'Geografia',
#     # 'Análise e Desenvolvimento de Sistemas'
# ]

# def normalizar_texto(texto):
#     texto = texto.lower()
#     texto = re.sub(r'[^\w\s]', '', texto)  # remove pontuação
#     texto = re.sub(r'\s+', ' ', texto).strip()
#     return texto

# def disciplina_similar_existe(cursor, course_id, nome_disciplina, limite_similaridade=85):
#     cursor.execute('''
#         SELECT "DisciplineName" FROM quizz."Discipline" WHERE "CourseId" = %s
#     ''', (course_id,))
#     disciplinas = cursor.fetchall()

#     nome_normalizado = normalizar_texto(nome_disciplina)

#     for (disc_existente,) in disciplinas:
#         existente_normalizado = normalizar_texto(disc_existente)
#         similaridade = fuzz.ratio(nome_normalizado, existente_normalizado)

#         if similaridade >= limite_similaridade:
#             print(f"🔁 Disciplina parecida já existe: \"{disc_existente}\" (similaridade: {similaridade}%)")
#             return True

#     return False


# def create_courses(l):
#     # Conexão com o banco
#     con = psycopg2.connect(
#         dbname = dbname,
#         host = host,
#         port = port,
#         user = user,
#         password = password
#     )
#     cursor = con.cursor()

#     for lesson in l:
#         # Verificar se já existe o curso
#         sql_select_course = '''
#             SELECT "Id" FROM quizz."Course" WHERE "CourseName" = %s
#         '''
#         cursor.execute(sql_select_course, (lesson,))
#         exists = cursor.fetchone()

#         if exists is not None:
#             print(f'Curso a ser inserido já existe !\nlesson')
#             continue
        
#         # Prompt da IA
#         prompt = f"""
#         Quero que me retorne 5 matérias básicas (nao podem ser tao dificeis pois vou por elas num quiz) do curso de {lesson} das ETEC's, se forem matérias do ensino médio comum, coloque matérias básicas do fundamental 2 e uma descrição para cada curso e cada matéria de no máximo 50 caracteres, nao precisa especificar nada da etec na descrição da seguinte forma em um json:
#         [
#             {{
#                 "course_name": {lesson},
#                 "course_description": "descricao do curso",
#                 "course_disciplines": [
#                     {{
#                         "discipline_name": "nome da disciplina",
#                         "discipline_description": "descrição da disciplina"
#                     }}
#                 ],
#                 "course_category": 'M-TEC' se o curso for técnico ou 'MÉDIO' se for padrão do ensino médio
#             }}
#         ]
#         """
#         response = client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=prompt
#         )
#         try:
#             # Formatação da resposta da IA
#             clean_text = re.sub(r'```json', '', response.text)
#             clean_text = re.sub(r'```', '', clean_text)

#             lessons = json.loads(clean_text)

#             for lesson in lessons:
#                 course_name = lesson["course_name"]
#                 course_desc = lesson["course_description"]
#                 course_disc = lesson["course_disciplines"]
#                 course_category = lesson["course_category"]

#                 sql_insert_course = '''
#                     INSERT INTO quizz."Course" ("Id", "CourseName", "Description", "Category") values (gen_random_uuid(), %s, %s, %s) RETURNING "Id"
#                 '''
#                 cursor.execute(sql_insert_course, (course_name, course_desc, course_category))
                
#                 # Retorno do ID do curso criado
#                 course_id = cursor.fetchone()[0]

#                 for discipline in course_disc:
#                     disc_name = discipline["discipline_name"]
#                     disc_desc = discipline["discipline_description"]

#                     if disciplina_similar_existe(cursor, course_id, disc_name):
#                         print(f'Disciplina ignorada por similaridade: {disc_name}')
#                         continue
                    
#                     sql_insert_disciplines = '''
#                         INSERT INTO quizz."Discipline" ("Id", "DisciplineName", "CourseId", "Description") values (gen_random_uuid(), %s, %s, %s)
#                     '''
#                     cursor.execute(sql_insert_disciplines, (disc_name, course_id, disc_desc))
                
#                 print('Incrivelmente tudo funcionou')
                    
#             con.commit()
#             cursor.close()
#             con.close()
#         except Exception as e:
#             print(f'Erro ao processar resposta da IA para {lesson}\n{e}')
#             continue

# create_courses(lessons)

import os
import re
import json
import psycopg2
from google import genai
from dotenv import load_dotenv
from rapidfuzz import fuzz

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

# Cursos que você quer criar ou complementar com novas disciplinas
lessons = [
    "Português"
    # Adicione mais cursos se quiser
]

def normalizar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def disciplina_similar_existe(cursor, course_id, nome_disciplina, limite_similaridade=85):
    cursor.execute('''
        SELECT "DisciplineName" FROM quizz."Discipline" WHERE "CourseId" = %s
    ''', (course_id,))
    disciplinas = cursor.fetchall()

    nome_normalizado = normalizar_texto(nome_disciplina)

    for (disc_existente,) in disciplinas:
        existente_normalizado = normalizar_texto(disc_existente)
        similaridade = fuzz.ratio(nome_normalizado, existente_normalizado)

        if similaridade >= limite_similaridade:
            print(f"🔁 Disciplina parecida já existe: \"{disc_existente}\" (similaridade: {similaridade}%)")
            return True

    return False

def create_courses(l):
    con = psycopg2.connect(
        dbname=dbname,
        host=host,
        port=port,
        user=user,
        password=password
    )
    cursor = con.cursor()

    for lesson in l:
        # Verifica se o curso já existe
        cursor.execute('SELECT "Id" FROM quizz."Course" WHERE "CourseName" = %s', (lesson,))
        course_row = cursor.fetchone()

        if course_row:
            course_id = course_row[0]
            print(f'📚 Curso "{lesson}" já existe. Buscando adicionar novas disciplinas.')

            # Prompt para gerar novas disciplinas diferentes
            prompt = f"""
            Me retorne 5 matérias diferentes das já criadas para o curso de {lesson} nas ETECs.
            As matérias devem ser básicas, fáceis e com descrição de no máximo 50 caracteres.
            Use o seguinte JSON:

            [
                {{
                    "discipline_name": "nome da disciplina",
                    "discipline_description": "descrição curta"
                }}
            ]
            """

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                clean_text = re.sub(r'```json', '', response.text)
                clean_text = re.sub(r'```', '', clean_text)
                novas_disciplinas = json.loads(clean_text)

                for disciplina in novas_disciplinas:
                    disc_name = disciplina["discipline_name"]
                    disc_desc = disciplina["discipline_description"]

                    if disciplina_similar_existe(cursor, course_id, disc_name):
                        print(f'⚠️ Disciplina ignorada por similaridade: {disc_name}')
                        continue

                    cursor.execute('''
                        INSERT INTO quizz."Discipline" ("Id", "DisciplineName", "CourseId", "Description")
                        VALUES (gen_random_uuid(), %s, %s, %s)
                    ''', (disc_name, course_id, disc_desc))

                print(f'✅ Novas disciplinas inseridas para "{lesson}"')

            except Exception as e:
                print(f'❌ Erro ao processar novas disciplinas para {lesson}:\n{e}')
                con.rollback()
                continue

        else:
            print(f'➕ Criando novo curso: {lesson}')

            # Prompt completo para novo curso + disciplinas
            prompt = f"""
            Me retorne um curso chamado "{lesson}" com 5 disciplinas básicas (não muito difíceis), com uma descrição para o curso e para cada disciplina (máx. 50 caracteres).
            Use o seguinte JSON:

            [
                {{
                    "course_name": "{lesson}",
                    "course_description": "descrição do curso",
                    "course_disciplines": [
                        {{
                            "discipline_name": "nome da disciplina",
                            "discipline_description": "descrição da disciplina"
                        }}
                    ],
                    "course_category": "M-TEC" ou "MÉDIO"
                }}
            ]
            """

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                clean_text = re.sub(r'```json', '', response.text)
                clean_text = re.sub(r'```', '', clean_text)
                course_data = json.loads(clean_text)[0]

                course_name = course_data["course_name"]
                course_desc = course_data["course_description"]
                course_category = course_data["course_category"]
                course_disciplines = course_data["course_disciplines"]

                cursor.execute('''
                    INSERT INTO quizz."Course" ("Id", "CourseName", "Description", "Category")
                    VALUES (gen_random_uuid(), %s, %s, %s)
                    RETURNING "Id"
                ''', (course_name, course_desc, course_category))

                course_id = cursor.fetchone()[0]

                for disciplina in course_disciplines:
                    disc_name = disciplina["discipline_name"]
                    disc_desc = disciplina["discipline_description"]

                    cursor.execute('''
                        INSERT INTO quizz."Discipline" ("Id", "DisciplineName", "CourseId", "Description")
                        VALUES (gen_random_uuid(), %s, %s, %s)
                    ''', (disc_name, course_id, disc_desc))

                print(f'✅ Curso "{course_name}" e disciplinas criados com sucesso!')

            except Exception as e:
                print(f'❌ Erro ao processar novo curso {lesson}:\n{e}')
                con.rollback()
                continue

    con.commit()
    cursor.close()
    con.close()

# Roda tudo
create_courses(lessons)
