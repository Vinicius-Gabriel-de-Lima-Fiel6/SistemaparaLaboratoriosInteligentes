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

# --- 1. CONFIGURAÇÕES E CONEXÕES (IGUAL AO SEU ORIGINAL) ---
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

# --- 2. CLASSES DE SUPORTE (MANTIDAS) ---
class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.model(img)
        return results[0].plot()

# Classe para carregar o modelo YOLO sem travar o sistema
class YOLOManager:
    def __init__(self):
        self.model = None
    def get_model(self):
        if self.model is None:
            self.model = YOLO("yolov8n.pt")
        return self.model

if "yolo_manager" not in st.session_state:
    st.session_state.yolo_manager = YOLOManager()

# --- 3. FUNÇÕES AUXILIARES DE IA (MEMÓRIA E ARQUIVOS) ---
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

def gerar_resposta_ia(prompt, historico, dados_arquivo=None, especialista="Geral"):
    messages = [{"role": "system", "content": f"Você é o LabSmart AI atuando como {especialista}. Use o histórico e os arquivos fornecidos."}]
    # MEMÓRIA DE CONTEXTO (Passa o que já foi dito)
    for msg in historico[-10:]:
        messages.append(msg)
    
    conteudo_final = f"DADOS DO ARQUIVO: {dados_arquivo}\n\nPERGUNTA: {prompt}" if dados_arquivo else prompt
    messages.append({"role": "user", "content": conteudo_final})
    
    res = client_groq.chat.completions.create(model=modelo_ativo, messages=messages, temperature=0.4)
    return res.choices[0].message.content

# --- 4. FUNÇÃO PRINCIPAL (TOTALMENTE RESTAURADA) ---
def show_chatbot():
    st.title("🔬 LabSmart AI - Hub Científico")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # CRIAÇÃO DAS SUB-ABAS (SÓ ACRESCENTEI ISSO PARA ORGANIZAR)
    aba_chat, aba_agentes = st.tabs(["💬 Chat & Memória", "👥 Agentes Especialistas"])

    with aba_chat:
        col_c, col_v = st.columns([2, 1])
        
        with col_v:
            st.subheader("👁️ Visão & Arquivos")
            cam = st.toggle("Ativar Câmera YOLO")
            if cam:
                webrtc_streamer(key="yolo", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_manager.get_model()))
            
            st.divider()
            up = st.file_uploader("📎 Analisar PDF, CSV ou TXT", type=["pdf", "csv", "txt"])

        with col_c:
            # Exibe histórico (Memória)
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            if p := st.chat_input("Como posso ajudar no laboratório?"):
                st.session_state.messages.append({"role": "user", "content": p})
                with st.chat_message("user"): st.markdown(p)
                
                with st.chat_message("assistant"):
                    with st.spinner("Pensando..."):
                        txt = extrair_texto_arquivo(up)
                        resposta = gerar_resposta_ia(p, st.session_state.messages, txt)
                        st.markdown(resposta)
                        st.session_state.messages.append({"role": "assistant", "content": resposta})

    with aba_agentes:
        st.subheader("👥 Squad de Agentes Especialistas")
        agente = st.selectbox("Escolha o Especialista:", ["Bioquímico Sênior", "Escritor Técnico", "Auditor de Qualidade", "Enxame (Todos)"])
        tarefa = st.text_area("Descreva a tarefa complexa:")
        
        if st.button("🚀 Iniciar Processamento"):
            with st.spinner("Agentes trabalhando..."):
                res_ag = gerar_resposta_ia(tarefa, st.session_state.messages, especialista=agente)
                st.markdown(res_ag)

# Linha que o seu sistema (app.py) chama
if __name__ == "__main__":
    show_chatbot()
