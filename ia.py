import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import PyPDF2
import io
import logging

# Configuração de logs para evitar poluição no terminal
logging.getLogger("aioice").setLevel(logging.ERROR)
logging.getLogger("aiortc").setLevel(logging.ERROR)

# --- CARREGAMENTO DO MODELO COM CACHE (MUITO MAIS ESTÁVEL) ---
@st.cache_resource
def carregar_modelo_yolo():
    return YOLO("yolov8n.pt")

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, str(e)

client_groq, modelo_ativo = inicializar_motor()

class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        try:
            img = frame.to_ndarray(format="bgr24")
            if img is not None and self.model is not None:
                results = self.model(img, verbose=False)
                return results[0].plot()
            return img
        except:
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
    except Exception as e:
        return f"Erro na IA: {e}"

def show_chatbot():
    # --- INICIALIZAÇÃO SEGURA (RESOLVE O ATTRIBUTEERROR) ---
    yolo_model = carregar_modelo_yolo()

    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    
    st.subheader("🔬 LabSmart AI - Hub de Inteligência")
    escolha_aba = st.radio("Selecione o ambiente de trabalho:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.divider()

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

    if escolha_aba == "💬 Chat Científico":
        col_c1, col_t1 = st.columns([3, 1])
        with col_t1:
            st.write("### ⚙️ Ferramentas")
            if st.toggle("🎥 Visão YOLO", key="tgl_v1"):
                # Passamos o modelo direto da função de cache, sem depender do session_state
                webrtc_streamer(
                    key="vision_stable",
                    mode=WebRtcMode.SENDRECV,
                    video_processor_factory=lambda: VideoProcessor(yolo_model),
                    rtc_configuration={
                        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                    },
                    media_stream_constraints={
                        "video": {"facingMode": "environment"},
                        "audio": False
                    },
                    async_processing=True
                )
            
            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages_geral = []
                st.rerun()
            
            st.write("---")
            ft_sel = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_geral")
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
            else:
                info = dict_ferramentas[ft_sel]
            
            with st.popover("Ver Detalhes"):
                st.write(info["desc"])
                st.link_button("Abrir", info["url"])

        with col_c1:
            chat_box = st.container(height=500)
            for m in st.session_state.messages_geral:
                chat_box.chat_message(m["role"]).write(m["content"])
            
    else:
        col_c2, col_t2 = st.columns([3, 1])
        with col_t2:
            st.write("### 👥 Squad")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            up_agente = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            if st.button("🗑️ Limpar Squad"):
                st.session_state.messages_agente = []
                st.rerun()

        with col_c2:
            chat_box_ag = st.container(height=500)
            for m in st.session_state.messages_agente:
                chat_box_ag.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input("Digite sua mensagem..."):
        h_key = "messages_geral" if escolha_aba == "💬 Chat Científico" else "messages_agente"
        persona = "Consultor Sênior PhD" if escolha_aba == "💬 Chat Científico" else esp_nome
        
        st.session_state[h_key].append({"role": "user", "content": prompt})
        with st.spinner("Analisando..."):
            doc_ativa = up_geral if escolha_aba == "💬 Chat Científico" else up_agente
            dados_doc = extrair_texto(doc_ativa)
            resposta = responder_ia(prompt, st.session_state[h_key], dados_doc, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
