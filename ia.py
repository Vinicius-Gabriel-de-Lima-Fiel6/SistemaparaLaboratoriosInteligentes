import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LabSmart AI", layout="wide", initial_sidebar_state="collapsed")

# CSS para emular a interface da foto e limpar o design
st.markdown("""
    <style>
    .stChatInputContainer { padding-bottom: 20px; }
    .stChatMessage { border-radius: 15px; }
    /* Ajuste para o botão de voz e ferramentas ficarem alinhados */
    .stPopover { display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE INTELIGÊNCIA ---
def inicializar_motor():
    try:
        if "GROQ_API_KEY" not in st.secrets:
            return None, "Chave API não configurada nos Secrets."
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, f"Erro ao iniciar motor: {str(e)}"

client_groq, modelo_ativo = inicializar_motor()

# --- FUNÇÕES DE TRATAMENTO DE ERROS E DADOS ---

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
    except Exception:
        st.warning("🎧 Ocorreu um pequeno ruído na comunicação. Pode repetir, por favor?")
        return None

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except Exception:
        st.error("📂 Ops! Tive um problema ao ler este arquivo. Verifique se ele não está protegido.")
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
    msgs.extend(historico[-10:])
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except Exception:
        return "⚠️ Estou com uma instabilidade momentânea na conexão. Poderia tentar enviar sua mensagem novamente?"

# --- INTERFACE ---

def show_chatbot():
    # Inicialização de Estados (Mantendo o original)
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "💬 Chat Científico"

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    # Tabs para alternar entre Geral e Squad (Estilo original)
    aba_escolhida = st.radio("Ambiente:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = aba_escolhida
    
    st.divider()

    # Variáveis de contexto baseadas na aba
    if st.session_state.aba_atual == "💬 Chat Científico":
        h_key = "messages_geral"
        persona = "Consultor Sênior em Engenharia, Medicina de Precisão e Auditoria Científica"
    else:
        h_key = "messages_agente"
        persona = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])

    # Dicionário de Ferramentas (Recuperado do seu código original)
    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "IA para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Structure Database": {"desc": "Acesso a mais de 200 milhões de estruturas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server (Previsão)": {"desc": "Prever novas estruturas e interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold no Google Colab": {"desc": "Execução via código.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    # Container de Chat
    chat_container = st.container(height=450, border=False)
    with chat_container:
        for m in st.session_state[h_key]:
            st.chat_message(m["role"]).write(m["content"])

    # --- BARRA DE INPUT ESTILO "FOTO" ---
    col_plus, col_mic, col_space = st.columns([0.08, 0.08, 0.84])
    
    up_file = None
    
    with col_plus:
        # Botão "+" que abre as ferramentas e upload na mesma aba
        with st.popover("➕", help="Arquivos e Ferramentas"):
            st.markdown("### 📎 Anexar Dados")
            up_file = st.file_uploader("Upload (PDF/CSV/TXT)", type=["pdf", "csv", "txt"], key=f"up_{st.session_state.aba_atual}")
            
            st.divider()
            st.markdown("### 🛠️ Auxiliares")
            ft_sel = st.selectbox("Ferramenta:", list(dict_ferramentas.keys()))
            
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
            else:
                info = dict_ferramentas[ft_sel]
            
            st.info(info["desc"])
            st.link_button("Abrir Ferramenta", info["url"], use_container_width=True)
            
            if st.button("🗑️ Limpar Conversa", use_container_width=True):
                st.session_state[h_key] = []
                st.rerun()

    with col_mic:
        # Gravação de voz
        audio_data = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=f"mic_{h_key}")

    # Logica de entrada
    prompt = st.chat_input("Pergunte alguma coisa...")
    entrada_final = None

    if prompt:
        entrada_final = prompt
    elif audio_data:
        with st.spinner("Traduzindo sua voz..."):
            entrada_final = transcrever_audio(audio_data['bytes'])

    # Processamento da Resposta
    if entrada_final:
        st.session_state[h_key].append({"role": "user", "content": entrada_final})
        chat_container.chat_message("user").write(entrada_final)
        
        # Extração de texto do upload (se houver)
        dados_contexto = extrair_texto(up_file) if up_file else None

        with st.chat_message("assistant"):
            with st.spinner(f"{persona} está processando..."):
                resposta = responder_ia(entrada_final, st.session_state[h_key], dados_contexto, persona)
                st.write(resposta)
                st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
