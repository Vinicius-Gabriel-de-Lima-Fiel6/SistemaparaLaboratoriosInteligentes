import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO

# --- MOTOR DE CONEXÃO GROQ ---
def inicializar_groq():
    try:
        if "GROQ_API_KEY" not in st.secrets:
            return None, "Chave GROQ_API_KEY não configurada nos Secrets."
        
        # O Groq é compatível com os servidores globais do Streamlit
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        # Modelo Llama 3.3 de 70 bilhões de parâmetros (Equivalente ao Gemini Pro)
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, f"Erro de conexão: {str(e)}"

# Inicialização global
motor_groq, modelo_ativo = inicializar_groq()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = motor_groq

    def get_ai_answer(self, user_text: str):
        if self.client is None:
            return f"IA Indisponível: {modelo_ativo}"
        try:
            # Chamada de chat para o Groq
            completion = self.client.chat.completions.create(
                model=modelo_ativo,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é o Assistente LabSmart, especialista em Química e Física. Responda de forma técnica e em português."
                    },
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Erro no processamento Groq: {e}"

    def run_object_detection(self):
        """Seu detector YOLO original"""
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        cap = cv2.VideoCapture(0)
        st.toast("Câmera ativada! Pressione 'Q' para sair.")
        while True:
            success, img = cap.read()
            if not success: break
            results = self.yolo_model.track(img, persist=True)
            for result in results:
                img = result.plot()
            cv2.imshow("LabSmartAI", img)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
        cap.release()
        cv2.destroyAllWindows()

# --- FUNÇÃO PRINCIPAL QUE O SEU APP.PY CHAMA ---
def show_chatbot():
    st.header("🤖 Assistente Científico (Motor Groq)")

    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # Painel de Status
    if bot.client:
        st.success(f"✅ Motor Ativo: **{modelo_ativo}** (Sem bloqueio regional)")
    else:
        st.error(f"❌ {modelo_ativo}")

    # Links Científicos
    st.subheader("📚 Bases de Pesquisa")
    cols = st.columns(4)
    with cols[0]: st.link_button("🧪 PubMed", "https://pubmed.ncbi.nlm.nih.gov/", use_container_width=True)
    with cols[1]: st.link_button("🔬 Scielo", "https://scielo.org/", use_container_width=True)
    with cols[2]: st.link_button("🎓 Scholar", "https://scholar.google.com/", use_container_width=True)
    with cols[3]: st.link_button("🧠 Perplexity", "https://www.perplexity.ai/", use_container_width=True)

    st.divider()

    # Chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte ao LabSmart via Groq..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("IA processando..."):
                resposta = bot.get_ai_answer(prompt)
                st.markdown(resposta)
                st.session_state.chat_history.append({"role": "assistant", "content": resposta})
