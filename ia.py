import streamlit as st
import pandas as pd
import google.generativeai as genai
import cv2
import numpy as np
from ultralytics import YOLO

# --- MOTOR DE DIAGNÓSTICO ---
def inicializar_ia_diagnostico():
    erros_acumulados = []
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "Chave GOOGLE_API_KEY ausente nos Secrets do Streamlit."
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Testando os principais modelos
        for nome in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
            try:
                model = genai.GenerativeModel(nome)
                # Teste real
                model.generate_content("oi", generation_config={"max_output_tokens": 1})
                return model, nome
            except Exception as e:
                erros_acumulados.append(f"{nome}: {str(e)}")
                continue
        
        # Se chegou aqui, todos falharam. Vamos mostrar o porquê:
        return None, " | ".join(erros_acumulados)
    except Exception as e:
        return None, f"Erro de configuração: {str(e)}"

# Inicialização
motor_ia, mensagem_status = inicializar_ia_diagnostico()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.model = motor_ia

    def get_ai_answer(self, user_text: str):
        if self.model is None:
            return f"IA Desconectada. Motivo: {mensagem_status}"
        try:
            contexto = "Você é um Assistente de Laboratório. Responda em português: "
            response = self.model.generate_content(contexto + user_text)
            return response.text
        except Exception as e:
            return f"Erro na consulta: {e}"

    def run_object_detection(self):
        """Detector YOLO"""
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

# --- FUNÇÃO CHAMADA PELO APP.PY ---
def show_chatbot():
    st.header("🤖 Assistente Científico com IA")

    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    if bot.model:
        st.success(f"✅ IA Pronta! Modelo: {mensagem_status}")
    else:
        st.error("❌ Falha na Conexão com o Google")
        with st.expander("Clique para ver o erro técnico detalhado"):
            st.write(mensagem_status)
        st.info("Dica: Tente gerar uma NOVA chave de API no Google AI Studio.")

    # Links e Chat (Mantenha o resto do seu show_chatbot original aqui abaixo)
    st.divider()
    if prompt := st.chat_input("Pergunte algo..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            resposta = bot.get_ai_answer(prompt)
            st.markdown(resposta)
