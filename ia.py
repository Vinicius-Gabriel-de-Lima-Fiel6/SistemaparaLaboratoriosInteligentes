import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io
import logging

# 1. CONFIGURAÇÃO DE LOGS (Essencial para monitorar o servidor no GitHub)
logging.basicConfig(level=logging.INFO)

# 2. INICIALIZAÇÃO DE MOTORES (FORA DAS ABAS PARA ESTABILIDADE)

@st.cache_resource
def carregar_modelo_yolo():
    """Carrega o modelo globalmente. Se tiver o 'best.pt' treinado, substitua o nome aqui."""
    try:
        # O modelo yolov8n.pt será baixado automaticamente na primeira execução
        return YOLO("yolov8n.pt")
    except Exception as e:
        logging.error(f"Erro Crítico ao carregar YOLO: {e}")
        return None

def inicializar_motor_groq():
    """Inicializa a conexão com a Groq Cloud."""
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente nos st.secrets."
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, f"Erro na Groq: {e}"

# Instanciação dos motores globais
client_groq, modelo_ativo = inicializar_motor_groq()

# 3. CLASSE DE VISÃO COMPUTACIONAL (BLINDADA CONTRA THREAD ERRORS)

class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        # Recebemos o modelo no construtor. Isso evita o erro de session_state.
        self.model = model

    def transform(self, frame):
        try:
            img = frame.to_ndarray(format="bgr24")
            if self.model is not None:
                # Inferência configurada para rodar em CPU (padrão do GitHub/Streamlit Cloud)
                results = self.model(img, verbose=False)
                return results[0].plot()
            return img
        except Exception as e:
            # Em caso de erro no frame, retorna o frame original sem travar o sistema
            return frame.to_ndarray(format="bgr24")

# 4. FUNÇÕES DE SUPORTE (EXTRACÇÃO E IA)

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except Exception as e:
        logging.error(f"Erro na extração: {e}")
        return None

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    instrucoes = (
        f"VOCÊ É O NÚCLEO LABSMART AI PhD EM {esp}. STATUS: ERRO ZERO.\n"
        "DIRETRIZES DE ALTA PRECISÃO (OBRIGATÓRIO):\n"
        "1. PENSAMENTO PROCEDIMENTAL: [Dados] -> [Teoria Aplicada] -> [Cálculo] -> [Validação].\n"
        "2. RIGOR MATEMÁTICO: Proibido arredondar. Use 8 casas decimais.\n"
        "3. SEGURANÇA CLÍNICA/QUÍMICA: Analise riscos CYP450 e toxicidade. Se risco >= 0.01%, VETO TERMINAL.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: Responda 'ESTADO DE INCERTEZA SISTÊMICA' se o dado for inexistente.\n"
        "5. REFERENCIAL 2026: Baseado em Normas Técnicas ISO/ABNT e Meta-análises."
    )
    msgs = [{"role": "system", "content": instrucoes}]
    msgs.extend(historico[-10:]) 
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except Exception as e:
        return f"ERRO SISTÊMICO NA API: {e}"

# 5. INTERFACE DO USUÁRIO (STREAMLIT)

def show_chatbot():
    # Inicialização segura do session_state
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "💬 Chat Científico"
    
    # Carregamento do modelo em variável local (Garante que a thread do vídeo o encontre)
    modelo_yolo_instanciado = carregar_modelo_yolo()

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    escolha_aba = st.radio("Selecione o ambiente de trabalho:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = escolha_aba

    st.divider()

    # Catálogo de Ferramentas
    dict_ferramentas = {
        "Lovable": {"desc": "Prototipagem de sistemas internos.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Apresentações profissionais via IA.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de execução digital autônomo.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico verificado.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {"desc": "Predição proteica profunda (DeepMind).", "url": "https://alphafoldserver.com/"}
    }

    if st.session_state.aba_atual == "💬 Chat Científico":
        col_c1, col_t1 = st.columns([3, 1])
        with col_t1:
            st.write("### ⚙️ Ferramentas")
            
            # IMPLEMENTAÇÃO DE VISÃO RESILIENTE
            if st.toggle("🎥 Visão YOLO", key="tgl_v1"):
                if modelo_yolo_instanciado:
                    webrtc_streamer(
                        key="video_vision_lab",
                        video_processor_factory=lambda: VideoProcessor(modelo_yolo_instanciado),
                        rtc_configuration={
                            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                        },
                        media_stream_constraints={"video": True, "audio": False},
                        async_processing=True
                    )
                else:
                    st.error("Cérebro visual offline. Verifique os logs do servidor.")

            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages_geral = []
                st.rerun()
            
            ft_sel = st.selectbox("Auxiliar:", list(dict_ferramentas.keys()), key="ft_geral")
            with st.popover("Ver Link", use_container_width=True):
                st.link_button(f"Abrir {ft_sel}", dict_ferramentas[ft_sel]["url"], use_container_width=True)

        with col_c1:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_geral:
                chat_container.chat_message(m["role"]).write(m["content"])
            
    else:
        # ABA SQUAD DE AGENTES (Lógica para especialistas)
        col_c2, col_t2 = st.columns([3, 1])
        with col_t2:
            st.write("### 👥 Squad")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            up_agente = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            if st.button("🗑️ Limpar Squad"):
                st.session_state.messages_agente = []
                st.rerun()

        with col_c2:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_agente:
                chat_container.chat_message(m["role"]).write(m["content"])

    # PROCESSAMENTO DE MENSAGENS (CHAT)
    if prompt := st.chat_input("Digite sua consulta técnica para o PhD..."):
        if st.session_state.aba_atual == "💬 Chat Científico":
            h_key = "messages_geral"
            doc_data = extrair_texto(up_geral) if up_geral else None
            persona_name = "Consultor Sênior PhD"
        else:
            h_key = "messages_agente"
            doc_data = extrair_texto(up_agente) if up_agente else None
            persona_name = esp_nome

        st.session_state[h_key].append({"role": "user", "content": prompt})
        with st.spinner(f"O {persona_name} está analisando os dados..."):
            resposta = responder_ia(prompt, st.session_state[h_key], doc_data, persona_name)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
