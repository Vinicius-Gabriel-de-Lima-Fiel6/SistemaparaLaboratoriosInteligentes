import streamlit as st
import pandas as pd
import google.generativeai as genai
import cv2
import numpy as np
from ultralytics import YOLO

# --- 1. MOTOR DE CONEXÃO ESTÁVEL (CORREÇÃO DO ERRO 404) ---
def inicializar_ia_estavel():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "ERRO: Chave ausente nos Secrets."
            
        # Configuração forçando o protocolo estável para evitar o erro v1beta
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"], transport='rest')
        
        # Lista de modelos para força bruta
        # Usamos nomes diretos para garantir compatibilidade
        for nome in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
            try:
                model = genai.GenerativeModel(nome)
                # Teste de conexão
                model.generate_content("oi", generation_config={"max_output_tokens": 1})
                return model, nome
            except Exception:
                continue
                
        return None, "O Google ainda não reconheceu os modelos. Verifique se sua chave de API é do tipo 'Pay-as-you-go' ou 'Free tier' no AI Studio."
    except Exception as e:
        return None, f"Erro de sistema: {str(e)}"

# Inicialização global
motor_ia, modelo_vencedor = inicializar_ia_estavel()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.model = motor_ia
        self.nome_modelo = modelo_vencedor

    def get_ai_answer(self, user_text: str):
        if self.model is None:
            return f"IA fora de linha: {self.nome_modelo}"
        try:
            contexto = "Você é um Assistente de Laboratório Inteligente especializado em Química e Física. Responda em português: "
            response = self.model.generate_content(contexto + user_text)
            return response.text
        except Exception as e:
            return f"Erro ao processar: {e}"

    def run_object_detection(self):
        """Seu sistema YOLO original"""
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        cap = cv2.VideoCapture(0)
        st.toast("Câmera ativada!")
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

# --- 2. FUNÇÃO QUE CONECTA AO SEU APP.PY ---
def show_chatbot():
    st.header("🤖 Assistente Científico com IA")

    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # Banner de status
    if bot.model:
        st.success(f"✅ Conectado com Sucesso! Motor: **{bot.nome_modelo}**")
    else:
        st.error(f"❌ {bot.nome_modelo}")
        st.info("Dica: Se você criou a chave hoje, o Google pode levar alguns minutos para ativá-la nos modelos 1.5.")

    # Links Científicos
    st.subheader("📚 Bases de Pesquisa")
    cols = st.columns(4)
    with cols[0]: st.link_button("🧪 PubMed", "https://pubmed.ncbi.nlm.nih.gov/", use_container_width=True)
    with cols[1]: st.link_button("🔬 Scielo", "https://scielo.org/", use_container_width=True)
    with cols[2]: st.link_button("🎓 Scholar", "https://scholar.google.com/", use_container_width=True)
    with cols[3]: st.link_button("🧠 Perplexity", "https://www.perplexity.ai/", use_container_width=True)

    st.divider()

    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte ao LabSmart..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analisando dados científicos..."):
                resposta = bot.get_ai_answer(prompt)
                st.markdown(resposta)
                st.session_state.chat_history.append({"role": "assistant", "content": resposta})
