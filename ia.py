import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# --- CONFIGURAÇÃO DO MOTOR GROQ ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Configure a GROQ_API_KEY nos Secrets do Streamlit."
    
    # Modelo estável e potente para 2026
    modelo = "llama-3.3-70b-versatile"
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

# --- PROCESSADOR DE VÍDEO (YOLO VIA NAVEGADOR) ---
class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model

    def transform(self, frame):
        # Converte o frame recebido do navegador (WebRTC) para array numpy
        img = frame.to_ndarray(format="bgr24")
        
        # Executa a detecção do YOLOv8
        results = self.model(img)
        
        # Retorna o frame anotado com as caixas de detecção
        return results[0].plot()

# --- CLASSE PRINCIPAL DA IA ---
class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = client_groq

    def get_yolo_model(self):
        """Carrega o modelo YOLO apenas se a câmera for ativada"""
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        return self.yolo_model

    def executar_fluxo_agente(self, objetivo, dados=None):
        """Lógica de resposta proporcional e científica"""
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        prompt_sistema = f"""
        Data Atual: {data_hoje}
        Usuário solicitou: {objetivo}
        
        DIRETRIZES:
        1. PROPORCIONALIDADE: Se for uma saudação ou algo simples, responda de forma curta e amigável.
        2. PROFUNDIDADE: Se for um pedido técnico, projeto ou análise, realize uma pesquisa profunda (deep search) em sua base de dados e entregue uma resposta científica detalhada.
        3. ESTILO: Resposta limpa, integrada, sem divisões de agentes (estilo ChatGPT/Gemini).
        4. DADOS: Se houver dados fornecidos abaixo, incorpore na análise:
        {dados if dados else "Nenhum dado extra fornecido."}
        """

        messages = [
            {"role": "system", "content": "Você é o LabSmart AI, um assistente científico de alto nível que adapta o tom à necessidade do usuário."},
            {"role": "user", "content": prompt_sistema}
        ]

        try:
            res = self.client.chat.completions.create(
                model=modelo_ativo,
                messages=messages,
                temperature=0.4,
                max_tokens=6000
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro na IA: {str(e)}"

# --- INTERFACE STREAMLIT ---
def show_chatbot():
    st.set_page_config(page_title="LabSmart AI", layout="wide")
    st.title("🔬 LabSmart AI - Hub Científico")

    if "ia_engine" not in st.session_state:
        st.session_state.ia_engine = LabSmartAI()
    
    bot = st.session_state.ia_engine

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("👁️ Visão Computacional")
        ativar_camera = st.toggle("Ativar Câmera do Notebook")
        
        if ativar_camera:
            st.info("Conectando à câmera...")
            webrtc_streamer(
                key="yolo-vision",
                video_processor_factory=lambda: VideoProcessor(bot.get_yolo_model()),
                async_processing=True,
                # Servidores STUN robustos para evitar erro de conexão
                rtc_configuration={
                    "iceServers": [
                        {"urls": ["stun:stun.l.google.com:19302"]},
                        {"urls": ["stun:stun1.l.google.com:19302"]},
                        {"urls": ["stun:stun.services.mozilla.com"]}
                    ]
                },
                media_stream_constraints={"video": True, "audio": False},
            )
        
        st.divider()
        st.header("📂 Arquivos")
        up = st.file_uploader("Upload de CSV ou TXT", type=["csv", "txt"])
        
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.messages = []
            st.rerun()

    # --- ÁREA DE CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Exibe histórico
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Input do usuário
    if prompt := st.chat_input("Como posso ajudar no laboratório hoje?"):
        # Adiciona mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Gera resposta
        with st.chat_message("assistant"):
            with st.spinner("Analisando e pesquisando..."):
                dados_txt = up.getvalue().decode("utf-8", errors="ignore") if up else None
                resposta = bot.executar_fluxo_agente(prompt, dados_txt)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

        # Botão para baixar a resposta
        st.download_button("📥 Baixar Relatório", resposta, file_name="labsmart_report.md")

if __name__ == "__main__":
    show_chatbot()
