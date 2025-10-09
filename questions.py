import os
import re
import json
import psycopg2
from google import genai
from dotenv import load_dotenv
from courses import lessons
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

con = psycopg2.connect(
    dbname=dbname,
    host=host,
    port=port,
    user=user,
    password=password
)
cursor = con.cursor()

client = genai.Client(api_key=apiKey)

def reconnect():
    global con, cursor
    try:
        con = psycopg2.connect(
            dbname=dbname,
            host=host,
            port=port,
            user=user,
            password=password
        )
        cursor = con.cursor()
        print("🔁 Reconectado ao banco de dados")
    except Exception as e:
        print(f"❌ Falha ao reconectar: {e}")

def normalizar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def pergunta_parecida(cursor, disciplina_id, nova_pergunta_normalizada, limite_similaridade=75):
    cursor.execute('SELECT "QuestionStatement" FROM public."Question" WHERE "DisciplineId" = %s', (disciplina_id,))
    perguntas = cursor.fetchall()

    for (existente,) in perguntas:
        if existente is None:
            continue
        normalizada = normalizar_texto(existente)
        similaridade = fuzz.ratio(nova_pergunta_normalizada, normalizada)
        if similaridade >= limite_similaridade:
            return True
    return False

def insert_questions(questions, disc_id, disc_name, lesson):
    try:
        if not questions:
            print(f'❌ Nenhuma questão gerada para {lesson}')
            return

        inseridas = 0
        ignoradas = 0

        for question in questions:
            title = question["question_title"]
            difficulty = question["difficulty"]
            alternatives = question["alternatives"]

            titulo_normalizado = normalizar_texto(title)

            if pergunta_parecida(cursor, disc_id, titulo_normalizado):
                print(f'Pergunta parecida já existe \"{title}" ')
                ignoradas += 1
                continue

            cursor.execute('''
                INSERT INTO public."Question"
                ("Id", "QuestionStatement", "DisciplineId", "Difficulty") VALUES
                (gen_random_uuid(), %s, %s, %s) RETURNING "Id";
            ''', (title, disc_id, difficulty))
            question_id = cursor.fetchone()[0]

            for text_alternative, correct in alternatives:
                is_correct = True if correct == 1 else False
                
                cursor.execute('''
                    INSERT INTO public."Answer"
                    ("Id", "QuestionId", "AnswerText", "IsCorrect") VALUES
                    (gen_random_uuid(), %s, %s, %s);
                ''', (question_id, text_alternative, is_correct))

        print(f'Questões inseridas para {disc_name}')
        inseridas += 1

        if inseridas:
            print(f'{inseridas} questões inseridas para {lesson}')
        if ignoradas:
            print(f'{ignoradas} questões ignoradas para {lesson}')
    
    except Exception as e:
        print(f'Erro ao criar questões para {lesson}:\n{e}')

def verify_lessons(l):
    for lesson in l:
        # Verifica curso
        cursor.execute('SELECT "Id" FROM public."Course" WHERE "CourseName" = %s', (lesson,))
        course_row = cursor.fetchone()
        if not course_row:
            print(f"❌ Curso {lesson} não encontrado.")
            continue
        course_id = course_row[0]

        # Verifica disciplinas do curso
        cursor.execute('SELECT "Id", "DisciplineName" FROM public."Discipline" WHERE "CourseId" = %s', (course_id,))
        discipline_rows = cursor.fetchall()
        if not discipline_rows:
            print(f"⚠️ Nenhuma disciplina encontrada para o curso {lesson}.")
            continue

        for discipline_id, discipline_name in discipline_rows:
            # Verifica se já há questões
            cursor.execute('SELECT "Id" FROM public."Question" WHERE "DisciplineId" = %s', (discipline_id,))
            if cursor.fetchone():
                print(f'⏩ Já existem questões para {discipline_name} ({lesson})')
                continue

            print(f'📝 Criando questões para {discipline_name} ({lesson})')

            i = 0
            while i <= 2:
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f'''
                            Quero que elabore perguntas de quizz, que sejam possíveis de responder num tempo curto, com 5 alternativas, níveis diferentes sobre o ensino de {discipline_name} do curso de {lesson}. Use o seguinte formato JSON:
                            [
                                {{
                                    "question_title": "pergunta (de no máximo 140 caracteres)",
                                    "discipline": "nome da disciplina",
                                    "alternatives": [["texto da alternativa (de no máximo 90 caracteres)", 1 ou 0]],
                                    "difficulty": "0 a 2"
                                }}
                            ]
                        '''
                    )

                    raw_response = response.text.strip()

                    # Tenta extrair o JSON entre ```json ... ```
                    json_match = re.search(r'```json\s*(\[\s*\{.*?\}\s*\])\s*```', raw_response, re.DOTALL)
                    if not json_match:
                        print(f"⚠️ Não foi possível encontrar JSON válido na resposta da IA para {discipline_name} ({lesson})")
                        print("Resposta bruta:")
                        print(raw_response)
                        break  # Pula para a próxima disciplina

                    clean_text = json_match.group(1)

                    try:
                        questions = json.loads(clean_text)
                        insert_questions(questions, discipline_id, discipline_name, lesson)
                    except json.JSONDecodeError as e:
                        print(f"❌ Erro ao decodificar JSON para {discipline_name} ({lesson}): {e}")
                        print("Trecho capturado:")
                        print(clean_text)
                        break  # Pula para a próxima disciplina

                except Exception as e:
                    print(f"❌ Erro ao processar IA para {lesson}/{discipline_name}: {e}")
                    con.rollback()
                    break  # Pula para a próxima disciplina

                i += 1

    print('✅ Todas as questões foram processadas!')

verify_lessons(lessons)

# Encerrar conexão
con.commit()
cursor.close()
con.close()