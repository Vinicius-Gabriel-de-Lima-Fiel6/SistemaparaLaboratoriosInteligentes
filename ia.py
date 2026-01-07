import streamlit as st
import pandas as pd
import google.generativeai as genai
import cv2
import numpy as np
from ultralytics import YOLO

# --- 1. MOTOR DE CONEXÃO ULTRA-ESTÁVEL ---
def inicializar_ia_definitivo():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "Chave GOOGLE_API_KEY não encontrada nos Secrets."
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        
        # FORÇA A CONFIGURAÇÃO ESTÁVEL
        # O parâmetro transport='rest' evita o erro de versão v1beta das suas fotos
        genai.configure(api_key=api_key, transport='rest')
        
        # Testamos os modelos um por um na versão estável
        modelos = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        for nome in modelos:
            try:
                model = genai.GenerativeModel(model_name=nome)
                # Teste de fogo: se responder 'ok', o 404 foi vencido
                model.generate_content("ok", generation_config={"max_output_tokens": 1})
                return model, nome
            except Exception:
                continue
                
        return None, "O Google recusou todos os modelos. Verifique se sua chave de API no AI Studio está ativa."
    except Exception as e:
        return None, f"Erro de sistema: {str(e)}"

# Inicialização global
motor_ia, modelo_vencedor = inicializar_ia_definitivo()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.model = motor_ia
        self.nome_modelo = modelo_vencedor

    def get_ai_answer(self, user_text: str):
        if self.model is None:
            return f"IA Indisponível: {self.nome_modelo}"
        try:
            # Sua instrução científica original
            contexto = "Você é um Assistente de Laboratório Inteligente especializado em Química e Física. Responda em português: "
            response = self.model.generate_content(contexto + user_text)
            return response.text
        except Exception as e:
            return f"Erro ao processar consulta: {e}"

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

# --- 2. FUNÇÃO QUE O APP.PY CHAMA ---
def show_chatbot():
    st.header("🤖 Assistente Científico com IA")

    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # Diagnóstico para você ver se funcionou
    if bot.model:
        st.success(f"✅ Motor de IA Conectado: **{bot.nome_modelo}**")
    else:
        st.error(f"❌ Falha: {bot.nome_modelo}")
        st.info("Dica: Verifique se sua chave no Google AI Studio não tem restrições de IP.")

    # Links Científicos
    st.subheader("📚 Bases de Pesquisa")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.link_button("🧪 PubMed", "https://pubmed.ncbi.nlm.nih.gov/", use_container_width=True)
    with col2: st.link_button("🔬 Scielo", "https://scielo.org/", use_container_width=True)
    with col3: st.link_button("🎓 Scholar", "https://scholar.google.com/", use_container_width=True)
    with col4: st.link_button("🧠 Perplexity", "https://www.perplexity.ai/", use_container_width=True)

    st.divider()

    # Interface de Chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte ao Gemini..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            resposta = bot.get_ai_answer(prompt)
            st.markdown(resposta)
            st.session_state.chat_history.append({"role": "assistant", "content": resposta})
