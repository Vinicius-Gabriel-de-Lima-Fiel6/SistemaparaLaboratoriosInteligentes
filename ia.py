import streamlit as st
import pandas as pd
from groq import Groq
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from supabase import create_client
import PyPDF2
import io

# --- 1. CONFIGURAÇÕES E CONEXÕES ---
st.set_page_config(page_title="LabSmart OS", layout="wide", page_icon="🔬")

# Inicialização Supabase
url_sb = st.secrets["SUPABASE_URL"]
key_sb = st.secrets["SUPABASE_KEY"]
supabase = create_client(url_sb, key_sb)

# Inicialização Groq
def inicializar_groq():
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_groq()

# --- 2. AGENTES E VISÃO ---
AGENTES = {
    "Bioquímico Sênior": "Especialista em reações químicas e protocolos.",
    "Escritor Técnico": "Especialista em redação de POPs e relatórios.",
    "Planejador Estratégico": "Gestão de estoque e eficiência.",
    "Auditor de Qualidade": "Normas RDC, ISO e conformidade."
}

class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.model(img)
        return results[0].plot()

# --- 3. CLASSE CORE DA IA (MEMÓRIA + ARQUIVOS) ---
class LabSmartAI:
    def __init__(self):
        self.yolo_model = None
        self.client = client_groq

    def get_yolo_model(self):
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        return self.yolo_model

    def extrair_texto(self, arquivo):
        if arquivo is None: return None
        try:
            if arquivo.name.endswith('.pdf'):
                pdf = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
                return "".join([p.extract_text() for p in pdf.pages])
            elif arquivo.name.endswith('.csv'):
                return pd.read_csv(arquivo).to_string()
            return arquivo.read().decode("utf-8")
        except: return "Erro na leitura."

    def executar_agente(self, prompt, historico, dados=None, nome="Geral", enxame=False):
        contexto = f"Você é {nome} (Especialista)." if not enxame else "Vocês são um enxame de especialistas."
        messages = [{"role": "system", "content": f"{contexto} Lembre-se do histórico. Data: {datetime.now().strftime('%d/%m/%Y')}"}]
        
        # Injeção da Memória (Últimas 10 mensagens)
        for msg in historico[-10:]:
            messages.append(msg)
            
        full_prompt = f"Contexto Dados: {dados}\n\nPergunta: {prompt}" if dados else prompt
        messages.append({"role": "user", "content": full_prompt})

        res = self.client.chat.completions.create(model=modelo_ativo, messages=messages, temperature=0.3)
        return res.choices[0].message.content

# --- 4. FUNÇÕES DE INTERFACE (HOMMEL) ---
def render_hommel(saude, fogo, reat, esp):
    st.markdown(f"""
    <div style="display: flex; justify-content: center; background: #1e1e1e; padding: 10px; border-radius: 10px;">
        <div style="position: relative; width: 60px; height: 60px; transform: rotate(45deg); border: 1px solid #555;">
            <div style="position: absolute; top: 0; left: 0; width: 30px; height: 30px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{fogo}</div>
            <div style="position: absolute; top: 0; left: 30px; width: 30px; height: 30px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">{reat}</div>
            <div style="position: absolute; top: 30px; left: 0; width: 30px; height: 30px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{saude}</div>
            <div style="position: absolute; top: 30px; left: 30px; width: 30px; height: 30px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-size: 0.6em;">{esp}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. EXECUÇÃO DO APP ---
def main():
    if "ia_engine" not in st.session_state: st.session_state.ia_engine = LabSmartAI()
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # Mock de dados de usuário (Substitua pela sua lógica de login)
    user_data = st.session_state.get('user_data', {'org_name': 'Lab Central', 'role': 'ADM', 'username': 'Admin'})

    tab_inv, tab_ia, tab_agentes = st.tabs(["📋 Inventário & Excel", "🤖 Chat & Memória", "👥 Squad de Agentes"])

    # --- ABA 1: INVENTÁRIO (SISTEMA ANTERIOR MANTIDO) ---
    with tab_inv:
        st.subheader("Gerenciamento de Substâncias")
        # Lógica de Cadastro e Tabela (Resumida para o código não ficar infinito, mas mantendo a estrutura)
        res = supabase.table("substancias").select("*").eq("org_name", user_data['org_name']).execute()
        df = pd.DataFrame(res.data)
        
        if not df.empty:
            st.dataframe(df[['nome', 'quantidade', 'estoque_minimo', 'validade']], use_container_width=True)
            
            # Botões Excel (Sua solicitação de exportação facilitada)
            c1, c2, c3 = st.columns(3)
            c1.download_button("📥 Baixar CSV", df.to_csv(index=False).encode('utf-8'), "estoque.csv", "text/csv", use_container_width=True)
            c2.link_button("🌐 Abrir Excel Online", "https://excel.new", use_container_width=True)
            with c3:
                with st.popover("📖 Instruções"):
                    st.write("Baixe o CSV e arraste para o Excel Online.")

    # --- ABA 2: CHAT & MEMÓRIA ---
    with tab_ia:
        col_chat, col_side = st.columns([2, 1])
        with col_side:
            st.markdown("### 📎 Análise de Arquivos")
            file_up = st.file_uploader("Upload PDF/CSV/TXT", type=["pdf", "csv", "txt"])
            st.divider()
            st.markdown("### 👁️ Visão")
            if st.toggle("Ativar Câmera YOLO"):
                webrtc_streamer(key="viz", video_processor_factory=lambda: VideoProcessor(st.session_state.ia_engine.get_yolo_model()))

        with col_chat:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.markdown(m["content"])

            if prompt := st.chat_input("Pergunte algo sobre o estoque ou arquivos..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.chat_message("user").markdown(prompt)
                
                with st.chat_message("assistant"):
                    txt_extraido = st.session_state.ia_engine.extrair_texto(file_up)
                    resposta = st.session_state.ia_engine.executar_agente(prompt, st.session_state.messages, txt_extraido)
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})

    # --- ABA 3: AGENTES ---
    with tab_agentes:
        st.subheader("Central de Agentes Especialistas")
        c_cfg, c_res = st.columns([1, 2])
        with c_cfg:
            modo = st.radio("Operação", ["Individual", "Enxame"])
            ag = st.selectbox("Líder", list(AGENTES.keys()))
            task = st.text_area("Tarefa:")
            if st.button("🚀 Executar"):
                with c_res:
                    with st.spinner("Agentes trabalhando..."):
                        res_ag = st.session_state.ia_engine.executar_agente(task, st.session_state.messages, nome=ag, enxame=(modo=="Enxame"))
                        st.markdown(res_ag)

if __name__ == "__main__":
    main()
