import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from audio_recorder_streamlit import audio_recorder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LabSmart AI", page_icon="🔬", layout="wide")

# --- UI/UX CUSTOMIZADA (ESTILO CHAT ATUAL) ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .stChatFloatingInputContainer { bottom: 20px; }
    
    /* Container para alinhar botões e input na mesma linha */
    .input-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px;
        background: #f9f9f9;
        border-radius: 15px;
        border: 1px solid #ddd;
    }
    
    /* Ajuste para esconder labels e compactar uploader */
    div[data-testid="stFileUploader"] label { display: none; }
    section[data-testid="stFileUploadDropzone"] { border: none; padding: 0; min-height: unset; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORES E LÓGICA ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

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
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")
    
    aba = st.radio("Ambiente:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = aba

    # Dicionário de Ferramentas (Mantido conforme original)
    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente para execução de tarefas digitais.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "IA para predição de estruturas de proteínas.",
            "sub": {
                "Database": {"desc": "200 milhões de estruturas.", "url": "https://alphafold.ebi.ac.uk/"},
                "Server": {"desc": "Prever novas estruturas.", "url": "https://alphafoldserver.com/"}
            }
        }
    }

    # Seleção de Histórico e Persona
    if st.session_state.aba_atual == "💬 Chat Científico":
        h_key = "messages_geral"
        persona = "Consultor Sênior em Engenharia e Medicina de Precisão"
    else:
        h_key = "messages_agente"
        persona = st.sidebar.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])

    # AREA DE CHAT
    chat_container = st.container(height=450, border=False)
    with chat_container:
        for m in st.session_state[h_key]:
            st.chat_message(m["role"]).write(m["content"])

    # --- BARRA DE INPUT INTEGRADA (VOZ + ARQUIVO + TEXTO) ---
    st.divider()
    col_v, col_u, col_i, col_r = st.columns([0.2, 0.4, 3, 0.2])

    with col_v:
        # Microfone à esquerda
        audio_data = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#4f4f4f", icon_size="2x")
    
    with col_u:
        # Upload discreto no meio
        up_file = st.file_uploader("Upload", type=["pdf", "csv", "txt"], label_visibility="collapsed")

    with col_i:
        # Campo de texto central
        prompt_txt = st.chat_input("Digite sua consulta ou use o áudio...")

    with col_r:
        if st.button("🗑️", help="Limpar conversa"):
            st.session_state[h_key] = []
            st.rerun()

    # --- LÓGICA DE EXECUÇÃO ---
    final_prompt = None
    if audio_data:
        with st.spinner("🎙️..."):
            final_prompt = transcrever_audio(audio_data)
    elif prompt_txt:
        final_prompt = prompt_txt

    if final_prompt:
        st.session_state[h_key].append({"role": "user", "content": final_prompt})
        dados = extrair_texto(up_file)
        
        with st.spinner(f"Processando via {persona}..."):
            resposta = responder_ia(final_prompt, st.session_state[h_key], dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

    # Barra Lateral com as Ferramentas Originais (Para não poluir o chat)
    with st.sidebar:
        st.write("### 🛠️ Auxiliares")
        ft_sel = st.selectbox("Ferramenta:", list(dict_ferramentas.keys()))
        if ft_sel == "AlphaFold":
            sub = st.selectbox("Versão:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
            info = dict_ferramentas["AlphaFold"]["sub"][sub]
        else:
            info = dict_ferramentas[ft_sel]
        
        st.info(info["desc"])
        st.link_button("Abrir Ferramenta", info["url"], use_container_width=True)

if __name__ == "__main__":
    show_chatbot()
