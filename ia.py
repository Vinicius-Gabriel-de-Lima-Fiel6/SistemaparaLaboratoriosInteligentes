import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io

# ==========================================
# 1. CONFIGURAÇÃO DO MOTOR E MODELOS (2026)
# ==========================================
def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # Modelo Principal: Raciocínio PhD | Modelo Backup: Velocidade/Estabilidade
    return client, "deepseek-r1-distill-llama-70b"

client_groq, modelo_ativo = inicializar_motor()

# ==========================================
# 2. CLASSES E FUNÇÕES DE APOIO
# ==========================================
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

# ==========================================
# 3. NÚCLEO DE INTELIGÊNCIA E PRECISÃO
# ==========================================
def responder_ia(prompt, historico, dados=None, esp="Geral"):
    # Prompt de Alta Densidade (Otimizado para evitar BadRequest)
    instrucoes = (
        f"NÚCLEO LABSMART AI PhD {esp}. STATUS: ERRO ZERO.\n"
        "HEPTA-CHECK: 1.Decomp; 2.Dim-Val; 3.Laws; 4.Triple-Calc; 5.Reg-Audit; 6.Adv-Attack; 7.Synthesis.\n"
        "REGRAS: Sem arredondar (8 casas). Use Python para cálculos. Veto se risco >= 0.01%.\n"
        "Analise CYP450, SLCO/UGT, ClCr e Fração Livre. Precisão >99.9%."
    )
    
    # Limpeza de contexto para estabilidade (Mantém apenas 2 turnos + prompt atual)
    msgs = [{"role": "system", "content": instrucoes}]
    msgs.extend(historico[-2:]) 
    
    # Limite de segurança para dados de arquivos (5000 caracteres)
    ctx_doc = f"DADOS DOC: {dados[:5000]}\n" if dados else ""
    msgs.append({"role": "user", "content": f"{ctx_doc}INPUT: {prompt}"})
    
    try:
        # Tentativa com o modelo PhD (DeepSeek-R1)
        res = client_groq.chat.completions.create(
            model=modelo_ativo, 
            messages=msgs, 
            temperature=0.1, # Estabilidade térmica 2026
            max_tokens=4000
        )
        return res.choices[0].message.content
    except Exception as e:
        # Sistema de Fallback Automático para Llama 3.3 em caso de erro da API
        try:
            res_backup = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=msgs,
                temperature=0.0
            )
            return "⚠️ (MODO BACKUP ATIVADO)\n\n" + res_backup.choices[0].message.content
        except:
            return f"🚨 ERRO CRÍTICO: {str(e)}. Use o botão 'Limpar Chat' e tente novamente."

# ==========================================
# 4. INTERFACE DO SISTEMA (STREAMLIT)
# ==========================================
def show_chatbot():
    # Configuração de Página (Deve ser a primeira instrução Streamlit)
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    if "yolo_model" not in st.session_state: 
        try: st.session_state.yolo_model = YOLO("yolov8n.pt")
        except: st.session_state.yolo_model = None

    st.subheader("🔬 LabSmart AI - Hub de Inteligência Multidisciplinar")

    escolha_aba = st.radio("Ambiente de Trabalho:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = escolha_aba

    st.divider()

    dict_ferramentas = {
        "Lovable": {"desc": "Interfaces e protótipos.", "url": "https://lovable.dev"},
        "Gamma": {"desc": "Apresentações profissionais.", "url": "https://gamma.app"},
        "Manus": {"desc": "Agente de execução digital.", "url": "https://manus.im"},
        "Perplexity": {"desc": "Buscador técnico.", "url": "https://www.perplexity.ai"},
        "AlphaFold": {
            "desc": "Predição proteica.",
            "sub": {
                "AlphaFold DB": {"desc": "Estruturas preditas.", "url": "https://alphafold.ebi.ac.uk"},
                "AlphaFold Server": {"desc": "Novas estruturas.", "url": "https://alphafoldserver.com"}
            }
        }
    }

    col_c, col_t = st.columns([3, 1])

    with col_t:
        st.write("### ⚙️ Painel")
        if st.session_state.aba_atual == "💬 Chat Científico":
            up_file = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            h_key = "messages_geral"
            persona = "Especialista Multidisciplinar em Ciências e Engenharia"
        else:
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])
            up_file = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            h_key = "messages_agente"
            persona = esp_nome

        if st.button("🗑️ Limpar Chat/Memória"):
            st.session_state[h_key] = []
            st.rerun()
            
        st.write("---")
        if st.toggle("🎥 Visão YOLO"):
            if st.session_state.yolo_model:
                webrtc_streamer(key="stream", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
            else: st.error("Modelo YOLO não carregado.")

        st.write("🛠️ **Auxiliares**")
        ft_sel = st.selectbox("Selecionar:", list(dict_ferramentas.keys()))
        if ft_sel == "AlphaFold":
            sub = st.selectbox("Versão:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
            info = dict_ferramentas["AlphaFold"]["sub"][sub]
        else: info = dict_ferramentas[ft_sel]

        with st.popover("Ver Detalhes"):
            st.write(info["desc"])
            st.link_button("Abrir Ferramenta", info["url"], use_container_width=True)

    with col_c:
        chat_container = st.container(height=500, border=False)
        for m in st.session_state[h_key]:
            chat_container.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input("Digite sua consulta PhD..."):
        st.session_state[h_key].append({"role": "user", "content": prompt})
        with chat_container: st.chat_message("user").write(prompt)

        with st.spinner(f"O {persona} está analisando..."):
            dados = extrair_texto(up_file) if up_file else None
            resposta = responder_ia(prompt, st.session_state[h_key], dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
            with chat_container: st.chat_message("assistant").write(resposta)
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
