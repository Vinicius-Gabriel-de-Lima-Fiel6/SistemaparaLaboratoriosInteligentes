import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# --- MOTOR GROQ ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Chave não configurada."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

# --- PROCESSADOR DE VÍDEO (CORRETO PARA O SERVIDOR) ---
class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        # O YOLO processa aqui o frame enviado pelo seu navegador
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

    def executar_fluxo_agente(self, objetivo, dados=None):
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        prompt = f"""Data: {data_hoje}. Pedido: {objetivo}. 
        Diretriz: Responda de forma proporcional (curta para saudações, detalhada para ciência). 
        Estilo limpo. Dados: {dados}"""
        
        messages = [
            {"role": "system", "content": "Você é o LabSmart AI, assistente científico direto e adaptativo."},
            {"role": "user", "content": prompt}
        ]
        try:
            res = self.client.chat.completions.create(model=modelo_ativo, messages=messages, temperature=0.4)
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro: {str(e)}"

def show_chatbot():
    st.title("🔬 LabSmart AI")
    if "ia_engine" not in st.session_state:
        st.session_state.ia_engine = LabSmartAI()
    bot = st.session_state.ia_engine

    with st.sidebar:
        st.header("Monitoramento")
        # USANDO WEBRTC PARA EVITAR ERROS DE INDEX DA CÂMERA
        if st.toggle("🎥 Ativar Câmera do Notebook"):
            webrtc_streamer(
                key="yolo-stream",
                video_processor_factory=lambda: VideoProcessor(bot.get_yolo_model()),
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                media_stream_constraints={"video": True, "audio": False},
            )
        st.divider()
        up = st.file_uploader("Dados", type=["csv", "txt"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Como posso ajudar?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            dados_txt = up.getvalue().decode("utf-8") if up else None
            resposta = bot.executar_fluxo_agente(prompt, dados_txt)
            st.markdown(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})
