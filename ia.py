import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io

# --- CONFIGURAÇÕES DE MOTOR E AGENTES ---
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Chave Groq ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return self.model(img)[0].plot()

# --- FUNÇÕES DE APOIO ---
def extrair_texto(arquivo):
    if not arquivo: return None
    if arquivo.name.endswith('.pdf'):
        leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
        return "".join([p.extract_text() for p in leitor.pages])
    return arquivo.read().decode("utf-8")

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    msgs = [{"role": "system", "content": f"Você é o LabSmart AI ({esp}). Mantenha o contexto do histórico."}]
    msgs.extend(historico[-10:])
    contexto = f"DADOS: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.4)
    return res.choices[0].message.content

# --- INTERFACE PRINCIPAL ---
def show_chatbot():
    # Inicialização de Memória Separada
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "yolo_model" not in st.session_state: st.session_state.yolo_model = YOLO("yolov8n.pt")

    st.subheader("🔬 LabSmart AI - Sistema Integrado")

    # Criamos as abas e usamos uma variável para saber qual está ativa
    aba_geral, aba_agente = st.tabs(["💬 Chat Científico", "👥 Squad de Agentes"])

    # --- RENDERIZAÇÃO DA ABA GERAL ---
    with aba_geral:
        col_c1, col_t1 = st.columns([3, 1])
        with col_t1:
            st.caption("⚙️ Ferramentas")
            if st.toggle("Ativar YOLO", key="t1"):
                webrtc_streamer(key="v1", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
            up_geral = st.file_uploader("Subir base", type=["pdf", "csv", "txt"], key="up1")
        with col_c1:
            for m in st.session_state.messages_geral:
                with st.chat_message(m["role"]): st.markdown(m["content"])

    # --- RENDERIZAÇÃO DA ABA AGENTE ---
    with aba_agente:
        col_c2, col_t2 = st.columns([3, 1])
        with col_t2:
            st.caption("👥 Configuração")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])
            up_agente = st.file_uploader("Dados específicos", type=["pdf", "csv", "txt"], key="up2")
        with col_c2:
            for m in st.session_state.messages_agente:
                with st.chat_message(m["role"]): st.markdown(m["content"])

    # --- INPUT ÚNICO E FIXO NO RODAPÉ ---
    # O segredo: o input fica fora das abas para "travar" no fundo
    if prompt := st.chat_input("Como posso ajudar no laboratório agora?"):
        
        # Lógica de Roteamento: Se o upload da aba agente tiver algo ou se estivermos na aba agente
        # O Streamlit não detecta a aba ativa diretamente, então usamos os widgets de cada aba como sinal
        if up_agente or "up2" in st.session_state:
            h_key = "messages_agente"
            dados = extrair_texto(up_agente)
            persona = esp_nome
        else:
            h_key = "messages_geral"
            dados = extrair_texto(up_geral)
            persona = "Geral"

        # 1. Adiciona pergunta do usuário ao histórico correto
        st.session_state[h_key].append({"role": "user", "content": prompt})
        
        # 2. Gera resposta
        resposta = responder_ia(prompt, st.session_state[h_key], dados, persona)
        
        # 3. Adiciona resposta da IA ao histórico correto
        st.session_state[h_key].append({"role": "assistant", "content": resposta})
        
        # 4. Recarrega para exibir as bolhas de chat atualizadas
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
