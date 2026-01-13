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

# --- 3. LÓGICA DE RESPOSTA COM MEMÓRIA ---
def processar_resposta(prompt, historico_key, dados_arquivo=None, especialista="Geral"):
    # Filtra o histórico da aba específica
    messages = [{"role": "system", "content": f"Você é o LabSmart AI ({especialista}). Use o histórico da conversa para manter o contexto."}]
    for msg in st.session_state[historico_key][-10:]:
        messages.append(msg)
    
    conteudo = f"CONTEXTO DO ARQUIVO: {dados_arquivo}\n\nPERGUNTA: {prompt}" if dados_arquivo else prompt
    messages.append({"role": "user", "content": conteudo})
    
    res = client_groq.chat.completions.create(model=modelo_ativo, messages=messages, temperature=0.4)
    return res.choices[0].message.content

# --- 4. INTERFACE PRINCIPAL ---
def show_chatbot():
    # Inicializa históricos separados para não misturar as conversas das abas
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agentes" not in st.session_state: st.session_state.messages_agentes = []

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    aba_chat, aba_agentes = st.tabs(["💬 Chat Científico", "👥 Especialistas & Planejamento"])

    # --- ABA 1: CHAT GERAL ---
    with aba_chat:
        col_chat, col_tools = st.columns([2, 1])
        
        with col_tools:
            st.write("### 🛠️ Recursos")
            cam = st.toggle("🎥 Câmera YOLO", key="cam_geral")
            if cam:
                webrtc_streamer(key="stream_geral", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
            st.divider()
            up_geral = st.file_uploader("📎 Anexar arquivo", type=["pdf", "csv", "txt"], key="up_geral")

        with col_chat:
            # Exibe as mensagens como no WhatsApp/ChatGPT
            for m in st.session_state.messages_geral:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            if p := st.chat_input("Perqunte qualquer coisa...", key="input_geral"):
                st.session_state.messages_geral.append({"role": "user", "content": p})
                st.rerun() # Atualiza para mostrar a mensagem do usuário imediatamente

            # Processamento da resposta (se a última mensagem for do usuário)
            if st.session_state.messages_geral and st.session_state.messages_geral[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    with st.spinner("Analisando..."):
                        txt = extrair_texto_arquivo(up_geral)
                        resp = processar_resposta(st.session_state.messages_geral[-1]["content"], "messages_geral", txt)
                        st.markdown(resp)
                        st.session_state.messages_geral.append({"role": "assistant", "content": resp})

    # --- ABA 2: AGENTES ---
    with aba_agentes:
        col_ag, col_cfg = st.columns([2, 1])
        
        with col_cfg:
            st.write("### 👥 Configuração")
            especialista = st.selectbox("Selecione o Agente:", ["Bioquímico Sênior", "Escritor Técnico", "Auditor de Qualidade"])
            st.info(f"O {especialista} analisará o histórico deste chat.")
            up_ag = st.file_uploader("📎 Dados para o Agente", type=["pdf", "csv", "txt"], key="up_ag")
            if st.button("🗑️ Limpar Conversa do Agente"):
                st.session_state.messages_agentes = []
                st.rerun()

        with col_ag:
            # Interface de Chat para os Agentes
            for m in st.session_state.messages_agentes:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            if p_ag := st.chat_input("Envie sua tarefa para o agente...", key="input_ag"):
                st.session_state.messages_agentes.append({"role": "user", "content": p_ag})
                st.rerun()

            if st.session_state.messages_agentes and st.session_state.messages_agentes[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    with st.spinner(f"{especialista} está trabalhando..."):
                        txt_ag = extrair_texto_arquivo(up_ag)
                        resp_ag = processar_resposta(st.session_state.messages_agentes[-1]["content"], "messages_agentes", txt_ag, especialista)
                        st.markdown(resp_ag)
                        st.session_state.messages_agentes.append({"role": "assistant", "content": resp_ag})

if __name__ == "__main__":
    show_chatbot()
