import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Configure a GROQ_API_KEY nos Secrets."
    modelo = "llama-3.3-70b-versatile"
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = client_groq

    def executar_fluxo_agente(self, objetivo, dados=None):
        """Hub de IAs Especializadas em Ciências Naturais"""
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        # PROMPT DE ORQUESTRAÇÃO CIENTÍFICA
        prompt_master = f"""
        DATA: {data_hoje} | OBJETIVO: {objetivo}
        
        Você deve orquestrar a resposta utilizando os seguintes especialistas virtuais:
        
        1. 🧪 [MODO CHEM-IA]: Especialista em Estequiometria, Reações Orgânicas e Segurança Química (MSDS).
        2. 🧬 [MODO BIO-GEN]: Especialista em Biologia Molecular, Genética e Botânica.
        3. ⚛️ [MODO PHYS-TECH]: Especialista em Física Experimental, Termodinâmica e Arduino.
        4. 📊 [MODO MATH-STAT]: Executa cálculos precisos e análise de dados CSV.

        Se o usuário fornecer dados ({dados if dados else "Nenhum"}), use o MODO MATH-STAT para analisá-los prioritariamente.
        Responda com rigor acadêmico, tabelas e fórmulas em LaTeX.
        """

        messages = [
            {"role": "system", "content": "Você é o LabSmart Hub, uma rede de agentes especializados em ciências naturais e exatas."},
            {"role": "user", "content": prompt_master}
        ]

        try:
            res = self.client.chat.completions.create(
                model=modelo_ativo,
                messages=messages,
                temperature=0.2, # Baixa temperatura para evitar erros em fórmulas
                max_tokens=6000 # Aumentado para suportar projetos longos
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro na conexão com o Hub: {str(e)}"

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

# --- INTERFACE APRIMORADA ---
def show_chatbot():
    st.title("🧪 LabSmart AI - Hub de Especialistas")

    if "ia_engine" not in st.session_state:
        st.session_state.ia_engine = LabSmartAI()
    
    bot = st.session_state.ia_engine

    with st.sidebar:
        st.header("🔬 Ferramentas Ativas")
        st.info("Agentes: Chem-IA, Bio-Gen, Phys-Tech")
        if st.button("🚀 Iniciar Visão YOLO"):
            bot.run_yolo_vision()
        
        st.divider()
        up = st.file_uploader("Suba seus dados científicos", type=["csv", "txt"])
        
        if st.button("🗑️ Resetar Sessão"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Diga: 'Calcule a molaridade...' ou 'Crie um projeto de genética...'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando Especialistas..."):
                dados_txt = up.getvalue().decode("utf-8", errors="ignore") if up else None
                resposta = bot.executar_fluxo_agente(prompt, dados_txt)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

        st.download_button("📥 Exportar Relatório Científico", resposta, file_name="relatorio_especialista.md")
