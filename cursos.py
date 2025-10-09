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
client = genai.Client(api_key=ia_api_key)

# Conexão com o banco de dados
db_name = os.getenv('DB_NAME')
db_host = os.getenv('DB_HOST')
db_port = int(os.getenv('DB_PORT'))
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# Cursos a serem implementados
cursos = [
    'Geografia',
    # Colocar mais
]

# Função para deixar texto como JSON
def normalizar_texto(texto):
    texto = re.sub(r'```json', '', texto)
    texto_normalizado = re.sub(r'```', '', texto).strip()
    texto_normalizado = json.loads(texto_normalizado)
    return texto_normalizado

# Verificar se já existe uma disciplina similar
def disciplina_similiar_existe(cursor, id_curso, nome_disciplina, limite_similaridade = 85):
    cursor.execute('''
        SELECT "DisciplineName" FROM public."Discipline" WHERE "CourseId" = %s
    ''', (id_curso,))
    
    # Pega toda as diciplinas já existentes do curso
    disciplinas = cursor.fetchall()
    
    nome_normalizado = normalizar_texto(nome_disciplina)

    for disc_existente in disciplinas:
        existente_normalizado = normalizar_texto(disc_existente)
        similaridade = fuzz.ratio(nome_normalizado, existente_normalizado)

        if similaridade >= limite_similaridade:
            print(f'Disciplina parecida já existe: {disc_existente} (similaridade: {similaridade}%)')
            return True

    return False

def criar_cursos(lista_cursos):
    # Conexão com o Banco de Dados
    con = psycopg2.connect(
        dbname = db_name,
        host = db_host,
        port = db_port,
        user = db_user,
        password = db_password
    )
    cursor = con.cursor()

    for curso in lista_cursos:
        # Verifica se o curso já existe
        cursor.execute('SELECT "Id" FROM public."Course" WHERE "CourseName" = %s', (curso,))
        curso_existente = cursor.fetchone()
        
        if curso_existente:
            id_curso_existente = curso_existente[0]
            print(f'📚 Curso "{curso}" já existe')
        
            # Conta quantas disciplinas já existem nesse curso
            cursor.execute(f'''SELECT COUNT("Id") from public."Discipline" WHERE "CourseId" = '{id_curso_existente}' ''')
            contagem_disciplinas = cursor.fetchone()[0]
            
            # Se há mais de 5 disciplinas, não adiciona nenhuma
            if contagem_disciplinas < 5:
                materias_a_fazer = 5 - contagem_disciplinas
                try:
                    ia_resposta = client.models.generate_content(
                        model = 'gemini-2.5-flash',
                        contents = f"""
                            Me retorne {materias_a_fazer} matérias diferentes das já criadas para o curso de {curso} nas ETECs.
                            As matérias devem ser básicas, fáceis para serem de um quiz e com descrição de no máximo 50 caracteres.
                            Use o seguinte JSON:

                            [
                                {{
                                    "discipline_name": "nome da disciplina",
                                    "discipline_description": "descrição curta"
                                }}
                            ]
                            """
                    )
                    
                    # Normalizar resposta da IA
                    novas_disciplinas = normalizar_texto(ia_resposta.text)
                    
                    # Insere no banco de dados cada disciplina
                    for disciplina in novas_disciplinas:
                        nome_disc = disciplina['discipline_name']
                        descricao_disciplina = disciplina['discipline_description']
                        
                        if disciplina_similiar_existe(cursor, id_curso_existente):
                            print(f'Disciplina ignorada por similaridade: {descricao_disciplina}')
                            continue
                        
                        cursor.execute('''INSERT INTO public."Discipline"
                            ("Id", "Description", "DisciplineName", "CreatedAt", "UpdatedAt", "CourseId") VALUES
                            (gen_random_uuid(), %s, %s, now(), now(), %s);
                        ''', (descricao_disciplina, nome_disc, id_curso_existente))
                        
                    print(f'Novas disciplinas inseridas para {curso}')
                    
                except Exception as e:
                    print(f'Erro ao processar novas disciplinas para {curso}: \n{e}')
                    continue
            else:
                print(f'Já existem disciplinas suficientes para este curso: {contagem_disciplinas}')
        else:
            # Se não existe o curso ainda, cria-o
            print(f'Criando novo curso: {curso}')
            
            try:
                ia_resposta = client.models.generate_content(
                    model = 'gemini-2.5-flash',
                    contents = f"""
                        Me retorne um curso chamado "{curso}" com 5 disciplinas básicas (não muito difíceis), com uma descrição para o curso e para cada disciplina (máx. 50 caracteres).
                        Use o seguinte JSON:

                        [
                            {{
                                "course_name": "{curso}",
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
                )
                
                # Normalizar resposta da IA
                informacoes_curso = normalizar_texto(ia_resposta.text)
                informacoes_curso = informacoes_curso[0]
                
                nome_curso = informacoes_curso["course_name"]
                descricao_curso = informacoes_curso["course_description"]
                categoria_curso = informacoes_curso["course_category"]
                disciplinas_curso = informacoes_curso["course_disciplines"]
                
                if categoria_curso == 'MÉDIO' or categoria_curso == 'MEDIO':
                    categoria_curso = 1
                else:
                    categoria_curso = 0
                    
                cursor.execute('''
                    INSERT INTO public."Course"
                    ("Id", "CourseName", "Description", "Category", "Rating", "CreatedAt", "UpdatedAt")
                    VALUES(gen_random_uuid(), %s, %s, %s, 0, now(), now()) RETURNING "Id";
                ''', (nome_curso, descricao_curso, categoria_curso))
                
                # Pega o ID do curso criado para inserir nas disciplinas
                id_curso = cursor.fetchone()[0]
                
                # Insere cada discilpinas no banco de dados
                for disciplina in disciplinas_curso:
                    nome_disc = disciplina['discipline_name']
                    descricao_disciplina = disciplina['discipline_description']
                    
                    cursor.execute('''
                        INSERT INTO public."Discipline"
                        ("Id", "Description", "DisciplineName", "CreatedAt", "UpdatedAt", "CourseId") VALUES
                        (gen_random_uuid(), %s, %s, now(), now(), %s);
                    ''', (descricao_disciplina, nome_curso, id_curso))
                    
                # Aplica as alterações
                con.commit()
                
                print(f'Curso {nome_curso} e disciplinas criados com sucesso !')
                
            except Exception as e:
                print(f'Erro ao processar novo curso {curso}:\n{e}')
                continue
                
criar_cursos(cursos)