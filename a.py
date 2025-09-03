import re

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
    print(info['pergunta'])
    print("Alternativas:\n")
    for alternativa in info['alternativas']:
        print(f"{alternativa}")  # Exibe apenas o título da alternativa
    print(f"\nResposta correta: {info['resposta_correta']}")
