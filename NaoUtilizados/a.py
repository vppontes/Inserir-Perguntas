import re
import psycopg2

dbname = 'railway',
host = 'gondola.proxy.rlwy.net',
port = '41562',
user = 'postgres',
password = 'xLZRRPNWFgRqeSHuNjvZRSZqErtetuCO'

def inserir_curso(nome_curso):
    con = psycopg2.connect(
        dbname = dbname,
        host = host,
        port = port,
        user = user,
        password = password
    )
    sql_insert = f'''
        INSERT INTO quizz.question
        (question_statement, discipline_id, difficulty)
        VALUES(%s, %s, %s);
    '''

    cursor = con.cursor()
    cursor.execute(sql_insert, ( nome_curso, '195a4b30-f73a-4832-9dfa-443e8c754203', 0 ))
    con.commit()
    cursor.close()
    con.close()

def atualizar_curso():
    con = psycopg2.connect(
        dbname = dbname,
        host = host,
        port = port,
        user = user,
        password = password
    )
    sql_update = f'''
        UPDATE quizz.question
        SET question_statement='%s', discipline_id=?, difficulty=0
        WHERE id='%s';
    '''

# Função para processar o arquivo e extrair as perguntas e respostas
def extrair_info_do_arquivo(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as file:
        conteudo = file.read()

    # Expressões regulares para capturar as perguntas, alternativas e respostas corretas
    padrao_pergunta = r'(\d.+?)(?=\n|Alternativas)'  # Captura perguntas seguidas de alternativas
    padrao_respostas = r'[a-d]\)\s*(.*)'  # Captura as alternativas, removendo a letra e parênteses
    padrao_resposta_correta = r'(\d+)\. (a|b|c|d)\) (.*)'  # Captura a resposta correta

    conteudo_sem_gabarito = re.sub(r'Gabarito\n.*', '', conteudo, flags=re.DOTALL)

    perguntas = re.findall(padrao_pergunta, conteudo_sem_gabarito, re.DOTALL)
    respostas = re.findall(padrao_respostas, conteudo)
    respostas_corretas = re.findall(padrao_resposta_correta, conteudo)

    respostas = [re.sub(r'\(.*?\)', '', r) for r in respostas]

    # Organizando as informações
    perguntas_respostas = []
    for i, pergunta in enumerate(perguntas):
        pergunta_sem_numero = re.sub(r'^\d+\.\s*', '', pergunta).strip()
        alternativas = [resposta.strip() for resposta in respostas[i*4:(i+1)*4]]  # Extrai só o título das alternativas
        resposta_correta = next((r[2] for r in respostas_corretas if r[0] == str(i+1)), None)
        perguntas_respostas.append({
            'pergunta': pergunta_sem_numero,
            'alternativas': alternativas,
            'resposta_correta': resposta_correta
        })

    return perguntas_respostas

# Caminho do arquivo de texto
caminho_arquivo = 'quizz_perguntas_e_respostas.txt'

# Extraindo as informações
informacoes = extrair_info_do_arquivo(caminho_arquivo)

# Exibindo as informações extraídas
for info in informacoes:
    print("-" * 40)
    inserir_curso(info['pergunta'])
    print("Alternativas:\n")
    for alternativa in info['alternativas']:
        print(f"{alternativa}")  # Exibe apenas o título da alternativa
    print(f"\nResposta correta: {info['resposta_correta']}")