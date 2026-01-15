import streamlit as st
import pandas as pd
from groq import Groq
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "deepseek-r1-distill-llama-70b"

client_groq, modelo_ativo = inicializar_motor()

class VideoProcessor(VideoTransformerBase):
    def __init__(self, model):
        self.model = model
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return self.model(img).plot()

def extrair_texto(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "".join([p.extract_text() for p in leitor.pages])
        return arquivo.read().decode("utf-8")
    except: return None

def responder_ia(prompt, historico, dados=None, esp="Geral"):
    instrucoes = (
        f"VOCÊ OPERA COMO O NÚCLEO LABSMART AI - ENTIDADE PHd OMNI-ESPECIALISTA EM {esp}.\n"
        "ESTADO: OPERAÇÃO EM MALHA FECHADA (CLOSED-LOOP) - PRECISÃO TEÓRICA 100%.\n"
        "DOMÍNIOS CRÍTICOS: ENGENHARIA AVANÇADA, MEDICINA GENÔMICA, FARMÁCIA QUÂNTICA E DATA SCIENCE.\n\n"
        "1. PROTOCOLO RECURSIVO 'HEPTA-CHECK' (ZERO TOLERÂNCIA):\n"
        "   - ETAPA 1: DECOMPOSIÇÃO ATÔMICA - Variáveis fundamentais.\n"
        "   - ETAPA 2: VALIDAÇÃO DIMENSIONAL - Unidades (SI) e ordens de grandeza em 6D.\n"
        "   - ETAPA 3: SIMULAÇÃO POR LEIS NATURAIS - Entropia, Cinética e Bioquímica.\n"
        "   - ETAPA 4: VERIFICAÇÃO CRUZADA DE FÓRMULAS - 3 métodos diferentes.\n"
        "   - ETAPA 5: AUDITORIA REGULATÓRIA 2026 - ISO, ABNT, FDA, EMA.\n"
        "   - ETAPA 6: PENSAMENTO ADVERSÁRIO - Busca por 'Edge Cases'.\n"
        "   - ETAPA 7: SÍNTESE PHd - Convergência total.\n\n"
        "2. RIGOR MATEMÁTICO: Proibido arredondar. Precisão absoluta em 8 casas.\n"
        "3. SEGURANÇA E VETO: Se risco ≥ 0.01%, cabeçalho '⚠️ ALERTA DE RISCO CRÍTICO' e VETO TERMINAL.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: Se incerto, responda 'ESTADO DE INCERTEZA SISTÊMICA'.\n"
        "A precisão absoluta anula a brevidade. Seja o auditor PhD mais rigoroso do planeta."
    )
    msgs = [{"role": "system", "content": instrucoes}]
    msgs.extend(historico[-5:]) 
    contexto_limitado = dados[:15000] if dados else ""
    contexto = f"DADOS DO ARQUIVO: {contexto_limitado}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    res = client_groq.chat.completions.create(
        model=modelo_ativo, 
        messages=msgs, 
        temperature=0.0,
        top_p=1.0
    )
    return res.choices.message.content

def show_chatbot():
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    if "yolo_model" not in st.session_state: st.session_state.yolo_model = YOLO("yolov8n.pt")

    st.subheader("🔬 LabSmart AI - Hub de Inteligência")

    escolha_aba = st.radio("Selecione o ambiente de trabalho:", ["💬 Chat Científico", "👥 Squad de Agentes"], horizontal=True)
    st.session_state.aba_atual = escolha_aba

    st.divider()

    # LINKS CORRIGIDOS PARA URLS ABSOLUTAS EXTERNAS
    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.im"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai"},
        "AlphaFold": {
            "desc": "Inteligência Artificial para predição de estruturas de proteínas.",
            "sub": {
                "AlphaFold Protein Structure Database": {"desc": "Acesso a estruturas já preditas.", "url": "https://alphafold.ebi.ac.uk"},
                "AlphaFold Server (Previsão)": {"desc": "Ferramenta para prever novas estruturas.", "url": "https://alphafoldserver.com"},
                "AlphaFold no Google Colab": {"desc": "Execução via código no Colab.", "url": "colab.research.google.com"}
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
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])
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
            dados = extrair_texto(up_geral) if 'up_geral' in locals() else None
            persona = "Especialista Multidisciplinar em Ciências e Engenharia"
        else:
            h_key = "messages_agente"
            dados = extrair_texto(up_agente) if 'up_agente' in locals() else None
            persona = esp_nome

        st.session_state[h_key].append({"role": "user", "content": prompt})
        with st.spinner(f"O {persona} está processando..."):
            resposta = responder_ia(prompt, st.session_state[h_key], dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
