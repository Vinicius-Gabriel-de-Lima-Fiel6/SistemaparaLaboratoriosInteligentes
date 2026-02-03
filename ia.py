import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from streamlit_mic_recorder import mic_recorder  # Biblioteca para capturar áudio

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="LabSmart AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PROFISSIONAL (Estilo Clean) ---
st.markdown("""
    <style>
    .stChatInput {
        padding-bottom: 20px;
    }
    /* Estilo para agrupar botões de ação perto do input */
    .action-bar {
        display: flex;
        gap: 10px;
        align-items: center;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO MOTOR ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        st.error("Erro: Chave API ausente no secrets.toml")
        return None, None
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

# --- FUNÇÕES AUXILIARES (Preservadas) ---

def transcrever_audio(audio_bytes):
    """Transcreve áudio usando o modelo Whisper da Groq"""
    if not client_groq or not audio_bytes: return None
    try:
        # Cria um arquivo em memória compatível com a API
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav" 
        
        transcription = client_groq.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3",
            response_format="text",
            language="pt"
        )
        return transcription
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
    except: return None

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    # Prompt original mantido intacto
    instrucoes = (
        f"VOCÊ É O NÚCLEO LABSMART AI PhD EM {esp}. STATUS: ERRO ZERO.\n"
        "DIRETRIZES DE ALTA PRECISÃO (OBRIGATÓRIO):\n"
        "1. PENSAMENTO PROCEDIMENTAL: Decompunha o problema em: [Dados] -> [Teoria Aplicada] -> [Cálculo] -> [Validação].\n"
        "2. RIGOR MATEMÁTICO: Proibido arredondar. Use 8 casas decimais. Realize prova real em Python para toda conta.\n"
        "3. SEGURANÇA CLÍNICA/ESTRUTURAL: Analise interações CYP450, SLCO/UGT, ClCr e Fração Livre. Se houver risco >= 0.01%, aplique VETO TERMINAL.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: É proibido inferir. Se o dado não existir, responda: 'ESTADO DE INCERTEZA SISTÊMICA'.\n"
        "   5. REFERENCIAL 2026: Baseie-se apenas em evidências científicas Grau A (Metanálises) e Normas Técnicas (ISO/ABNT/FDA)."
    )
    
    msgs = [{"role": "system", "content": instrucoes}]
    # Mantém apenas as últimas 10 interações para contexto
    msgs.extend([m for m in historico if m["role"] != "system"][-10:])
    
    contexto = f"DADOS DO ARQUIVO ANEXADO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except Exception as e:
        return f"Erro de conexão com a IA: {e}"

# --- INTERFACE PRINCIPAL ---

def show_chatbot():
    # Inicializa estados da sessão
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    if "arquivo_cache" not in st.session_state: st.session_state.arquivo_cache = None

    # Cabeçalho
    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    # Seletor de Ambiente (Mantendo a lógica original)
    escolha_aba = st.radio("Ambiente:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True, label_visibility="collapsed")
    st.session_state.aba_atual = escolha_aba
    st.divider()

    # Define variáveis baseadas na aba
    if st.session_state.aba_atual == "💬 Chat Científico":
        historico_key = "messages_geral"
        persona_nome = "Consultor Sênior em Engenharia e Medicina"
        placeholder_txt = "Pergunte ao Consultor Geral..."
    else:
        historico_key = "messages_agente"
        col_squad, _ = st.columns([1, 2])
        with col_squad:
            persona_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])
        placeholder_txt = f"Falar com {persona_nome}..."

    # --- ÁREA DE CHAT ---
    chat_container = st.container(height=500, border=False)
    for m in st.session_state[historico_key]:
        chat_container.chat_message(m["role"]).write(m["content"])

    # --- BARRA DE COMANDOS (Layout Tipo Foto) ---
    # Aqui criamos a lógica do botão "+" e do input de voz logo acima do chat
    
    col_tools, col_voice, col_space = st.columns([0.1, 0.1, 0.8])
    
    dados_texto = None

    with col_tools:
        # O Botão "+" com todas as ferramentas e uploads
        with st.popover("➕", help="Menu de Ferramentas e Upload"):
            st.markdown("### 📎 Anexar Arquivo")
            arquivo_up = st.file_uploader("Carregar PDF/TXT/CSV", type=["pdf", "csv", "txt"], key=f"up_{historico_key}")
            
            if arquivo_up:
                # Processa o arquivo apenas se mudou
                dados_texto = extrair_texto(arquivo_up)
                st.success("Arquivo processado na memória!")

            st.divider()
            st.markdown("### 🛠️ Links & Ferramentas")
            
            # Lista de ferramentas do código original
            st.link_button("🌐 Lovable (Interface)", "https://lovable.dev/", use_container_width=True)
            st.link_button("📊 Gamma (Slides)", "https://gamma.app/", use_container_width=True)
            st.link_button("🤖 Manus (Agente)", "https://manus.ai/", use_container_width=True)
            st.link_button("🔎 Perplexity (Busca)", "https://www.perplexity.ai/", use_container_width=True)
            
            with st.expander("🧬 AlphaFold"):
                st.link_button("Database", "https://alphafold.ebi.ac.uk/")
                st.link_button("Server Prediction", "https://alphafoldserver.com/")
                st.link_button("Google Colab", "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb")

            st.divider()
            if st.button("🗑️ Limpar Chat Atual"):
                st.session_state[historico_key] = []
                st.rerun()

    with col_voice:
        # Componente de Gravação de Voz
        audio_data = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="⏹️", 
            just_once=True,
            key=f"mic_{historico_key}"
        )

    # --- PROCESSAMENTO DE ENTRADA (Voz ou Texto) ---
    prompt_usuario = st.chat_input(placeholder_txt)
    prompt_final = None

    # Prioridade 1: Texto digitado
    if prompt_usuario:
        prompt_final = prompt_usuario
    
    # Prioridade 2: Áudio gravado (se não houver texto)
    elif audio_data:
        with st.spinner("Transcrevendo áudio..."):
            texto_transcrito = transcrever_audio(audio_data['bytes'])
            if texto_transcrito:
                prompt_final = texto_transcrito

    # Execução da Resposta
    if prompt_final:
        # Adiciona mensagem do usuário
        st.session_state[historico_key].append({"role": "user", "content": prompt_final})
        chat_container.chat_message("user").write(prompt_final)

        # Gera resposta da IA
        with st.chat_message("assistant"):
            with st.spinner(f"{persona_nome} está analisando..."):
                resposta = responder_ia(
                    prompt_final, 
                    st.session_state[historico_key], 
                    dados=dados_texto, # Passa o texto do arquivo se estiver no popover
                    esp=persona_nome
                )
                st.write(resposta)
        
        # Salva resposta no histórico
        st.session_state[historico_key].append({"role": "assistant", "content": resposta})
        
        # Força atualização para limpar o buffer de áudio se necessário
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
