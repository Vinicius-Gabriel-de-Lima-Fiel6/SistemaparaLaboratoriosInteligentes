import streamlit as st
import pandas as pd
import google.generativeai as genai
import cv2
import numpy as np
from ultralytics import YOLO

# --- 1. MOTOR DE FORÇA BRUTA (CONEXÃO) ---
def inicializar_ia_forca_bruta():
    """Tenta conectar em todos os modelos possíveis para encontrar um funcional."""
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "Chave de API não configurada nos Secrets"
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Lista exaustiva do mais novo ao mais estável
        modelos_disponiveis = [
            'gemini-1.5-flash', 
            'gemini-1.5-pro', 
            'gemini-pro', 
            'gemini-1.0-pro',
            'gemini-1.5-flash-8b'
        ]
        
        for nome in modelos_disponiveis:
            try:
                model = genai.GenerativeModel(nome)
                # Teste rápido de 1 token para validar a conexão
                model.generate_content("oi", generation_config={"max_output_tokens": 1})
                return model, nome  # Se funcionar, para aqui e entrega o modelo
            except Exception:
                continue # Se der 404 ou 403, tenta o próximo
                
        return None, "Nenhum modelo Gemini respondeu (verifique sua chave)"
    except Exception as e:
        return None, str(e)

# Inicializa o motor uma vez ao carregar o arquivo
motor_ia, modelo_vencedor = inicializar_ia_forca_bruta()

# --- 2. CLASSE DO SISTEMA LABSMART ---
class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.model = motor_ia
        self.nome_modelo = modelo_vencedor

    def get_ai_answer(self, user_text: str):
        """Usa o modelo que passou no teste de força bruta"""
        if self.model is None:
            return f"Erro de Conexão: {self.nome_modelo}"
            
        try:
            # Mantendo sua instrução científica original
            contexto = "Você é um Assistente de Laboratório Inteligente especializado em Química e Física. Responda em português: "
            response = self.model.generate_content(contexto + user_text)
            return response.text
        except Exception as e:
            return f"Erro ao processar com {self.nome_modelo}: {e}"

    def run_object_detection(self):
        """Seu sistema YOLO original"""
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        
        cap = cv2.VideoCapture(0)
        st.toast("Câmera ativada! Pressione 'Q' na janela local para fechar.")
        
        while True:
            success, img = cap.read()
            if not success: break
            results = self.yolo_model.track(img, persist=True)
            for result in results:
                img = result.plot()
            
            cv2.imshow("LabSmartAI - Detector de Objetos", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

# --- 3. INTERFACE (CHAMADA PELO APP.PY) ---
def show_chatbot():
    st.header("🤖 Assistente Científico com IA")

    # Inicializa a classe na sessão
    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # Mostra qual modelo o sistema escolheu
    if bot.model:
        st.success(f"✅ Conectado ao modelo: **{bot.nome_modelo}**")
    else:
        st.error(f"❌ {bot.nome_modelo}")

    # --- BOTÕES DE PESQUISA (Seu sistema original) ---
    st.subheader("📚 Bases de Pesquisa & IA Especializada")
    col_links = st.columns(4)
    with col_links[0]:
        st.link_button("🧪 PubMed", "https://pubmed.ncbi.nlm.nih.gov/", use_container_width=True)
    with col_links[1]:
        st.link_button("🔬 Scielo", "https://scielo.org/", use_container_width=True)
    with col_links[2]:
        st.link_button("🎓 Scholar", "https://scholar.google.com/", use_container_width=True)
    with col_links[3]:
        st.link_button("🧠 Perplexity", "https://www.perplexity.ai/", use_container_width=True)

    st.divider()

    # --- SIDEBAR E VISÃO ---
    with st.sidebar:
        st.subheader("Ferramentas de Visão")
        if st.button("🚀 Ativar Detector YOLO", use_container_width=True):
            bot.run_object_detection()

    # --- INTERFACE DE CHAT ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte qualquer coisa ao LabSmart..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"Consultando {bot.nome_modelo}..."):
                resposta = bot.get_ai_answer(prompt)
                st.markdown(resposta)
                st.session_state.chat_history.append({"role": "assistant", "content": resposta})
