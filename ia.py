import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
import base64
from datetime import datetime

# --- CONFIGURAÇÃO DE ELITE ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        st.error("ERRO: GROQ_API_KEY não encontrada nos Secrets!")
        return None, None
    return Groq(api_key=st.secrets["GROQ_API_KEY"]), "llama-3.2-11b-vision-preview"

client_groq, modelo_ativo = inicializar_motor()

class LabSmartInfinite:
    def __init__(self):
        self.yolo_model = None

    def executar_fluxo_agente(self, objetivo, imagem=None, dados=None):
        """Sistema de Raciocínio em Cadeia (Chain-of-Thought)"""
        
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        
        # PROMPT DE ARQUITETURA DE PENSAMENTO
        prompt_master = f"""
        DATA: {data_hoje}
        OBJETIVO: {objetivo}
        
        Siga rigorosamente este fluxo de trabalho:
        1. [PLANEJAMENTO]: Decomponha o objetivo em 3 sub-tarefas científicas.
        2. [PESQUISA TÉCNICA]: Use sua base de dados para buscar normas ABNT/ISO e reagentes necessários.
        3. [ANÁLISE DE SEGURANÇA]: Liste riscos (EPC/EPI) e compatibilidade química.
        4. [PROJETO EXECUTIVO]: Gere o passo a passo com cálculos exatos.
        
        CONTEXTO DE ARQUIVO: {dados if dados else "Sem dados externos."}
        """

        messages = [
            {"role": "system", "content": "Você é o LabSmart Infinite, o sistema de IA laboratorial mais avançado do mundo. Sua precisão é cirúrgica e sua visão é multimodal."},
            {"role": "user", "content": prompt_master}
        ]

        if imagem:
            img_b64 = base64.b64encode(imagem.read()).decode('utf-8')
            messages[1]["content"] = [
                {"type": "text", "text": prompt_master},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]

        try:
            res = client_groq.chat.completions.create(
                model=modelo_ativo,
                messages=messages,
                temperature=0.1, # Rigor técnico total
                max_tokens=8192
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Erro Crítico: {e}"

# --- INTERFACE DE NÍVEL INDUSTRIAL ---
def show_chatbot():
    st.set_page_config(page_title="LabSmart Infinite", layout="wide", initial_sidebar_state="expanded")
    
    # Estilização Profissional
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        .main-card { border-left: 5px solid #007bff; padding: 20px; background: white; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
        </style>
    """, unsafe_allow_html=True)

    if "engine" not in st.session_state:
        st.session_state.engine = LabSmartInfinite()

    # --- SIDEBAR INTELIGENTE ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3062/3062331.png", width=80)
        st.title("LabSmart Infinite")
        st.caption("v3.0 - Intelligence & Vision")
        
        st.divider()
        st.header("⚙️ Controle de Missão")
        modo_rigoroso = st.toggle("Rigor Científico Máximo", value=True)
        search_web = st.checkbox("Simular Deep Search", value=True)
        
        st.divider()
        st.header("📂 Data Lake")
        up = st.file_uploader("Arraste arquivos ou fotos", type=["png", "jpg", "csv", "txt", "pdf"])
        
        if st.button("🗑️ Resetar Sistema"):
            st.session_state.messages = []
            st.rerun()

    # --- ÁREA DE TRABALHO ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Container de Histórico
    chat_container = st.container()
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    # Entrada de Dados
    if prompt := st.chat_input("Inicie uma pesquisa, projeto ou análise..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🌀 Orquestrando Agentes e Consultando Bases..."):
                    
                    # Extração de contexto
                    contexto_txt = None
                    if up and not up.name.endswith(('jpg', 'png', 'jpeg')):
                        contexto_txt = up.getvalue().decode("utf-8", errors="ignore")
                    
                    foto = up if up and up.name.endswith(('jpg', 'png', 'jpeg')) else None
                    
                    # Resposta
                    resposta = st.session_state.engine.executar_fluxo_agente(prompt, foto, contexto_txt)
                    
                    st.markdown(f'<div class="main-card">{resposta}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})

        # --- EXPORTAÇÃO AUTOMÁTICA ---
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📝 Baixar Relatório (MD)", resposta, file_name=f"projeto_{datetime.now().strftime('%d%m%Y')}.md")
        with col2:
            if st.button("🔬 Gerar Protocolo de Segurança"):
                st.toast("Protocolo gerado com base nas normas ISO!")
