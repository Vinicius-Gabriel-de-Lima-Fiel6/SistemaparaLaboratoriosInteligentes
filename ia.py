import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from audio_recorder_streamlit import audio_recorder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SynapseAI", page_icon="🔬", layout="wide")

# --- UI/UX CUSTOMIZADA (CSS PARA ÍCONES E ALINHAMENTO) ---
st.markdown("""
    <style>
    /* Transforma o uploader em um ícone de clipe 📎 */
    div[data-testid="stFileUploader"] label { display: none; }
    section[data-testid="stFileUploadDropzone"] {
        border: none !important;
        padding: 0 !important;
        min-height: unset !important;
        background: transparent !important;
    }
    section[data-testid="stFileUploadDropzone"] div div { display: none; }
    section[data-testid="stFileUploadDropzone"]::before {
        content: '📎';
        font-size: 24px;
        cursor: pointer;
        padding: 8px;
        background: #f0f2f6;
        border-radius: 10px;
        display: flex;
        justify-content: center;
        transition: 0.3s;
    }
    section[data-testid="stFileUploadDropzone"]:hover::before { background: #dfe3e8; }
    
    /* Alinhamento da barra de chat e microfone */
    .stChatFloatingInputContainer { bottom: 20px; }
    [data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente nos secrets."
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
        st.error(f"Erro na transcrição: {e}")
        return None

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except Exception as e:
        return f"Erro na extração: {str(e)}"

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
    contexto_final = f"DADOS: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto_final})
    
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except Exception as e:
        return f"ERRO CRÍTICO: {str(e)}"

def show_chatbot():
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")
    aba = st.radio("Selecione o ambiente:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = aba
    st.divider()

    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para tarefas digitais.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico verificado.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "IA para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Database": {"desc": "200 milhões de estruturas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server": {"desc": "Previsão de novas interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold Colab": {"desc": "Execução via código.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    if st.session_state.aba_atual == "💬 Chat Científico":
        col_c, col_t = st.columns([3, 1])
        with col_t:
            st.write("### ⚙️ Ferramentas")
            up_geral = st.file_uploader("📎 Anexo", type=["pdf", "csv", "txt"], key="up_v1")
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages_geral = []
                st.rerun()
            st.divider()
            ft_sel = st.selectbox("Auxiliares:", list(dict_ferramentas.keys()), key="ft_geral")
            info = dict_ferramentas[ft_sel] if ft_sel != "AlphaFold" else dict_ferramentas["AlphaFold"]["sub"][st.selectbox("AlphaFold:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))]
            st.info(info["desc"])
            st.link_button("Abrir", info["url"], use_container_width=True)
        with col_c:
            cont = st.container(height=500, border=False)
            for m in st.session_state.messages_geral:
                cont.chat_message(m["role"]).write(m["content"])
    else:
        col_c, col_t = st.columns([3, 1])
        with col_t:
            st.write("### 👥 Squad")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            up_agente = st.file_uploader("📎 Anexo", type=["pdf", "csv", "txt"], key="up_v2")
            if st.button("🗑️ Limpar Squad"):
                st.session_state.messages_agente = []
                st.rerun()
        with col_c:
            cont = st.container(height=500, border=False)
            for m in st.session_state.messages_agente:
                cont.chat_message(m["role"]).write(m["content"])

    # BARRA DE INPUT MODERNA (MICROFONE + CHAT)
    st.divider()
    col_v, col_i = st.columns([0.2, 3.8])
    with col_v:
        audio_data = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#4f4f4f", icon_size="2x")
    with col_i:
        input_manual = st.chat_input("Digite sua consulta técnica...")

    final_prompt = None
    if audio_data:
        with st.spinner("Ouvindo..."):
            final_prompt = transcrever_audio(audio_data)
    elif input_manual:
        final_prompt = input_manual

    if final_prompt:
        h_key = "messages_geral" if st.session_state.aba_atual == "💬 Chat Científico" else "messages_agente"
        arquivo_atual = up_geral if st.session_state.aba_atual == "💬 Chat Científico" else up_agente
        dados = extrair_texto(arquivo_atual)
        persona = "Consultor Sênior PhD" if st.session_state.aba_atual == "💬 Chat Científico" else esp_nome

        st.session_state[h_key].append({"role": "user", "content": final_prompt})
        with st.spinner(f"Analisando via {persona}..."):
            resp = responder_ia(final_prompt, st.session_state[h_key], dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resp})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
