import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io
import logging

# Configuração de Logs para identificar erros ocultos
logging.basicConfig(level=logging.INFO)

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, f"Erro ao conectar na Groq: {e}"

client_groq, modelo_ativo = inicializar_motor()

# Classe de Visão Ajustada para não travar o sistema
class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model

    def transform(self, frame):
        try:
            img = frame.to_ndarray(format="bgr24")
            # Rodar inferência com threshold de segurança
            results = self.model(img, stream=False, conf=0.25)
            return results[0].plot()
        except Exception as e:
            logging.error(f"Erro no processamento de vídeo: {e}")
            return frame.to_ndarray(format="bgr24")

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except Exception as e:
        logging.error(f"Erro na extração de texto: {e}")
        return None

def responder_ia(prompt, historico, dados=None, esp="Geral"):
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
    msgs.extend(historico[-10:]) 
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    try:
        res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
        return res.choices[0].message.content
    except Exception as e:
        return f"ERRO CRÍTICO NA API: {e}"

@st.cache_resource
def carregar_modelo():
    # Carrega o modelo uma única vez para economizar memória
    try:
        return YOLO("yolov8n.pt")
    except Exception as e:
        st.error(f"Erro ao carregar YOLO: {e}")
        return None

def show_chatbot():
    # Inicialização de estados
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    if "yolo_model" not in st.session_state: st.session_state.yolo_model = carregar_modelo()

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

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
                "AlphaFold Protein Structure Database": {"desc": "Acesso a mais de 200 milhões de estruturas de proteínas já preditas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server (Previsão)": {"desc": "Ferramenta para prever novas estruturas de proteínas e interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold no Google Colab": {"desc": "Execução do modelo via código para pesquisas personalizadas.", "url": "https://colab.research.google.com/github/google-deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb"}
            }
        }
    }

    if st.session_state.aba_atual == "💬 Chat Científico":
        col_c1, col_t1 = st.columns([3, 1])
        with col_t1:
            st.write("### ⚙️ Ferramentas")
            if st.toggle("🎥 Visão YOLO", key="tgl_v1"):
                if st.session_state.yolo_model:
                    webrtc_streamer(
                        key="stream_v1", 
                        video_processor_factory=lambda: VideoProcessor(st.session_state.yolo_model),
                        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}, # Estabiliza conexão
                        media_stream_constraints={"video": True, "audio": False}
                    )
                else:
                    st.error("Modelo de visão offline.")
            
            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            if st.button("🗑️ Limpar Chat"):
                st.session_state.messages_geral = []
                st.rerun()
            
            st.write("---")
            st.write("🛠️ **Auxiliares**")
            ft_sel = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_geral")
            
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Tipo de AlphaFold:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_geral")
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
                btn_label = sub_sel
            else:
                info = dict_ferramentas[ft_sel]
                btn_label = ft_sel

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info["desc"])
                st.link_button(f"Abrir {btn_label}", info["url"], use_container_width=True)

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
            st.write("🛠️ **Auxiliares**")
            ft_sel_ag = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_agente")
            
            if ft_sel_ag == "AlphaFold":
                sub_sel_ag = st.selectbox("Tipo de AlphaFold:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_agente")
                info_ag = dict_ferramentas["AlphaFold"]["sub"][sub_sel_ag]
                btn_label_ag = sub_sel_ag
            else:
                info_ag = dict_ferramentas[ft_sel_ag]
                btn_label_ag = ft_sel_ag

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info_ag["desc"])
                st.link_button(f"Abrir {btn_label_ag}", info_ag["url"], use_container_width=True)

        with col_c2:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_agente:
                chat_container.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input("Digite sua mensagem para o ambiente selecionado..."):
        if st.session_state.aba_atual == "💬 Chat Científico":
            h_key = "messages_geral"
            conteudo_dados = extrair_texto(up_geral) if up_geral else None
            persona = "Consultor Sênior em Engenharia, Medicina de Precisão e Auditoria Científica"
        else:
            h_key = "messages_agente"
            conteudo_dados = extrair_texto(up_agente) if up_agente else None
            persona = esp_nome

        st.session_state[h_key].append({"role": "user", "content": prompt})
        with st.spinner(f"O {persona} está processando..."):
            resposta = responder_ia(prompt, st.session_state[h_key], conteudo_dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
