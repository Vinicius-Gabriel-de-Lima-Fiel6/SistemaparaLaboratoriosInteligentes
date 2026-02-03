import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LabSmart AI", layout="wide", initial_sidebar_state="collapsed")

# --- FIX CSS: ALINHAMENTO HORIZONTAL SEM FLUTUAÇÃO ---
st.markdown("""
    <style>
    /* Remove o espaço em branco excessivo no topo */
    .block-container { padding-top: 1rem; }
    
    /* Força as colunas a se alinharem na base (bottom) para o input */
    [data-testid="column"] {
        display: flex;
        align-items: flex-end !important;
        justify-content: center;
        padding-bottom: 5px;
    }

    /* Estilização dos botões para ficarem fixos na barra */
    .stPopover, .stMicRecorder {
        margin-bottom: 12px !important;
    }

    /* Ajuste de largura do input para não quebrar a linha */
    .stChatInputContainer {
        padding-bottom: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE INTELIGÊNCIA ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

# --- FUNÇÕES TÉCNICAS (Originais) ---
def transcrever_audio(audio_bytes):
    if not client_groq or not audio_bytes: return None
    try:
        audio_file = io.BytesIO(audio_bytes); audio_file.name = "audio.wav"
        transcription = client_groq.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3",
            response_format="text", language="pt"
        )
        return transcription
    except: return None

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
        "2. RIGOR MATEMÁTICO: Proibido arredondar. Use 8 casas decimais.\n"
        "3. SEGURANÇA CLÍNICA/ESTRUTURAL: Analise interações CYP450, SLCO/UGT, ClCr e Fração Livre.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: Responda 'ESTADO DE INCERTEZA SISTÊMICA' se faltar dado.\n"
        "5. REFERENCIAL 2026: Baseie-se apenas em evidências científicas Grau A."
    )
    msgs = [{"role": "system", "content": instrucoes}]
    msgs.extend(historico[-10:])
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except: return "⚠️ Instabilidade na conexão. Tente novamente."

# --- INTERFACE ---
def show_chatbot():
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    
    st.subheader("🔬 LabSmart AI - Hub de Inteligência")
    escolha_aba = st.radio("Ambiente:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True, label_visibility="collapsed")
    st.session_state.aba_atual = escolha_aba
    st.divider()

    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "IA para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Structure Database": {"desc": "200 milhões de estruturas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server (Previsão)": {"desc": "Prever novas estruturas.", "url": "https://alphafoldserver.com/"},
                "AlphaFold no Google Colab": {"desc": "Execução via código.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    if st.session_state.aba_atual == "💬 Chat Científico":
        h_key, persona = "messages_geral", "Consultor Sênior"
    else:
        h_key = "messages_agente"
        col_s, _ = st.columns([1, 2]); persona = col_s.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])

    chat_container = st.container(height=480, border=False)
    with chat_container:
        for m in st.session_state[h_key]:
            st.chat_message(m["role"]).write(m["content"])

    # --- BARRA DE INPUT ESTILO FOTO (FIXA NA BASE) ---
    input_zone = st.container()
    with input_zone:
        col_plus, col_mic, col_txt = st.columns([0.06, 0.06, 0.88])
        
        with col_plus:
            with st.popover("➕", use_container_width=True):
                up_file = st.file_uploader("Upload", type=["pdf", "csv", "txt"])
                st.divider()
                ft_sel = st.selectbox("Ferramenta:", list(dict_ferramentas.keys()))
                if ft_sel == "AlphaFold":
                    sub = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                    info = dict_ferramentas["AlphaFold"]["sub"][sub]
                else: info = dict_ferramentas[ft_sel]
                st.caption(info["desc"])
                st.link_button("Abrir", info["url"], use_container_width=True)
                if st.button("🗑️ Limpar", type="primary", use_container_width=True):
                    st.session_state[h_key] = []; st.rerun()

        with col_mic:
            audio = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=f"mic_{h_key}")

        with col_txt:
            prompt = st.chat_input("Digite sua dúvida técnica...")

    # Processamento
    entrada = None
    if prompt: entrada = prompt
    elif audio:
        with st.spinner("..."): entrada = transcrever_audio(audio['bytes'])

    if entrada:
        st.session_state[h_key].append({"role": "user", "content": entrada})
        chat_container.chat_message("user").write(entrada)
        dados_doc = extrair_texto(up_file) if 'up_file' in locals() and up_file else None
        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                resposta = responder_ia(entrada, st.session_state[h_key], dados_doc, persona)
                st.write(resposta)
                st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
