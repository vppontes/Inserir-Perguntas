import json
from google import genai
import psycopg2

client = genai.Client(api_key="AIzaSyB2rcmmTe5vuNxT3Hv1jGpFZU1maYo6wlU")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents='''
        Quero que elabore uma única pergunta de quizz, com 5 alternativas, níveis diferentes sobre o ensino de ADS, que tem as disciplinas Banco de dados, Programação WEB, Qualidade e Teste de Software, Segurança da Informação, Design Digital, Sistemas Embarcados, Programação Mobile, Fundamentos da Informática, Análise e Projeto de Sistemas, Técnicas de programação e algoritmos e volte um JSON da seguinte forma:
        [
            {
                "titulo_questao": "(Título da questão com até 150 caracteres)",
                "disciplina": "(disciplina da pergunta)",
                "alternativas": [["(texto da alternativa)", (1 para correta ou 0 para incorreta)]],
                "dificuldade": "(um número de 0 à 2 conforme a dificuldade da pergunta)"
            }
        ]
    '''
)

response_text = response.text.strip()

# Remove aspas triplas, se existirem
if (response_text.startswith("'''") and response_text.endswith("'''")) or \
   (response_text.startswith('"""') and response_text.endswith('"""')):
    response_text = response_text[3:-3].strip()

# Converte para lista de dicionários Python
questoes = json.loads(response_text)

questoes2 = [
    {
        "titulo_questao": "Título questão",
        "disciplina": "Disciplina questão",
        "alternativas": [
            ["alternativa 1", 0],
            ["alternativa 2", 0],
            ["alternativa 3", 0],
            ["alternativa 4", 0],
            ["alternativa 5", 1]
        ],
        "dificuldade": 1
    }
]

# Exemplo: printar o título da primeira questão
print(questoes[0]['titulo_questao'])

dbname = 'railway',
host = 'gondola.proxy.rlwy.net',
port = '41562',
user = 'postgres',
password = 'xLZRRPNWFgRqeSHuNjvZRSZqErtetuCO'

def inserir_questao(questoes2):
    if (questoes):
        con = psycopg2.connect(
            dbname = dbname,
            host = host,
            port = port,
            user = user,
            password = password
        )
        sql_insert = f'''
            INSERT INTO quizz.question
            (id, question_statement, discipline_id, difficulty)
            VALUES(gen_random_uuid(), '', ?, 0);
        '''
    else:
        print('Questões não foram criadas corretamente !')