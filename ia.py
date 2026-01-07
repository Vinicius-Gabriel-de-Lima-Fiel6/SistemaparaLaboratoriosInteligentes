import streamlit as st
import pandas as pd
import google.generativeai as genai
import cv2
import numpy as np
from ultralytics import YOLO

# --- 1. MOTOR DE CONEXÃO (FORÇA BRUTA) ---
def inicializar_ia_final():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "Chave GOOGLE_API_KEY não encontrada nos Secrets."
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        
        # Força o transporte REST para evitar erros de versão beta
        genai.configure(api_key=api_key, transport='rest')
        
        # Lista de modelos para testar bloqueio regional
        modelos = ['gemini-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']
        
        for nome in modelos:
            try:
                model = genai.GenerativeModel(nome)
                # Teste rápido de conexão
                model.generate_content("Oi", generation_config={"max_output_tokens": 1})
                return model, nome
            except Exception as e:
                # Se for erro de localização, ele pula para o próximo modelo automaticamente
                continue
        
        return None, "Bloqueio Regional: O Google não permite acesso deste servidor."
    except Exception as e:
        return None, str(e)

# Inicializa o motor globalmente
motor_ia, modelo_ativo = inicializar_ia_final()

# --- 2. CLASSE DO SISTEMA ---
class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.model = motor_ia

    def get_ai_answer(self, user_text: str):
        if self.model is None:
            return f"IA Indisponível: {modelo_ativo}"
        try:
            contexto = "Você é o Assistente LabSmart, especialista em Química e Física. Responda em português: "
            response = self.model.generate_content(contexto + user_text)
            return response.text
        except Exception as e:
            return f"Erro na consulta: {e}"

    def run_object_detection(self):
        """Detector YOLO"""
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

# --- 3. FUNÇÃO PRINCIPAL (CHAMADA PELO APP.PY) ---
def show_chatbot():
    st.header("🤖 Assistente Científico LabSmart")

    # Garante a instância na sessão
    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # Status da IA
    if bot.model:
        st.success(f"✅ Conectado ao modelo: **{modelo_ativo}**")
    else:
        st.error(f"❌ Falha: {modelo_ativo}")

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

    if prompt := st.chat_input("Pergunte algo..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            resposta = bot.get_ai_answer(prompt)
            st.markdown(resposta)
            st.session_state.chat_history.append({"role": "assistant", "content": resposta})
