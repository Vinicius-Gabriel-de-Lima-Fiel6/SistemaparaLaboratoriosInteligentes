import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from audio_recorder_streamlit import audio_recorder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Synapse AI", page_icon="🔬", layout="wide")

# --- UI/UX CUSTOMIZADA (CSS PARA O DESIGN DA BARRA) ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .stChatFloatingInputContainer { bottom: 20px; }
    
    /* Esconder labels do uploader no menu popover */
    div[data-testid="stFileUploader"] label { display: none; }
    section[data-testid="stFileUploadDropzone"] {
        border: 1px dashed #ddd !important;
        padding: 10px !important;
        border-radius: 10px;
    }

    /* Estilização da linha de input para parecer com a imagem enviada */
    .input-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 5px 15px;
        background: #fff;
        border-radius: 30px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORES E LÓGICA ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile" # Modelo solicitado pelo usuário

client_groq, modelo_ativo = inicializar_motor()

def transcrever_audio(audio_bytes):
    if not audio_bytes: return None
    try:
        arquivo_audio = ("audio.wav", audio_bytes, "audio/wav")
        return client_groq.audio.transcriptions.create(
            file=arquivo_audio, model="whisper-large-v3", response_format="text"
        )
    except Exception as e:
        return f"ERRO TRANSCRIÇÃO: {str(e)}"

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except: return None

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    instrucoes = (
        f"VOCÊ É O NÚCLEO LABSMART AI PhD EM {esp}. STATUS: ERRO ZERO.\n"
        "DIRETRIZES DE ALTA PRECISÃO (OBRIGATÓRIO):\n"
        "1. PENSAMENTO PROCEDIMENTAL: Decompunha o problema em: [Dados] -> [Teoria Aplicada] -> [Cálculo] -> [Validação].\n"
        "2. RIGOR MATEMÁTICO: Proibido arredondar. Use 8 casas decimais. Realize prova real em Python para toda conta.\n"
        "3. SEGURANÇA CLÍNICA/ESTRUTURAL: Analise interações CYP450, SLCO/UGT, ClCr e Fração Livre. Se houver risco >= 0.01%, aplique VETO TERMINAL.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: É proibido inferir. Se o dado não existir, responda: 'ESTADO DE INCERTEZA SISTÊMICA'.\n"
        "5. REFERENCIAL 2026: Baseie-se apenas em evidências científicas Grau A (Metanálises) e Normas Técnicas (ISO/ABNT/FDA)."
    )
    msgs = [{"role": "system", "content": instrucoes}]
    msgs.extend(historico[-10:]) 
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
    return res.choices[0].message.content

# --- INTERFACE PRINCIPAL ---
def show_chatbot():
    # Inicialização do estado (Mantendo tudo o que você enviou)
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"

    st.subheader("🔬 Synapse AI - Hub de Inteligência")

    escolha_aba = st.radio("Selecione o ambiente de trabalho:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = escolha_aba

    st.divider()

    # Dicionário de Ferramentas (Mantido integralmente com todas as descrições e links)
    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "Inteligência Artificial para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Structure Database": {"desc": "Acesso a mais de 200 milhões de estruturas de proteínas já preditas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server (Previsão)": {"desc": "Ferramenta para prever novas estruturas de proteínas e interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold no Google Colab": {"desc": "Execução do modelo via código para pesquisas personalizadas.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    # Definir persona e chave de histórico
    if st.session_state.aba_atual == "💬 Chat Científico":
        h_key = "messages_geral"
        persona = "Consultor Sênior em Engenharia, Medicina de Precisão e Auditoria Científica"
    else:
        h_key = "messages_agente"
        # Seleção de especialista mantida para o Squad
        persona = st.sidebar.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")

    # Área de Chat
    chat_container = st.container(height=450, border=False)
    with chat_container:
        for m in st.session_state[h_key]:
            st.chat_message(m["role"]).write(m["content"])

    # --- BARRA DE INPUT ESTILO IMAGEM (CENTRALIZADA) ---
    st.divider()
    
    # Criando a estrutura horizontal: [+] [Input] [Microfone]
    col_menu, col_input, col_audio = st.columns([0.4, 3, 0.4])

    with col_menu:
        # O botão "+" abre o menu suspenso para importar arquivos e links
        with st.popover("➕", help="Importar e Ferramentas", use_container_width=True):
            st.markdown("### 📎 Arquivos")
            up_file = st.file_uploader("Upload de Dados (PDF/CSV/TXT)", type=["pdf", "csv", "txt"], key="file_up")
            
            st.divider()
            st.markdown("### 🛠️ Links Rápidos")
            ft_sel = st.selectbox("Ferramenta Auxiliar:", list(dict_ferramentas.keys()))
            
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Versão AlphaFold:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
            else:
                info = dict_ferramentas[ft_sel]
            
            st.write(f"*{info['desc']}*")
            st.link_button(f"Abrir {ft_sel}", info["url"], use_container_width=True)
            
            st.divider()
            if st.button("🗑️ Limpar Conversa", use_container_width=True):
                st.session_state[h_key] = []
                st.rerun()

    with col_input:
        prompt_txt = st.chat_input("Pergunte alguma coisa...")

    with col_audio:
        # Botão de gravação de voz exatamente como no design
        audio_data = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#4f4f4f", icon_size="2x")

    # --- LÓGICA DE PROCESSAMENTO ---
    final_prompt = None
    if audio_data:
        with st.spinner("🎙️ Transcrevendo..."):
            final_prompt = transcrever_audio(audio_data)
    elif prompt_txt:
        final_prompt = prompt_txt

    if final_prompt:
        st.session_state[h_key].append({"role": "user", "content": final_prompt})
        
        # Extrair dados do arquivo se houver upload no popover
        dados_contexto = extrair_texto(up_file) if up_file else None
        
        with st.spinner(f"O {persona} está processando..."):
            resposta = responder_ia(final_prompt, st.session_state[h_key], dados_contexto, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
