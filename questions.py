import json
from google import genai
import psycopg2
import re
from dotenv import load_dotenv
from disciplines import disciplines
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

client = genai.Client(api_key=apiKey)
def verify_lessons(l):
    con = psycopg2.connect(
        dbname = dbname,
        host = host,
        port = port,
        user = user,
        password = password
    )
    cursor = con.cursor()

    for lesson in lessons:
        sql_select_course_id = '''
            SELECT "Id" FROM quizz."Course" WHERE "CourseName" = %s
        '''
        cursor.execute(sql_select_course_id, (lesson,))
        course_id = cursor.fetchone()[0]

        sql_select_discipline_id = '''
            SELECT "Id" FROM quizz."Discipline" WHERE "CourseId" = %s
        '''
        cursor.execute(sql_select_discipline_id, (course_id,))
        discipline_id = cursor.fetchone()[0]

        sql_select_question_id = '''
            SELECT "Id" FROM quizz."Question" WHERE "DisciplineId" = %s
        '''
        cursor.execute(sql_select_question_id, (discipline_id,))
        exists = cursor.fetchone()

        if exists is not None:
            print('Já existem questões para essa matéria !\n', lesson)
            continue
    

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents='''
        Quero que elabore perguntas de quizz, com 5 alternativas, níveis diferentes sobre o ensino de ADS, que tem as disciplinas Banco de Dados, Programação Web, Qualidade e Teste de Software, Segurança da Informação, Design Digital, Sistemas Embarcados, Programação Mobile, Fundamentos da Informática, Análise e Projeto de Sistemas, Técnicas de Programação e Algoritmos que sejam menos específicas e volte um JSON da seguinte forma:
        [
            {
                "question_title": "(Título da questão de no máximo 140 caracteres)",
                "discipline": "(disciplina da pergunta)",
                "alternatives": [["(texto da alternativa de no máximo 90 caracteres)", (1 para correta ou 0 para incorreta)]],
                "difficulty": "(um número de 0 à 2 conforme a dificuldade da pergunta)"
            }
        ]
    '''
)

response_text = response.text

clean_text = re.sub(r'^```json', '', response_text)
clean_text = re.sub(r'```', '', clean_text)

print(clean_text)

clean_text = clean_text.strip()

questions = json.loads(clean_text)

def insert_questions(q):
    if not q:
        print('Questões não foram criadas corretamente!')
        return

    con = psycopg2.connect(
        dbname = dbname,
        host = host,
        port = port,
        user = user,
        password = password
    )
    cursor = con.cursor()

    for question in q:
        title = question["question_title"]
        discipline = question["discipline"]
        difficulty = question["difficulty"]
        alternatives = question["alternatives"]

        discipline_id = disciplines.get(discipline, None)
        if not discipline_id:
            print(f'Disciplina "{discipline}" não encontrada. Pulando questão.')
            continue

        sql_insert_question = '''
            INSERT INTO quizz."Question"
            ("Id", "QuestionStatement", "DisciplineId", "Difficulty")
            VALUES(gen_random_uuid(), %s, %s, %s)
            RETURNING "Id";
        '''
        cursor.execute(sql_insert_question, (title, discipline_id, difficulty))

        question_id = cursor.fetchone()[0]

        for text_alternative, correct in alternatives:
            correct = True if correct == 1 else False
            sql_insert_answers = '''
                INSERT INTO quizz."Answer"
                ("Id", "QuestionId", "AnswerText", "IsCorrect")
                VALUES(gen_random_uuid(), %s, %s, %s)
            '''
            cursor.execute(sql_insert_answers, (question_id, text_alternative, correct))

    con.commit()
    cursor.close()
    con.close()
    print("Todas as questões e alternativas foram inseridas com sucesso!")

insert_questions(questions)