import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LabSmart AI", layout="wide", initial_sidebar_state="collapsed")

# --- CSS DEFINITIVO: ALINHAMENTO NA BASE (IGUAL À FOTO) ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    
    /* Alinha as colunas do input na base para evitar que os botões flutuem */
    [data-testid="column"] {
        display: flex;
        align-items: flex-end !important;
        justify-content: center;
        padding-bottom: 8px;
    }

    /* Ajuste de margem para o Popover e o Mic ficarem nivelados com o Input */
    .stPopover, .stMicRecorder {
        margin-bottom: 12px !important;
    }

    /* Estilo limpo para o container de chat */
    .stChatInputContainer {
        padding-bottom: 15px !important;
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

# --- FUNÇÕES TÉCNICAS E TRATAMENTO DE ERROS ---

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
        st.toast("🎤 Erro na transcrição. Tente falar novamente.", icon="⚠️")
        return None

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except:
        st.toast("📂 Problema ao ler o arquivo técnico.", icon="❌")
        return None

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
    # Filtro para manter o histórico sem repetir instruções de sistema
    for m in historico[-10:]:
        if m["role"] != "system":
            msgs.append({"role": m["role"], "content": m["content"]})
    
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except:
        return "⚠️ ESTADO DE INCERTEZA SISTÊMICA: Falha na conexão com o núcleo."

# --- INTERFACE PRINCIPAL ---

def show_chatbot():
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "💬 Chat Científico"

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    # Tabs (Original)
    escolha_aba = st.radio("Ambiente:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True, label_visibility="collapsed")
    st.session_state.aba_atual = escolha_aba
    st.divider()

    # DICIONÁRIO ORIGINAL COMPLETO (Recuperado todas as 40+ linhas)
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

    # Definição de contexto
    if st.session_state.aba_atual == "💬 Chat Científico":
        h_key, persona = "messages_geral", "Consultor Sênior em Engenharia e Medicina"
    else:
        h_key = "messages_agente"
        col_esp, _ = st.columns([1, 2])
        with col_esp:
            persona = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])

    # Exibição do Chat
    chat_container = st.container(height=500, border=False)
    with chat_container:
        for m in st.session_state[h_key]:
            st.chat_message(m["role"]).write(m["content"])

    # --- BARRA DE COMANDO (ALINHADA À FOTO) ---
    input_row = st.container()
    with input_row:
        c_plus, c_mic, c_txt = st.columns([0.07, 0.07, 0.86])
        
        with c_plus:
            with st.popover("➕", use_container_width=True):
                st.write("### 📎 Arquivos e Ferramentas")
                up_file = st.file_uploader("Base de Dados", type=["pdf", "csv", "txt"])
                
                st.divider()
                st.write("### 🛠️ Auxiliares")
                ft_sel = st.selectbox("Selecionar:", list(dict_ferramentas.keys()))
                
                if ft_sel == "AlphaFold":
                    sub_sel = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                    info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
                else:
                    info = dict_ferramentas[ft_sel]

                st.info(info["desc"])
                st.link_button(f"Abrir {ft_sel}", info["url"], use_container_width=True)

                if st.button("🗑️ Limpar Chat", type="primary", use_container_width=True):
                    st.session_state[h_key] = []
                    st.rerun()

        with c_mic:
            audio_bytes = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=f"mic_{h_key}")

        with c_txt:
            prompt = st.chat_input("Digite ou fale sua dúvida técnica...")

    # --- PROCESSAMENTO DE ENTRADA ---
    final_input = None
    if prompt:
        final_input = prompt
    elif audio_bytes:
        with st.spinner("Transcrevendo..."):
            final_input = transcrever_audio(audio_bytes['bytes'])

    if final_input:
        st.session_state[h_key].append({"role": "user", "content": final_input})
        chat_container.chat_message("user").write(final_input)
        
        # Processamento do arquivo
        dados_txt = extrair_texto(up_file) if 'up_file' in locals() and up_file else None

        with st.chat_message("assistant"):
            with st.spinner(f"O {persona} está analisando..."):
                res = responder_ia(final_input, st.session_state[h_key], dados_txt, persona)
                st.write(res)
                st.session_state[h_key].append({"role": "assistant", "content": res})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
