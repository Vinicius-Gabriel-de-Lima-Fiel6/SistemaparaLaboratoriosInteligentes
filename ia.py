import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io

# --- 1. CONFIGURAÇÕES E MOTORES ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return self.model(img)[0].plot()

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except: return None

# --- 2. LÓGICA DE IA COM SEPARAÇÃO DE MEMÓRIA ---
def responder_ia(prompt, historico, dados=None, esp="Geral"):
    msgs = [{"role": "system", "content": f"Você é o LabSmart AI ({esp}). Não misture informações de outros chats."}]
    msgs.extend(historico[-10:]) # Puxa apenas o histórico da aba atual
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.4)
    return res.choices[0].message.content

# --- 3. INTERFACE PRINCIPAL ---
def show_chatbot():
    # Inicialização de Memórias Distintas
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "yolo_model" not in st.session_state: st.session_state.yolo_model = YOLO("yolov8n.pt")

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    # Criamos as abas e usamos o parâmetro 'key' para rastrear qual está aberta
    tab_id = st.tabs(["💬 Chat Científico", "👥 Squad de Agentes"])

    # --- ABA 1: CHAT CIENTÍFICO ---
    with tab_id[0]:
        col_c1, col_t1 = st.columns([3, 1])
        with col_t1:
            st.write("### ⚙️ Ferramentas")
            if st.toggle("🎥 Visão YOLO", key="tgl_v1"):
                webrtc_streamer(key="stream_v1", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            if st.button("🗑️ Limpar Chat Científico"):
                st.session_state.messages_geral = []
                st.rerun()
        with col_c1:
            # Container com scroll para as mensagens não empurrarem o input
            chat_container1 = st.container(height=500, border=False)
            for m in st.session_state.messages_geral:
                chat_container1.chat_message(m["role"]).write(m["content"])


    with tab_id[1]:
        col_c2, col_t2 = st.columns([3, 1])
        with col_t2:
            st.write("### 👥 Agentes")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            up_agente = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            if st.button("🗑️ Limpar Squad"):
                st.session_state.messages_agente = []
                st.rerun()
        with col_c2:
            chat_container2 = st.container(height=500, border=False)
            for m in st.session_state.messages_agente:
                chat_container2.chat_message(m["role"]).write(m["content"])


    if prompt := st.chat_input("Digite sua mensagem:"):
        
        if up_agente: # Se o usuário carregou algo na aba de agentes, ele quer falar com o agente
            h_key = "messages_agente"
            dados = extrair_texto(up_agente)
            persona = esp_nome
        else:
            # Caso contrário, assume-se o Chat Científico como padrão
            h_key = "messages_geral"
            dados = extrair_texto(up_geral)
            persona = "Geral"

        # Salva e Processa apenas no histórico escolhido
        st.session_state[h_key].append({"role": "user", "content": prompt})
        
        with st.spinner("IA Respondendo..."):
            resposta = responder_ia(prompt, st.session_state[h_key], dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        
        st.rerun()

if __name__ == "__main__":
    show_chatbot()

