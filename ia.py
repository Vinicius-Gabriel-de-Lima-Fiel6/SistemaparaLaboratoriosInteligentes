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

# --- 1. CONFIGURAÇÕES INICIAIS ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API não configurada."
    modelo = "llama-3.3-70b-versatile"
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

# --- 2. COMPONENTES TÉCNICOS ---
class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.model(img)
        return results[0].plot()

if "yolo_model" not in st.session_state:
    st.session_state.yolo_model = YOLO("yolov8n.pt")

def extrair_texto_arquivo(arquivo):
    if arquivo is None: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        elif arquivo.name.endswith('.csv'):
            return pd.read_csv(arquivo).to_string()
        return arquivo.read().decode("utf-8")
    except: return None

def processar_resposta(prompt, historico_key, dados_arquivo=None, especialista="Geral"):
    messages = [{"role": "system", "content": f"Você é o LabSmart AI ({especialista}). Use o histórico para contexto."}]
    for msg in st.session_state[historico_key][-10:]:
        messages.append(msg)
    
    conteudo = f"ARQUIVO: {dados_arquivo}\n\nPERGUNTA: {prompt}" if dados_arquivo else prompt
    messages.append({"role": "user", "content": conteudo})
    
    res = client_groq.chat.completions.create(model=modelo_ativo, messages=messages, temperature=0.4)
    return res.choices[0].message.content

# --- 3. INTERFACE PRINCIPAL ---
def show_chatbot():
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agentes" not in st.session_state: st.session_state.messages_agentes = []

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    # Definimos a aba ativa para saber qual histórico usar
    aba_selecionada = st.tabs(["💬 Chat Científico", "👥 Especialistas"])
    
    # --- ABA 1: CHAT GERAL ---
    with aba_selecionada[0]:
        col_chat, col_tools = st.columns([3, 1])
        with col_tools:
            st.write("### 🛠️ Recursos")
            cam = st.toggle("🎥 Câmera YOLO", key="tgl_geral")
            if cam:
                webrtc_streamer(key="viz_geral", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
            up_geral = st.file_uploader("📎 Anexar", type=["pdf", "csv", "txt"], key="file_geral")

        with col_chat:
            # Mostra mensagens da Aba Geral
            for m in st.session_state.messages_geral:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

    # --- ABA 2: AGENTES ---
    with aba_selecionada[1]:
        col_ag, col_cfg = st.columns([3, 1])
        with col_cfg:
            st.write("### 👥 Agentes")
            esp = st.selectbox("Especialista:", ["Bioquímico Sênior", "Escritor Técnico", "Auditor"], key="sel_ag")
            up_ag = st.file_uploader("📎 Dados", type=["pdf", "csv", "txt"], key="file_ag")
        
        with col_ag:
            # Mostra mensagens da Aba Agentes
            for m in st.session_state.messages_agentes:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

    # --- 4. CAIXA DE INPUT FIXA NO RODAPÉ ---
    # Colocamos o input FORA das colunas para ele grudar no fundo da tela
    if prompt := st.chat_input("Como posso ajudar no laboratório agora?"):
        
        # Lógica para decidir em qual histórico salvar baseado na aba que o usuário está vendo
        # Nota: O Streamlit processa o input globalmente, então usamos um pequeno truque de estado
        if up_geral or "cam_geral" in st.session_state: # Se o usuário interagiu com ferramentas da aba 1
            hist_key = "messages_geral"
            doc = up_geral
            nome_esp = "Geral"
        else:
            hist_key = "messages_agentes"
            doc = up_ag
            nome_esp = esp

        # Adiciona mensagem do usuário
        st.session_state[hist_key].append({"role": "user", "content": prompt})
        
        # Gera resposta imediatamente
        with st.spinner("IA processando..."):
            txt_contexto = extrair_texto_arquivo(doc)
            resposta = processar_resposta(prompt, hist_key, txt_contexto, nome_esp)
            st.session_state[hist_key].append({"role": "assistant", "content": resposta})
        
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
