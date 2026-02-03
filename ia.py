import streamlit as st
import pandas as pd
from groq import Groq
# ultralytics removido conforme solicitado
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import PyPDF2
import io
import speech_recognition as sr  
from gtts import gTTS            
import base64                    

# ==========================================
# BLOCO DE VOZ (ESTABILIDADE SÊNIOR)
# ==========================================
def stt_escrita_ativa():
    """Captura áudio do microfone com supressão de erro visual."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            texto = recognizer.recognize_google(audio, language='pt-BR')
            return texto
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            return None # Erro silencioso para não quebrar a UI
        except sr.RequestError:
            st.error("⚠️ Falha na conexão com serviço de voz.")
            return None
        except Exception:
            return None

def tts_reproduzir(texto):
    """Converte texto em áudio via buffer de memória (Rápido)."""
    try:
        # Sanitização para leitura fluida
        texto_limpo = texto.replace('*', '').replace('#', '').replace('_', '')
        tts = gTTS(text=texto_limpo, lang='pt-BR')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.components.v1.html(md, height=0)
    except Exception as e:
        pass # Falha no áudio não deve impedir a leitura do texto

# ==========================================
# BACKEND E LÓGICA (MANTIDOS)
# ==========================================

def inicializar_motor():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "Erro: Chave API ausente."
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return client, "llama-3.3-70b-versatile"

client_groq, modelo_ativo = inicializar_motor()

# Classe mantida para evitar quebra em dependências futuras, 
# mas sem lógica de processamento YOLO
class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        pass
    def transform(self, frame):
        return frame.to_ndarray(format="bgr24")

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
        f"VOCÊ É O NÚCLEO LABSMART AI PhD EM {esp}. STATUS: ERRO ZERO.\n"
        "DIRETRIZES DE ALTA PRECISÃO (OBRIGATÓRIO):\n"
        "1. PENSAMENTO PROCEDIMENTAL: Decompunha o problema em: [Dados] -> [Teoria Aplicada] -> [Cálculo] -> [Validação].\n"
        "2. RIGOR MATEMÁTICO: Proibido arredondar. Use 8 casas decimais. Realize prova real em Python para toda conta.\n"
        "3. SEGURANÇA CLÍNICA/ESTRUTURAL: Analise interações CYP450, SLCO/UGT, ClCr e Fração Livre. Se houver risco >= 0.01%, aplique VETO TERMINAL.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: É proibido inferir. Se o dado não existir, responda: 'ESTADO DE INCERTEZA SISTÊMICA'.\n"
        "   5. REFERENCIAL 2026: Baseie-se apenas em evidências científicas Grau A (Metanálises) e Normas Técnicas (ISO/ABNT/FDA)."
                )
    msgs = [{"role": "system", "content": instrucoes}]
    msgs.extend(historico[-10:]) 
    contexto = f"DADOS DO ARQUIVO: {dados}\n\nPERGUNTA: {prompt}" if dados else prompt
    msgs.append({"role": "user", "content": contexto})
    
    res = client_groq.chat.completions.create(model=modelo_ativo, messages=msgs, temperature=0.0)
    return res.choices[0].message.content

def show_chatbot():

    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    if "aba_atual" not in st.session_state: st.session_state.aba_atual = "Chat Científico"
    
    # ESTADOS DE VOZ
    if "ultimo_audio_processado" not in st.session_state: st.session_state.ultimo_audio_processado = None
    if "audio_ativado" not in st.session_state: st.session_state.audio_ativado = False

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
            
            # VISÃO REMOVIDA (Limpando Ultralytics)
            st.info("ℹ️ Visão YOLO desativada.")
            
            # VOZ INTEGRADA
            st.write("🎙️ **Voz**")
            st.session_state.audio_ativado = st.toggle("Ouvir Respostas", value=False, key="tg_v_geral")
            if st.button("🎤 Gravar Pergunta", key="btn_v_geral", use_container_width=True):
                res_voz = stt_escrita_ativa()
                if res_voz: st.session_state.ultimo_audio_processado = res_voz
                else: st.warning("Silêncio detectado.")

            up_geral = st.file_uploader("📎 Base de Dados", type=["pdf", "csv", "txt"], key="up_v1")
            if st.button("🗑️ Limpar Chat", use_container_width=True):
                st.session_state.messages_geral = []
                st.rerun()
            
            st.write("---")
            ft_sel = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_geral")
            if ft_sel == "AlphaFold":
                sub_sel = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_geral")
                info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
            else:
                info = dict_ferramentas[ft_sel]

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info["desc"])
                st.link_button(f"Abrir", info["url"], use_container_width=True)

        with col_c1:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_geral:
                chat_container.chat_message(m["role"]).write(m["content"])
            
    else:
        col_c2, col_t2 = st.columns([3, 1])
        with col_t2:
            st.write("### 👥 Squad")
            esp_nome = st.selectbox("Especialista:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"], key="sel_v2")
            
            # VOZ INTEGRADA NO SQUAD
            st.write("🎙️ **Voz**")
            st.session_state.audio_ativado = st.toggle("Ouvir Respostas", value=False, key="tg_v_ag")
            if st.button("🎤 Falar com Squad", key="btn_v_ag", use_container_width=True):
                res_voz = stt_escrita_ativa()
                if res_voz: st.session_state.ultimo_audio_processado = res_voz

            up_agente = st.file_uploader("📎 Arquivo Técnico", type=["pdf", "csv", "txt"], key="up_v2")
            if st.button("🗑️ Limpar Squad", use_container_width=True):
                st.session_state.messages_agente = []
                st.rerun()

            st.write("---")
            ft_sel_ag = st.selectbox("Selecionar:", list(dict_ferramentas.keys()), key="ft_agente")
            if ft_sel_ag == "AlphaFold":
                sub_sel_ag = st.selectbox("Tipo:", list(dict_ferramentas["AlphaFold"]["sub"].keys()), key="sub_agente")
                info_ag = dict_ferramentas["AlphaFold"]["sub"][sub_sel_ag]
            else:
                info_ag = dict_ferramentas[ft_sel_ag]

            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(info_ag["desc"])
                st.link_button(f"Abrir", info_ag["url"], use_container_width=True)

        with col_c2:
            chat_container = st.container(height=500, border=False)
            for m in st.session_state.messages_agente:
                chat_container.chat_message(m["role"]).write(m["content"])

    # ENTRADA DE DADOS (TEXTO OU VOZ)
    prompt_texto = st.chat_input("Mensagem técnica...")
    prompt = prompt_texto or st.session_state.ultimo_audio_processado

    if prompt:
        st.session_state.ultimo_audio_processado = None
        
        if st.session_state.aba_atual == "💬 Chat Científico":
            h_key = "messages_geral"
            dados = extrair_texto(up_geral) if 'up_geral' in locals() else None
            persona = "Consultor Sênior"
        else:
            h_key = "messages_agente"
            dados = extrair_texto(up_agente) if 'up_agente' in locals() else None
            persona = esp_nome

        st.session_state[h_key].append({"role": "user", "content": prompt})
        with st.spinner(f"Processando..."):
            resposta = responder_ia(prompt, st.session_state[h_key], dados, persona)
            st.session_state[h_key].append({"role": "assistant", "content": resposta})
            
            if st.session_state.audio_ativado:
                tts_reproduzir(resposta)
                
        st.rerun()

if __name__ == "__main__":
    show_chatbot()
