import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io

# --- MOTOR DE INTELIGÊNCIA ---
def inicializar_motor():
    """Inicializa o cliente Groq com tratamento de erro."""
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente nos Secrets."
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, f"Erro de Conexão: {str(e)}"

client_groq, modelo_ativo = inicializar_motor()

# --- PROCESSAMENTO DE VÍDEO (VISÃO COMPUTACIONAL) ---
class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        # Aplica o modelo YOLO e renderiza as detecções no frame
        results = self.model(img)
        return results[0].plot()

# --- EXTRAÇÃO DE DADOS ---
def extrair_texto(arquivo):
    """Extrai conteúdo de PDF ou TXT com segurança."""
    if not arquivo: 
        return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            texto = "".join([p.extract_text() for p in leitor.pages])
            return texto
        return arquivo.read().decode("utf-8")
    except Exception as e: 
        return f"Erro na leitura do arquivo: {str(e)}"

# --- LÓGICA DO NÚCLEO IA ---
def responder_ia(prompt, historico, dados=None, esp="Geral"):
    """Envia o prompt para o modelo com diretrizes de 2026 e rigor científico."""
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
    # Mantém apenas as últimas 10 mensagens para otimizar o contexto
    msgs.extend(historico[-10:]) 
    
    contexto = f"DADOS DO ARQUIVO ANEXADO: {dados}\n\nPERGUNTA DO USUÁRIO: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(
            model=modelo_ativo, 
            messages=msgs, 
            temperature=0.0 # Rigor total, sem criatividade aleatória
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ALERTA DE SISTEMA: Falha na comunicação com o Núcleo IA. Erro: {str(e)}"

# --- INTERFACE PRINCIPAL DO CHATBOT ---
def show_chatbot():
    # --- INJEÇÃO DE CSS PARA CORREÇÃO DE CORES (PRETO & ESMERALDA) ---
    st.markdown("""
        <style>
        /* Fundo Geral */
        .stApp { background-color: #000000 !important; }
        
        /* Forçar texto branco em labels e componentes */
        h1, h2, h3, h4, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }

        /* Estilização das Mensagens do Chat */
        [data-testid="stChatMessage"] {
            background-color: #0d1117 !important;
            border: 1px solid #30363d !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }

        /* CORREÇÃO DO SELECTBOX E POPOVER (Problema das fotos) */
        div[data-baseweb="select"] > div, 
        div[data-testid="stPopover"] > button,
        div[data-baseweb="input"] > div {
            background-color: #0d1117 !important;
            color: #ffffff !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }
        
        /* Texto dentro da Selectbox aberta */
        div[role="listbox"] {
            background-color: #0d1117 !important;
            color: white !important;
        }

        /* Botão Verde Esmeralda */
        div.stButton > button {
            background-color: #10b981 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            width: 100%;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #34d399 !important;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
        }

        /* Input de Chat (Barra inferior) */
        [data-testid="stChatInput"] {
            background-color: #000000 !important;
        }
        [data-testid="stChatInput"] textarea {
            background-color: #0d1117 !important;
            color: white !important;
            border: 1px solid #30363d !important;
        }

        /* Radio Buttons */
        div[data-testid="stMarkdownContainer"] p { color: white !important; }
        </style>
    """, unsafe_allow_html=True)

    # Inicialização de Estados
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    if "yolo_model" not in st.session_state: 
        try:
            st.session_state.yolo_model = YOLO("yolov8n.pt")
        except:
            st.session_state.yolo_model = None

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    escolha_aba = st.radio(
        "Selecione o ambiente de trabalho:", 
        ["💬 Chat Científico", "👥 Squad de Agentes"], 
        horizontal=True
    )
    st.session_state.aba_atual = escolha_aba

    st.divider()

    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "IA para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Structure Database": {"desc": "Acesso a 200 milhões de estruturas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server (Previsão)": {"desc": "Prever novas estruturas e interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold no Google Colab": {"desc": "Execução via código personalizado.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    # --- LAYOUT DINÂMICO ---
    if st.session_state.aba_atual == "💬 Chat Científico":
        col_chat, col_tools = st.columns([3, 1])
        with col_tools:
            st.write("### ⚙️ Ferramentas")
            if st.toggle("🎥 Visão YOLO", key="tgl_v1"):
                if st.session_state.yolo_model:
                    webrtc_streamer(key="stream_v1", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
                else:
                    st.error("Modelo YOLO não carregado.")
            
            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages_geral = []
                st.rerun()
            
            st.write("---")
            st.write("🛠️ **Auxiliares**")
            ft_sel = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_geral")
            
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_geral")
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
            else:
                info = dict_ferramentas[ft_sel]

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info["desc"])
                st.link_button(f"Abrir {ft_sel}", info["url"], use_container_width=True)

        with col_chat:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_geral:
                chat_container.chat_message(m["role"]).write(m["content"])
            
    else: # --- ABA SQUAD DE AGENTES ---
        col_chat, col_tools = st.columns([3, 1])
        with col_tools:
            st.write("### 👥 Squad")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            up_agente = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            
            if st.button("🗑️ Limpar Squad"):
                st.session_state.messages_agente = []
                st.rerun()

            st.write("---")
            st.write("🛠️ **Auxiliares**")
            ft_sel_ag = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_agente")
            
            if ft_sel_ag == "AlphaFold":
                sub_sel_ag = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_agente")
                info_ag = dict_ferramentas["AlphaFold"]["sub"][sub_sel_ag]
            else:
                info_ag = dict_ferramentas[ft_sel_ag]

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info_ag["desc"])
                st.link_button(f"Abrir {ft_sel_ag}", info_ag["url"], use_container_width=True)

        with col_chat:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_agente:
                chat_container.chat_message(m["role"]).write(m["content"])

    # --- ENTRADA DE CHAT ---
    if prompt := st.chat_input("Digite sua mensagem técnica..."):
        if st.session_state.aba_atual == "💬 Chat Científico":
            h_key = "messages_geral"
            # Extração de texto segura
            dados_txt = extrair_texto(up_geral) if up_geral else None
            persona = "Consultor Sênior em Engenharia e Medicina de Precisão"
        else:
            h_key = "messages_agente"
            dados_txt = extrair_texto(up_agente) if up_agente else None
            persona = esp_nome

        # Adiciona pergunta ao histórico
        st.session_state[h_key].append({"role": "user", "content": prompt})
        
        with st.spinner(f"O {persona} está processando dados..."):
            resposta = responder_ia(prompt, st.session_state[h_key], dados_txt, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        
        st.rerun()

# --- EXECUÇÃO ---
if __name__ == "__main__":
    show_chatbot()
