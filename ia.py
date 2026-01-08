import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime

# --- CONFIGURAÇÃO DO MOTOR ESTÁVEL ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Configure a GROQ_API_KEY nos Secrets."
    
    # Modelo Llama 3.3 70B: O mais estável e potente para texto e lógica
    modelo = "llama-3.3-70b-versatile"
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = client_groq

    def executar_fluxo_agente(self, objetivo, dados=None):
        """Sistema de Agentes focado em Lógica e Texto"""
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        prompt_master = f"""
        DATA: {data_hoje} | OBJETIVO: {objetivo}
        Aja como uma equipe de 3 especialistas:
        1. [ANALISTA]: Interpreta dados e contexto científico.
        2. [ENGENHEIRO]: Cálculos, normas técnicas e segurança.
        3. [ESCRITOR]: Relatório final estruturado em Markdown.
        
        CONTEXTO DE DADOS: {dados if dados else "Nenhum arquivo fornecido."}
        """

        messages = [
            {"role": "system", "content": "Você é o LabSmart AI, assistente técnico de laboratório."},
            {"role": "user", "content": prompt_master}
        ]

        try:
            res = self.client.chat.completions.create(
                model=modelo_ativo,
                messages=messages,
                temperature=0.3,
                max_tokens=4096
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro na IA: {str(e)}"

    def run_yolo_vision(self):
        """Visão Computacional Local"""
        if self.yolo_model is None:
            with st.spinner("Carregando YOLOv8..."):
                self.yolo_model = YOLO("yolov8n.pt")
        
        cap = cv2.VideoCapture(0)
        st.toast("Câmera aberta no servidor local. 'Q' para sair.")
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            results = self.yolo_model(frame)
            cv2.imshow("LabSmart Vision", results[0].plot())
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            
        cap.release()
        cv2.destroyAllWindows()

# --- INTERFACE ---
def show_chatbot():
    st.title("🔬 LabSmart AI PRO")

    # Inicializa a classe se não existir
    if "ia_engine" not in st.session_state:
        st.session_state.ia_engine = LabSmartAI()
    
    bot = st.session_state.ia_engine

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Opções")
        if st.button("🚀 Abrir Câmera (YOLO)"):
            bot.run_yolo_vision()
        
        st.divider()
        up = st.file_uploader("Suba arquivos de dados (CSV/TXT)", type=["csv", "txt"])
        
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.messages = []
            st.rerun()

    # Histórico
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Input
    if prompt := st.chat_input("Diga o que precisa fazer no lab..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                dados_txt = None
                if up:
                    dados_txt = up.getvalue().decode("utf-8", errors="ignore")
                
                resposta = bot.executar_fluxo_agente(prompt, dados_txt)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

        st.download_button("📥 Baixar Relatório", resposta, file_name="labsmart_relatorio.md")
