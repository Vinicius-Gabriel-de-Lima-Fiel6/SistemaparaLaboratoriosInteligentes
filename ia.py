import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Chave não configurada."
    modelo = "llama-3.3-70b-versatile"
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = client_groq

    def executar_fluxo_agente(self, objetivo, dados=None):
        """Resposta fluida e integrada (Estilo ChatGPT/Gemini)"""
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        # PROMPT DE SÍNTESE UNITÁRIA
        prompt_integrado = f"""
        Data: {data_hoje}
        Pergunta/Objetivo: {objetivo}
        
        Aja como um assistente científico de alto nível. Integre conhecimentos de Química, Biologia, Física, Engenharia e Matemática em uma única resposta coesa e direta. 
        
        Regras de Estilo:
        - Não se identifique como múltiplos agentes.
        - Não use divisões como '[MODO QUÍMICA]' ou '[MODO FÍSICA]'.
        - Forneça uma resposta fluida, técnica e detalhada.
        - Use tabelas ou listas apenas se ajudar na clareza.
        - Se houver dados fornecidos ({dados if dados else "Nenhum"}), incorpore a análise naturalmente no texto.
        """

        messages = [
            {"role": "system", "content": "Você é o LabSmart AI, um assistente especializado em ciência e tecnologia. Responda de forma integrada, clara e profissional."},
            {"role": "user", "content": prompt_integrado}
        ]

        try:
            res = self.client.chat.completions.create(
                model=modelo_ativo,
                messages=messages,
                temperature=0.3,
                max_tokens=6000
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro: {str(e)}"

    def run_yolo_vision(self):
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret: break
            results = self.yolo_model(frame)
            cv2.imshow("LabSmart Vision", results[0].plot())
            if cv2.waitKey(1) & 0xFF == ord('q'): break
        cap.release()
        cv2.destroyAllWindows()

def show_chatbot():
    st.title("🔬 LabSmart AI")

    if "ia_engine" not in st.session_state:
        st.session_state.ia_engine = LabSmartAI()
    
    bot = st.session_state.ia_engine

    with st.sidebar:
        st.header("Opções")
        if st.button("🚀 Ativar Câmera (YOLO)"):
            bot.run_yolo_vision()
        st.divider()
        up = st.file_uploader("Arquivos de Dados", type=["csv", "txt"])
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Como posso ajudar?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                dados_txt = up.getvalue().decode("utf-8", errors="ignore") if up else None
                resposta = bot.executar_fluxo_agente(prompt, dados_txt)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})
