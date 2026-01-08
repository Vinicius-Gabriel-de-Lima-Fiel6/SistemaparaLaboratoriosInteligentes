import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
import base64
from datetime import datetime
import io

# --- CONFIGURAÇÃO DE ELITE (VERSÃO 2026) ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Configure a GROQ_API_KEY nos Secrets do Streamlit."
    
    # O modelo 11b-vision-preview é o padrão atual para visão no Groq
    # Se o erro 400 persistir, o Groq pode ter mudado para 'llama-3.2-90b-vision-preview'
    modelo = "llama-3.2-11b-vision-preview" 
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, modelo

client_groq, modelo_ativo = inicializar_motor()

class LabSmartInfinite:
    def __init__(self):
        self.yolo_model = None

    def executar_fluxo_agente(self, objetivo, imagem=None, dados=None):
        """Sistema de Raciocínio Multi-Agente com Visão"""
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        prompt_master = f"""
        DATA ATUAL: {data_hoje}
        OBJETIVO: {objetivo}
        
        Aja como uma equipe de 3 Agentes de IA:
        1. [ANALISTA]: Pesquise tendências atuais na web e analise arquivos subidos.
        2. [ENGENHEIRO]: Desenvolva a parte técnica, cálculos e segurança (EPI/EPC).
        3. [ESCRITOR]: Formate um relatório científico final em Markdown.
        
        CONTEXTO DE DADOS: {dados if dados else "Sem arquivos de texto fornecidos."}
        """

        messages = [
            {"role": "system", "content": "Você é o LabSmart Infinite v3.0, um sistema multi-agente de alta precisão científica."},
        ]

        # Lógica Multimodal (Texto + Imagem)
        if imagem:
            img_bytes = imagem.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
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
            res = client_groq.chat.completions.create(
                model=modelo_ativo,
                messages=messages,
                temperature=0.1,
                max_tokens=8192
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro Crítico na IA: {str(e)}"

    def run_yolo_vision(self):
        """Detecção de Objetos em Tempo Real (YOLOv8)"""
        if self.yolo_model is None:
            with st.spinner("Carregando Rede Neural YOLOv8..."):
                self.yolo_model = YOLO("yolov8n.pt")
        
        cap = cv2.VideoCapture(0)
        st.toast("Visão Computacional Ativada! Pressione 'Q' na janela da câmera para sair.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            results = self.yolo_model(frame)
            annotated_frame = results[0].plot()
            
            cv2.imshow("LabSmart Vision - YOLOv8", annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

# --- INTERFACE STREAMLIT ---
def show_chatbot():
    st.set_page_config(page_title="LabSmart Infinite", layout="wide")
    
    if "engine" not in st.session_state:
        st.session_state.engine = LabSmartInfinite()
    
    st.title("🧪 LabSmart Infinite - IA & Computer Vision")

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Painel de Controle")
        if st.button("🚀 Ativar YOLO (Câmera Local)"):
            st.session_state.engine.run_yolo_vision()
        
        st.divider()
        st.header("📂 Importação")
        up_file = st.file_uploader("Suba fotos ou arquivos (CSV/TXT)", type=["png", "jpg", "jpeg", "csv", "txt"])
        
        if st.button("🗑️ Limpar Chat"):
            st.session_state.messages = []
            st.rerun()

    # --- CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Como posso ajudar no seu projeto científico hoje?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Orquestrando agentes e analisando dados..."):
                # Captura de contexto
                dados_contexto = None
                if up_file and up_file.name.endswith(('.csv', '.txt')):
                    dados_contexto = up_file.getvalue().decode("utf-8", errors="ignore")
                
                imagem_input = up_file if up_file and up_file.name.endswith(('jpg', 'png', 'jpeg')) else None
                
                # Resposta Final
                resposta = st.session_state.engine.executar_fluxo_agente(prompt, imagem_input, dados_contexto)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

        # Exportação
        st.download_button("📥 Baixar Relatório do Projeto", resposta, file_name="projeto_labsmart.md")
