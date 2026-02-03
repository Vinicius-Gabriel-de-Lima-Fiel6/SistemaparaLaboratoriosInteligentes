import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io

# Configuração da Página
st.set_page_config(page_title="LabSmart AI", page_icon="🔬", layout="wide")

def inicializar_motor():
    """Inicializa o cliente Groq e define o modelo de IA."""
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente nos secrets."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # Utilizando o modelo especificado: llama-3.3-70b-versatile
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

class VideoProcessor(VideoTransformerBase):
    """Processador para detecção de objetos em tempo real com YOLO."""
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        # Realiza a detecção e desenha as caixas delimitadoras
        results = self.model(img)
        return results[0].plot()

def extrair_texto(arquivo):
    """Extrai conteúdo de arquivos PDF ou TXT."""
    if not arquivo: 
        return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except Exception as e:
        return f"Erro na extração: {str(e)}"

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    """Gera resposta da IA com rigor científico e matemático."""
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
    # Limita o histórico para manter a janela de contexto eficiente
    msgs.extend(historico[-10:]) 
    
    contexto_final = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto_final})
    
    try:
        res = client_groq.chat.completions.create(
            model=modelo_ativo, 
            messages=msgs, 
            temperature=0.0 # Temperatura zero para máxima consistência
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERRO CRÍTICO DE SISTEMA: {str(e)}"

def show_chatbot():
    # Inicialização do Estado da Sessão
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    if "yolo_model" not in st.session_state: st.session_state.yolo_model = YOLO("yolov8n.pt")

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    escolha_aba = st.radio("Selecione o ambiente de trabalho:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = escolha_aba

    st.divider()

    # Dicionário de Ferramentas Auxiliares
    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "Inteligência Artificial para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Database": {"desc": "Acesso a mais de 200 milhões de estruturas de proteínas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server": {"desc": "Ferramenta para prever novas estruturas e interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold Colab": {"desc": "Execução via código para pesquisas personalizadas.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    # Layout em colunas para os ambientes
    if st.session_state.aba_atual == "💬 Chat Científico":
        col_chat, col_tools = st.columns([3, 1])
        
        with col_tools:
            st.write("### ⚙️ Ferramentas")
            if st.toggle("🎥 Visão YOLO", key="tgl_v1"):
                webrtc_streamer(key="stream_v1", video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model))
            
            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages_geral = []
                st.rerun()
            
            st.divider()
            st.write("🛠️ **Auxiliares**")
            ft_sel = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_geral")
            
            # Lógica para AlphaFold (Submenus)
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Versão AlphaFold:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
                btn_label = f"Abrir {sub_sel}"
            else:
                info = dict_ferramentas[ft_sel]
                btn_label = f"Abrir {ft_sel}"

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info["desc"])
                st.link_button(btn_label, info["url"], use_container_width=True)

        with col_chat:
            container = st.container(height=500)
            for m in st.session_state.messages_geral:
                container.chat_message(m["role"]).write(m["content"])
            
    else: # Aba Squad de Agentes
        col_chat, col_tools = st.columns([3, 1])
        
        with col_tools:
            st.write("### 👥 Squad")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            up_agente = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            
            if st.button("🗑️ Limpar Squad"):
                st.session_state.messages_agente = []
                st.rerun()

            st.divider()
            st.write("🛠️ **Auxiliares**")
            ft_sel_ag = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_agente")
            
            if ft_sel_ag == "AlphaFold":
                sub_sel_ag = st.selectbox("Versão AlphaFold:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_ag_sel")
                info_ag = dict_ferramentas["AlphaFold"]["sub"][sub_sel_ag]
                btn_label_ag = f"Abrir {sub_sel_ag}"
            else:
                info_ag = dict_ferramentas[ft_sel_ag]
                btn_label_ag = f"Abrir {ft_sel_ag}"

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info_ag["desc"])
                st.link_button(btn_label_ag, info_ag["url"], use_container_width=True)

        with col_chat:
            container = st.container(height=500)
            for m in st.session_state.messages_agente:
                container.chat_message(m["role"]).write(m["content"])

    # Input de Chat (Global)
    if prompt := st.chat_input("Digite sua consulta técnica..."):
        if st.session_state.aba_atual == "💬 Chat Científico":
            h_key = "messages_geral"
            dados_extraidos = extrair_texto(up_geral) if up_geral else None
            persona_atual = "Consultor Sênior em Engenharia e Medicina de Precisão"
        else:
            h_key = "messages_agente"
            dados_extraidos = extrair_texto(up_agente) if up_agente else None
            persona_atual = esp_nome

        # Adiciona pergunta ao histórico e exibe spinner
        st.session_state[h_key].append({"role": "user", "content": prompt})
        
        with st.spinner(f"Processando via {persona_atual}..."):
            resposta = responder_ia(prompt, st.session_state[h_key], dados_extraidos, persona_atual)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
