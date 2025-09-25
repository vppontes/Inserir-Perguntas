import json
from google import genai
import psycopg2
import re
from dotenv import load_dotenv
import os
from courses import lessons

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

def insert_questions(questions, disc_id, lesson):
    try:
        if not questions:
            print(f'❌ Nenhuma questão gerada para {lesson}')
            return

        for question in questions:
            title = question["question_title"]
            difficulty = question["difficulty"]
            alternatives = question["alternatives"]

            sql_insert_question = '''
                INSERT INTO quizz."Question"
                ("Id", "QuestionStatement", "DisciplineId", "Difficulty")
                VALUES(gen_random_uuid(), %s, %s, %s)
                RETURNING "Id";
            '''
            cursor.execute(sql_insert_question, (title, disc_id, difficulty))
            question_id = cursor.fetchone()[0]

            for text_alternative, correct in alternatives:
                is_correct = True if correct == 1 else False
                sql_insert_answers = '''
                    INSERT INTO quizz."Answer"
                    ("Id", "QuestionId", "AnswerText", "IsCorrect")
                    VALUES(gen_random_uuid(), %s, %s, %s)
                '''
                cursor.execute(sql_insert_answers, (question_id, text_alternative, is_correct))

        print(f'✅ Questões inseridas para {lesson}')
    
    except Exception as e:
        print(f'❌ Erro ao criar questões para {lesson}: {e}')

def verify_lessons(l):
    for lesson in l:
        # Verifica curso
        cursor.execute('SELECT "Id" FROM quizz."Course" WHERE "CourseName" = %s', (lesson,))
        course_row = cursor.fetchone()
        if not course_row:
            print(f"⚠️ Curso {lesson} não encontrado.")
            continue
        course_id = course_row[0]

        # Verifica disciplina
        cursor.execute('SELECT "Id", "DisciplineName" FROM quizz."Discipline" WHERE "CourseId" = %s', (course_id,))
        discipline_rows = cursor.fetchall()
        if not discipline_rows:
            print(f"⚠️ Nenhuma disciplina para o curso {lesson}.")
            continue

        for discipline_id, discipline_name in discipline_rows:
            # Verifica se já há questões
            cursor.execute('SELECT "Id" FROM quizz."Question" WHERE "DisciplineId" = %s', (discipline_id,))
            if cursor.fetchone():
                print(f'🟡 Já existem questões para {discipline_name} ({lesson})')
                continue

            print(f'🛠️ Criando questões para {discipline_name} ({lesson})...')

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

                clean_text = re.sub(r'^```json', '', response.text.strip())
                clean_text = re.sub(r'```$', '', clean_text)
                questions = json.loads(clean_text)

                insert_questions(questions, discipline_id, lesson)

            except Exception as e:
                print(f"❌ Erro ao processar IA para {lesson}/{discipline_name}: {e}")
                con.rollback()
                continue

verify_lessons(lessons)

# Encerrar conexão
con.commit()
cursor.close()
con.close()
