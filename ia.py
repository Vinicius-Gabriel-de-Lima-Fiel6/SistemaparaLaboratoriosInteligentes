import streamlit as st
import pandas as pd
import google.generativeai as genai
import cv2
import numpy as np
from ultralytics import YOLO

# --- CONFIGURAÇÃO DA IA (GOOGLE GEMINI) ---
# Certifique-se de adicionar GOOGLE_API_KEY nos Secrets do Streamlit Cloud
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model_gemini = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error("Erro ao carregar a chave da API do Google. Verifique os Secrets.")

class LabSmartAI:
    def __init__(self):
        # O modelo YOLO será carregado apenas quando solicitado para economizar memória
        self.yolo_model = None

    def get_ai_answer(self, user_text: str):
        """Conecta diretamente ao Gemini para respostas inteligentes"""
        try:
            # Instrução de sistema para manter o foco científico
            contexto = "Você é um Assistente de Laboratório Inteligente especializado em Química e Física. "
            response = model_gemini.generate_content(contexto + user_text)
            return response.text
        except Exception as e:
            return f"Erro ao conectar com o Gemini: {e}"

    def run_object_detection(self):
        """Roda o Detector YOLO (Nota: OpenCV local só abre janela se rodar no seu PC)"""
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        
        cap = cv2.VideoCapture(0)
        st.toast("Câmera ativada! Pressione 'Q' na janela da imagem para fechar.")
        
        while True:
            success, img = cap.read()
            if not success: break
            results = self.yolo_model.track(img, persist=True)
            for result in results:
                img = result.plot()
            
            cv2.imshow("LabSmartAI - Detector de Objetos", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

def show_chatbot():
    st.header("🤖 Assistente Científico com IA")

    # Inicializa a classe
    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # --- 1. BOTÕES DE PESQUISA CIENTÍFICA (LINKS EXTERNOS) ---
    st.subheader("📚 Bases de Pesquisa & IA Especializada")
    col_links = st.columns(4)
    with col_links[0]:
        st.link_button("🧪 PubMed", "https://pubmed.ncbi.nlm.nih.gov/", use_container_width=True)
    with col_links[1]:
        st.link_button("🔬 Scielo", "https://scielo.org/", use_container_width=True)
    with col_links[2]:
        st.link_button("🎓 Scholar", "https://scholar.google.com/", use_container_width=True)
    with col_links[3]:
        st.link_button("🧠 Perplexity", "https://www.perplexity.ai/", use_container_width=True)

    st.divider()

    # --- 2. SIDEBAR E VISÃO ---
    with st.sidebar:
        st.subheader("Ferramentas de Visão")
        if st.button("🚀 Ativar Detector YOLO", use_container_width=True):
            bot.run_object_detection()
        st.info("Nota: O detector abre uma janela local no computador onde o servidor está rodando.")

    # --- 3. INTERFACE DE CHAT ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Renderiza histórico
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada do usuário
    if prompt := st.chat_input("Pergunte qualquer coisa ao Gemini..."):
        # Adiciona pergunta do usuário
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Resposta da IA do Google
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = bot.get_ai_answer(prompt)
                st.markdown(resposta)
                st.session_state.chat_history.append({"role": "assistant", "content": resposta})


