import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
import base64
from datetime import datetime

# --- CONFIGURAÇÃO DO MOTOR (ATUALIZADO JAN/2026) ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Configure a GROQ_API_KEY nos Secrets."
    
    # Modelo estável que substitui as versões antigas (Llama 3.2 Vision)
    modelo = "llama-3.2-11b-vision-preview"
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

# NOME DA CLASSE IGUAL AO QUE O SEU APP.PY PROCURA
class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = client_groq

    def executar_fluxo_agente(self, objetivo, imagem=None, dados=None):
        """Sistema Multi-Agente: Analista, Engenheiro e Escritor"""
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        prompt_master = f"""
        DATA: {data_hoje} | OBJETIVO: {objetivo}
        Aja como uma equipe técnica de elite:
        1. [ANALISTA]: Pesquisa e contexto de dados.
        2. [ENGENHEIRO]: Cálculos, montagem e segurança (EPI/EPC).
        3. [ESCRITOR]: Relatório final em Markdown.
        
        CONTEXTO DE ARQUIVO: {dados if dados else "Nenhum dado fornecido."}
        """

        messages = [{"role": "system", "content": "Você é o LabSmart Ultra, sistema de inteligência laboratorial avançada."}]

        if imagem:
            img_b64 = base64.b64encode(imagem.getvalue()).decode('utf-8')
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_master},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt_master})

        try:
            res = self.client.chat.completions.create(
                model=modelo_ativo,
                messages=messages,
                temperature=0.1,
                max_tokens=8192
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro Crítico na IA: {str(e)}"

    def run_yolo_vision(self):
        """Detecção de Objetos em Tempo Real"""
        if self.yolo_model is None:
            with st.spinner("Carregando IA de Visão YOLOv8..."):
                self.yolo_model = YOLO("yolov8n.pt")
        
        cap = cv2.VideoCapture(0)
        st.toast("Câmera Ativada! Pressione 'Q' na janela para sair.")
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            results = self.yolo_model(frame)
            cv2.imshow("LabSmart Vision - YOLOv8", results[0].plot())
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            
        cap.release()
        cv2.destroyAllWindows()

# --- FUNÇÃO PRINCIPAL DE INTERFACE ---
def show_chatbot():
    st.title("🔬 LabSmart AI - Sistema Científico Ultra")

    if "ia_engine" not in st.session_state:
        st.session_state.ia_engine = LabSmartAI()
    
    bot = st.session_state.ia_engine

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Ferramentas")
        if st.button("🚀 Iniciar YOLO (Câmera Local)"):
            bot.run_yolo_vision()
        
        st.divider()
        st.header("📂 Entrada de Dados")
        up = st.file_uploader("Fotos ou Documentos (CSV/TXT)", type=["png", "jpg", "csv", "txt"])
        
        if st.button("🗑️ Limpar Conversa"):
            st.session_state.messages = []
            st.rerun()

    # --- HISTÓRICO DE CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # --- ENTRADA DO USUÁRIO ---
    if prompt := st.chat_input("Como posso ajudar no seu projeto hoje?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("IA Processando via Groq..."):
                # Extração de contexto
                dados_txt = None
                if up and up.name.endswith(('.csv', '.txt')):
                    dados_txt = up.getvalue().decode("utf-8", errors="ignore")
                
                imagem_up = up if up and up.name.endswith(('jpg', 'png', 'jpeg')) else None
                
                # Resposta
                resposta = bot.executar_fluxo_agente(prompt, imagem_up, dados_txt)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

        st.download_button("📥 Baixar Relatório", resposta, file_name="projeto_labsmart.md")
