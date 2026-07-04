import os
import tempfile

from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from loaders import carrega_site, carrega_youtube, carrega_pdf, carrega_csv, carrega_txt

TIPOS_ARQUIVOS_VALIDOS = ['Site', 'Youtube', 'Pdf', 'Csv', 'Txt']

CONFIG_MODELOS = {
    'Groq': {
        'modelos': ['llama-3.1-70b-versatile', 'gemma2-9b-it', 'mixtral-8x7b-32768'],
        'chat': ChatGroq,
    },
    'OpenAI': {
        'modelos': ['gpt-4o-mini', 'gpt-4o', 'o1-preview', 'o1-mini'],
        'chat': ChatOpenAI,
    },
}

SYSTEM_MESSAGE_TEMPLATE = '''Você é um assistente amigável chamado Genius.
Você possui acesso às seguintes informações vindas de um documento {tipo_arquivo}:

####
{documento}
####

Utilize as informações fornecidas para basear as suas respostas.

Sempre que houver $ na sua saída, substitua por S.

Se a informação do documento for algo como "Just a moment...Enable JavaScript and cookies to continue"
sugira ao usuário carregar novamente o Genius!'''


def _carrega_arquivo_enviado(arquivo, sufixo, funcao_loader):
    # Streamlit Cloud roda um único container para todos os usuários da app,
    # então o arquivo temporário precisa ser removido logo após o uso para
    # não acumular disco entre sessões concorrentes.
    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as temp:
        temp.write(arquivo.read())
        nome_temp = temp.name
    try:
        return funcao_loader(nome_temp)
    finally:
        os.remove(nome_temp)


def carrega_arquivos(tipo_arquivo, arquivo):
    if tipo_arquivo == 'Site':
        return carrega_site(arquivo)
    if tipo_arquivo == 'Youtube':
        return carrega_youtube(arquivo)
    if tipo_arquivo == 'Pdf':
        return _carrega_arquivo_enviado(arquivo, '.pdf', carrega_pdf)
    if tipo_arquivo == 'Csv':
        return _carrega_arquivo_enviado(arquivo, '.csv', carrega_csv)
    if tipo_arquivo == 'Txt':
        return _carrega_arquivo_enviado(arquivo, '.txt', carrega_txt)
    raise ValueError(f'Tipo de arquivo inválido: {tipo_arquivo}')


def monta_chain(provedor, modelo, api_key, tipo_arquivo, arquivo):
    documento = carrega_arquivos(tipo_arquivo, arquivo)
    system_message = SYSTEM_MESSAGE_TEMPLATE.format(tipo_arquivo=tipo_arquivo, documento=documento)

    template = ChatPromptTemplate.from_messages([
        ('system', system_message),
        ('placeholder', '{chat_history}'),
        ('user', '{input}'),
    ])
    chat = CONFIG_MODELOS[provedor]['chat'](model=modelo, api_key=api_key)
    return template | chat
