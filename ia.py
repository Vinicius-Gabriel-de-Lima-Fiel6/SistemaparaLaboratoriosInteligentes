import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io

def inicializar_motor():
    # Verifica se a chave existe nos secrets do Streamlit
    if "GROQ_API_KEY" not in st.secrets or not st.secrets["GROQ_API_KEY"]:
        return None, "Erro: Chave API ausente nos Secrets."
    
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        # Testamos o modelo padrão; você pode ajustar para o que preferir
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, f"Erro na inicialização: {str(e)}"

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
            texto = "".join([p.extract_text() for p in leitor.pages])
            return texto
        return arquivo.read().decode("utf-8")
    except: return None

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    # Bloqueio de segurança: se o cliente não iniciou, não tenta a chamada
    if client_groq is None:
        return "⚠️ ERRO DE SISTEMA: Chave de API Groq não configurada. Verifique os Secrets do Streamlit."

    instrucoes = (
        f"VOCÊ É O NÚCLEO LABSMART AI PhD EM {esp}. STATUS: ERRO ZERO.\n"
        "DIRETRIZES DE ALTA PRECISÃO (OBRIGATÓRIO):\n"
        "1. PENSAMENTO PROCEDIMENTAL: Decompunha o problema em: [Dados] -> [Teoria Aplicada] -> [Cálculo] -> [Validação].\n"
        "2. RIGOR MATEMÁTICO: Proibido arredondar. Use 8 casas decimais. Realize prova real em Python para toda conta.\n"
        "3. SEGURANÇA CLÍNICA/ESTRUTURAL: Analise interações CYP450, SLCO/UGT, ClCr e Fração Livre. Se houver risco >= 0.01%, aplique VETO TERMINAL.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: É proibido inferir. Se o dado não existir, responda: 'ESTADO DE INCERTEZA SISTÊMICA'.\n"
        "5. REFERENCIAL 2026: Baseie-se apenas em evidências científicas Grau A (Metanálises) e Normas Técnicas (ISO/ABNT/FDA)."
    )
    
    msgs = [{"role": "system", "content": instrucoes}]
    # Mantém apenas as últimas 10 mensagens para economizar tokens
    msgs.extend(historico[-10:]) 
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(
            model=modelo_ativo, 
            messages=msgs, 
            temperature=0.0
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Erro de Autenticação/Conexão com Groq: {str(e)}"

def show_chatbot():
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    
    # Cache do modelo YOLO para não recarregar toda hora
    if "yolo_model" not in st.session_state: 
        st.session_state.yolo_model = YOLO("yolov8n.pt")

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    # Alerta se a API não estiver configurada
    if client_groq is None:
        st.error("Chave 'GROQ_API_KEY' não encontrada nos segredos do Streamlit.")

    escolha_aba = st.radio("Selecione o ambiente de trabalho:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = escolha_aba

    st.divider()

    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "Inteligência Artificial para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Structure Database": {"desc": "Acesso a mais de 200 milhões de estruturas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server (Previsão)": {"desc": "Ferramenta para prever novas estruturas.", "url": "https://alphafoldserver.com/"},
                "AlphaFold no Google Colab": {"desc": "Execução via código.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    if st.session_state.aba_atual == "💬 Chat Científico":
        col_c1, col_t1 = st.columns([3, 1])
        with col_t1:
            st.write("### ⚙️ Ferramentas")
            if st.toggle("🎥 Visão YOLO", key="tgl_v1"):
                webrtc_streamer(key="stream_v1", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages_geral = []
                st.rerun()
            
            st.write("---")
            ft_sel = st.selectbox("Auxiliares:", list(dict_ferramentas.keys()), key="ft_geral")
            
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_geral")
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
            else:
                info = dict_ferramentas[ft_sel]
                sub_sel = ft_sel

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info["desc"])
                st.link_button(f"Abrir {sub_sel}", info["url"], use_container_width=True)

        with col_c1:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_geral:
                chat_container.chat_message(m["role"]).write(m["content"])
            
    else:
        col_c2, col_t2 = st.columns([3, 1])
        with col_t2:
            st.write("### 👥 Squad")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            up_agente = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            if st.button("🗑️ Limpar Squad"):
                st.session_state.messages_agente = []
                st.rerun()

            st.write("---")
            ft_sel_ag = st.selectbox("Auxiliares:", list(dict_ferramentas.keys()), key="ft_agente")
            
            if ft_sel_ag == "AlphaFold":
                sub_sel_ag = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_agente")
                info_ag = dict_ferramentas["AlphaFold"]["sub"][sub_sel_ag]
            else:
                info_ag = dict_ferramentas[ft_sel_ag]
                sub_sel_ag = ft_sel_ag

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info_ag["desc"])
                st.link_button(f"Abrir {sub_sel_ag}", info_ag["url"], use_container_width=True)

        with col_c2:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_agente:
                chat_container.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input("Digite sua mensagem..."):
        if st.session_state.aba_atual == "💬 Chat Científico":
            h_key = "messages_geral"
            dados = extrair_texto(up_geral) if up_geral else None
            persona = "Consultor Sênior em Engenharia, Medicina de Precisão e Auditoria Científica"
        else:
            h_key = "messages_agente"
            dados = extrair_texto(up_agente) if up_agente else None
            persona = esp_nome

        st.session_state[h_key].append({"role": "user", "content": prompt})
        with st.spinner(f"O {persona} está processando..."):
            resposta = responder_ia(prompt, st.session_state[h_key], dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
