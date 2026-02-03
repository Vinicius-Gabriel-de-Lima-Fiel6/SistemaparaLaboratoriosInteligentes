import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LabSmart AI", layout="wide", initial_sidebar_state="collapsed")

# CSS para alinhar os botões lado a lado com o input (estilo profissional)
st.markdown("""
    <style>
    .stChatInputContainer { padding-bottom: 20px; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    .stPopover, .stMicRecorder { margin-top: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE INTELIGÊNCIA ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

# --- FUNÇÕES TÉCNICAS ---

def transcrever_audio(audio_bytes):
    if not client_groq or not audio_bytes: return None
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        transcription = client_groq.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3",
            response_format="text",
            language="pt"
        )
        return transcription
    except:
        return None

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except:
        return None

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    # Instruções de sistema (Pre-prompts) - Injetadas apenas no backend
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
    # Filtra o histórico para garantir que prompts de sistema antigos não sejam exibidos no chat
    for m in historico[-10:]:
        msgs.append({"role": m["role"], "content": m["content"]})
    
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except:
        return "⚠️ Ocorreu uma instabilidade na conexão com o Núcleo. Por favor, tente novamente."

# --- INTERFACE ---

def show_chatbot():
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "💬 Chat Científico"

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    escolha_aba = st.radio("Ambiente:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True, label_visibility="collapsed")
    st.session_state.aba_atual = escolha_aba
    st.divider()

    # Dicionário de Ferramentas (Original Completo)
    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "Inteligência Artificial para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Structure Database": {"desc": "Acesso a mais de 200 milhões de estruturas já preditas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server (Previsão)": {"desc": "Ferramenta para prever novas estruturas e interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold no Google Colab": {"desc": "Execução do modelo via código.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    if st.session_state.aba_atual == "💬 Chat Científico":
        h_key, persona = "messages_geral", "Consultor Sênior"
    else:
        h_key = "messages_agente"
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            persona = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])

    # Exibição das mensagens
    chat_container = st.container(height=500, border=False)
    for m in st.session_state[h_key]:
        chat_container.chat_message(m["role"]).write(m["content"])

    # --- BARRA DE COMANDO (LADO A LADO) ---
    col_plus, col_mic, col_txt = st.columns([0.07, 0.07, 0.86])
    
    with col_plus:
        with st.popover("➕", use_container_width=True):
            up_file = st.file_uploader("Upload de Dados", type=["pdf", "csv", "txt"])
            st.divider()
            ft_sel = st.selectbox("Ferramentas:", list(dict_ferramentas.keys()))
            if ft_sel == "AlphaFold":
                sub = st.selectbox("Sub-tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                info = dict_ferramentas["AlphaFold"]["sub"][sub]
            else:
                info = dict_ferramentas[ft_sel]
            st.caption(info["desc"])
            st.link_button("Abrir", info["url"], use_container_width=True)
            if st.button("🗑️ Limpar Chat", type="primary", use_container_width=True):
                st.session_state[h_key] = []
                st.rerun()

    with col_mic:
        audio = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=f"mic_{h_key}")

    prompt = st.chat_input("Digite ou fale a sua dúvida técnica...")

    # --- PROCESSAMENTO ---
    entrada = None
    if prompt:
        entrada = prompt
    elif audio:
        with st.spinner("A processar áudio..."):
            entrada = transcrever_audio(audio['bytes'])

    if entrada:
        st.session_state[h_key].append({"role": "user", "content": entrada})
        chat_container.chat_message("user").write(entrada)
        
        dados_doc = extrair_texto(up_file) if 'up_file' in locals() and up_file else None

        with st.chat_message("assistant"):
            with st.spinner(f"O {persona} está a analisar..."):
                resposta = responder_ia(entrada, st.session_state[h_key], dados_doc, persona)
                st.write(resposta)
                st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
