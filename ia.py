import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from supabase import create_client
import PyPDF2
import io

# --- 1. CONFIGURAÇÕES E CONEXÕES (MANTIDAS) ---
# Conexão com o Banco de Dados na Nuvem
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Configure a GROQ_API_KEY nos Secrets do Streamlit."
    modelo = "llama-3.3-70b-versatile"
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

# --- 2. AGENTES E PROCESSAMENTO (APERFEIÇOADOS) ---
AGENTES = {
    "Bioquímico Sênior": "Especialista em reações químicas e protocolos.",
    "Escritor Técnico": "Especialista em redação de POPs e relatórios.",
    "Planejador Estratégico": "Gestão de estoque e eficiência.",
    "Auditor de Qualidade": "Normas RDC, ISO e conformidade."
}

class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.model(img)
        return results[0].plot()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = client_groq

    def get_yolo_model(self):
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        return self.yolo_model

    def extrair_texto_arquivo(self, upload_file):
        if upload_file is None: return None
        try:
            if upload_file.name.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(upload_file.read()))
                return "".join([page.extract_text() for page in pdf_reader.pages])
            elif upload_file.name.endswith('.csv'):
                return pd.read_csv(upload_file).to_string()
            return upload_file.read().decode("utf-8")
        except: return "Erro na extração."

    def executar_fluxo_agente(self, objetivo, historico_chat, dados=None, agente_nome="Geral", modo_enxame=False):
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        contexto = f"Você é {agente_nome}." if not modo_enxame else "Vocês são um enxame de especialistas."
        
        messages = [{"role": "system", "content": f"{contexto} Use a memória do chat abaixo. Data: {data_hoje}"}]
        for msg in historico_chat[-10:]: # MEMÓRIA DE CONTEXTO
            messages.append(msg)
            
        prompt_final = f"{objetivo}\n\nDADOS EXTRAS:\n{dados}" if dados else objetivo
        messages.append({"role": "user", "content": prompt_final})

        res = self.client.chat.completions.create(model=modelo_ativo, messages=messages, temperature=0.3)
        return res.choices[0].message.content

# --- 3. FUNÇÃO DE CÁLCULO/VISUAL (MANTIDA) ---
def render_hommel(saude, fogo, reat, esp):
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;">
        <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555;">
            <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{fogo}</div>
            <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">{reat}</div>
            <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{saude}</div>
            <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-size: 0.7em;">{esp if esp else ''}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÃO PRINCIPAL (NOME RESTAURADO PARA show_chatbot) ---
def show_chatbot():
    # Inicialização de motores
    if "ia_engine" not in st.session_state: st.session_state.ia_engine = LabSmartAI()
    if "messages" not in st.session_state: st.session_state.messages = []
    
    user_data = st.session_state.get('user_data', {'org_name': 'Default', 'role': 'ADM'})
    org_usuario = user_data.get('org_name')

    st.title("🔬 LabSmart AI - Sistema Integrado")

    # Sistema de Abas para organizar as novas funções sem quebrar as antigas
    tab_substancias, tab_ia, tab_agentes = st.tabs(["💊 Inventário & Segurança", "🤖 Chat com Memória", "👥 Squad de Agentes"])

    with tab_substancias:
        # --- AQUI FICA TODO O SEU CÓDIGO ORIGINAL DE SUBSTÂNCIAS ---
        # (Cadastro, Tabela, Botões de Excel Online, Diamante de Hommel)
        st.header("Gerenciamento de Substâncias")
        
        # Exemplo da sua lógica de exportação facilitada
        res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            c1, c2 = st.columns(2)
            c1.download_button("📥 Baixar CSV para análise", df.to_csv().encode('utf-8'), "estoque.csv")
            c2.link_button("🌐 Abrir Excel Online", "https://excel.new")

    with tab_ia:
        # --- CHAT COM MEMÓRIA E ARQUIVOS (PDF, CSV, TXT) ---
        col_chat, col_docs = st.columns([2, 1])
        with col_docs:
            st.markdown("### 📎 Documentos e Visão")
            up = st.file_uploader("Upload PDF/CSV/TXT", type=["pdf", "csv", "txt"])
            if st.toggle("Ativar Câmera YOLO"):
                webrtc_streamer(key="yolo", video_processor_factory=lambda: VideoProcessor(st.session_state.ia_engine.get_yolo_model()))

        with col_chat:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.markdown(m["content"])

            if p := st.chat_input("Pergunte sobre o histórico ou arquivos..."):
                st.session_state.messages.append({"role": "user", "content": p})
                st.chat_message("user").markdown(p)
                with st.chat_message("assistant"):
                    dados = st.session_state.ia_engine.extrair_texto_arquivo(up)
                    r = st.session_state.ia_engine.executar_fluxo_agente(p, st.session_state.messages, dados)
                    st.markdown(r)
                    st.session_state.messages.append({"role": "assistant", "content": r})

    with tab_agentes:
        # --- SISTEMA DE AGENTES ESPECIALISTAS ---
        st.header("Central de Agentes")
        modo = st.radio("Escolha o modo:", ["Individual", "Enxame (Todos Juntos)"])
        tarefa = st.text_area("O que os agentes devem fazer?")
        if st.button("🚀 Iniciar Agentes"):
            res_ag = st.session_state.ia_engine.executar_fluxo_agente(tarefa, st.session_state.messages, modo_enxame=(modo=="Enxame (Todos Juntos)"))
            st.markdown(res_ag)

# Chamada final que o Streamlit procura (Corrigida conforme sua imagem)
if __name__ == "__main__":
    show_chatbot()
