import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from core import TIPOS_ARQUIVOS_VALIDOS, CONFIG_MODELOS, monta_chain

st.set_page_config(page_title='Genius', page_icon='🧠')


def pagina_chat():
    st.header('🧠 Bem-vindo ao Genius', divider=True)

    chain = st.session_state.get('chain')
    if chain is None:
        st.error('Configure e inicialize o Genius na barra lateral.')
        st.stop()

    if 'historico' not in st.session_state:
        st.session_state['historico'] = []
    historico = st.session_state['historico']

    for mensagem in historico:
        tipo = 'human' if isinstance(mensagem, HumanMessage) else 'ai'
        chat = st.chat_message(tipo)
        chat.markdown(mensagem.content)

    input_usuario = st.chat_input('Fale com o Genius')
    if input_usuario:
        chat = st.chat_message('human')
        chat.markdown(input_usuario)

        chat = st.chat_message('ai')
        resposta = chat.write_stream(chain.stream({
            'input': input_usuario,
            'chat_history': historico,
        }))

        historico.append(HumanMessage(content=input_usuario))
        historico.append(AIMessage(content=resposta))
        st.session_state['historico'] = historico


def _valor_padrao_api_key(provedor):
    chave_sessao = f'api_key_{provedor}'
    if chave_sessao in st.session_state:
        return st.session_state[chave_sessao]
    try:
        return st.secrets.get(f'{provedor.upper()}_API_KEY', '')
    except Exception:
        return ''


def sidebar():
    tabs = st.tabs(['Upload de Arquivos', 'Seleção de Modelos'])

    arquivo = None
    with tabs[0]:
        tipo_arquivo = st.selectbox('Selecione o tipo de arquivo', TIPOS_ARQUIVOS_VALIDOS)
        if tipo_arquivo == 'Site':
            arquivo = st.text_input('Digite a url do site')
        elif tipo_arquivo == 'Youtube':
            arquivo = st.text_input('Digite a url do vídeo')
        elif tipo_arquivo == 'Pdf':
            arquivo = st.file_uploader('Faça o upload do arquivo pdf', type=['pdf'])
        elif tipo_arquivo == 'Csv':
            arquivo = st.file_uploader('Faça o upload do arquivo csv', type=['csv'])
        elif tipo_arquivo == 'Txt':
            arquivo = st.file_uploader('Faça o upload do arquivo txt', type=['txt'])

    with tabs[1]:
        provedor = st.selectbox('Selecione o provedor do modelo', list(CONFIG_MODELOS.keys()))
        modelo = st.selectbox('Selecione o modelo', CONFIG_MODELOS[provedor]['modelos'])
        api_key = st.text_input(
            f'Adicione a api key para o provedor {provedor}',
            value=_valor_padrao_api_key(provedor),
            type='password',
        )
        st.session_state[f'api_key_{provedor}'] = api_key

    if st.button('Inicializar Genius', use_container_width=True):
        if not arquivo:
            st.warning('Selecione ou envie um arquivo antes de inicializar.')
        elif not api_key:
            st.warning('Informe a api key do provedor selecionado.')
        else:
            with st.spinner('Carregando o Genius...'):
                st.session_state['chain'] = monta_chain(provedor, modelo, api_key, tipo_arquivo, arquivo)
            st.success('Genius inicializado com sucesso!')

    if st.button('Apagar Histórico de Conversa', use_container_width=True):
        st.session_state['historico'] = []


def main():
    with st.sidebar:
        sidebar()
    pagina_chat()


if __name__ == '__main__':
    main()
