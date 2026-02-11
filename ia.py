import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="SynapseLab AI ", 
    page_icon="🧬",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. CSS AVANÇADO (Alinhamento Perfeito e UI Limpa) ---
st.markdown("""
    <style>
    /* Ajuste geral do container */
    .block-container { padding-top: 1.5rem; }
    
    /* Alinha os botões (Mic e Popover) na base para nivelar com o Chat Input */
    [data-testid="column"] {
        display: flex;
        align-items: flex-end !important;
        justify-content: center;
    }

    /* Remove margens extras dos componentes auxiliares */
    .stPopover button, .stMicRecorder button {
        border-radius: 8px !important;
        height: 48px !important; /* Altura padrão do chat input */
        width: 100% !important;
    }

    /* Estilo para mensagens de erro/aviso */
    .stToast { background-color: #262730; color: white; }
    
    /* Ocultar elementos desnecessários do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTÃO DE ESTADO (SESSION STATE) ---
if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
if "conteudo_arquivo" not in st.session_state: st.session_state.conteudo_arquivo = None
if "nome_arquivo" not in st.session_state: st.session_state.nome_arquivo = None

# --- 4. MOTOR DE INTELIGÊNCIA ---
def inicializar_motor():
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return None, "⚠️ ERRO CRÍTICO: Chave API não encontrada nos secrets."
    try:
        client = Groq(api_key=api_key)
        return client, "llama-3.3-70b-versatile"
    except Exception as e:
        return None, f"⚠️ Erro de Conexão: {e}"

client_groq, modelo_ativo = inicializar_motor()

# --- 5. FUNÇÕES TÉCNICAS (Core) ---

def transcrever_audio(audio_data):
    """Converte áudio em texto usando Whisper via Groq."""
    if not client_groq: 
        st.error("Motor de IA não inicializado.")
        return None
    
    if not audio_data or 'bytes' not in audio_data:
        return None

    try:
        # Cria um arquivo em memória com nome .wav para a API aceitar
        audio_bytes = audio_data['bytes']
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "gravacao.wav" 
        
        transcription = client_groq.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3",
            response_format="text",
            language="pt"
        )
        return transcription
    except Exception as e:
        st.error(f"Erro na transcrição: {e}")
        return None

def processar_arquivo(uploaded_file):
    """Extrai texto de PDF, CSV ou TXT e salva no estado."""
    if not uploaded_file: return None
    
    texto_extraido = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            texto_extraido = "\n".join([p.extract_text() for p in leitor.pages if p.extract_text()])
        
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            texto_extraido = df.to_string() # Converte tabela para string
            
        elif uploaded_file.name.endswith('.txt'):
            texto_extraido = uploaded_file.read().decode("utf-8")
            
        # Salva no estado para persistência
        st.session_state.conteudo_arquivo = texto_extraido
        st.session_state.nome_arquivo = uploaded_file.name
        return texto_extraido
    except Exception as e:
        st.toast(f"Erro ao ler arquivo: {e}", icon="❌")
        return None

def responder_ia(prompt, historico, contexto_arquivo=None, persona="Especialista Geral"):
    """Gera a resposta da IA com instruções de sistema rigorosas."""
    if not client_groq:
        return "⚠️ O sistema não está conectado à API."

    # Prompt do Sistema (System Message)
    instrucoes_sistema = (
        f"VOCÊ É O NÚCLEO LABSMART AI - PERFIL: {persona}.\n"
        "STATUS OPERACIONAL: MÁXIMA PRECISÃO.\n\n"
        "PROTOCOLOS OBRIGATÓRIOS:\n"
        "1. ESTRUTURA: Responda sempre em Markdown bem formatado.\n"
        "2. RACIOCÍNIO: Pense passo-a-passo: [Análise] -> [Teoria] -> [Aplicação].\n"
        "3. CÁLCULOS: Para qualquer matemática, forneça o script Python completo para validação.\n"
        "4. SEGURANÇA: Se houver risco biológico, químico ou de dados, emita um ALERTA VERMELHO.\n"
        "5. CONTEXTO: Use os dados do arquivo fornecido como verdade absoluta se disponíveis.\n"
        "6. ESTILO: Seja direto, técnico e elimine verborragia desnecessária."
    )
    
    # Montagem das mensagens
    mensagens = [{"role": "system", "content": instrucoes_sistema}]
    
    # Adiciona contexto do arquivo se existir
    if contexto_arquivo:
        mensagens.append({"role": "system", "content": f"### DADOS DO ARQUIVO CARREGADO ({st.session_state.nome_arquivo}):\n{contexto_arquivo[:20000]}..."}) # Limite de chars para não estourar

    # Adiciona histórico recente (últimas 6 mensagens para economizar tokens)
    for m in historico[-6:]:
        if m["role"] != "system":
            mensagens.append({"role": m["role"], "content": m["content"]})
    
    mensagens.append({"role": "user", "content": prompt})

    try:
        completion = client_groq.chat.completions.create(
            model=modelo_ativo,
            messages=mensagens,
            temperature=0.1, # Baixa temperatura para precisão
            max_tokens=2048,
            stream=True
        )
        
        # Generator para streamar a resposta
        resposta_completa = ""
        placeholder = st.empty()
        for chunk in completion:
            if chunk.choices[0].delta.content:
                texto_chunk = chunk.choices[0].delta.content
                resposta_completa += texto_chunk
                placeholder.markdown(resposta_completa + "▌")
        
        placeholder.markdown(resposta_completa)
        return resposta_completa

    except Exception as e:
        return f"⚠️ FALHA NO NÚCLEO DE PROCESSAMENTO: {str(e)}"

# --- 6. INTERFACE DE USUÁRIO (UI) ---

def show_interface():
    st.title("🔬 LabSmart AI - Hub de Inteligência")
    
    # Navegação
    aba_selecionada = st.radio(
        "Modo de Operação:", 
        ["💬 Chat Científico", "👥 Squad de Agentes"], 
        horizontal=True, 
        label_visibility="collapsed"
    )
    st.divider()

    # Configuração de Persona e Histórico baseado na aba
    if aba_selecionada == "💬 Chat Científico":
        chave_hist = "messages_geral"
        persona_atual = "Consultor Sênior em Engenharia e Medicina"
    else:
        chave_hist = "messages_agente"
        col_persona, _ = st.columns([1, 3])
        with col_persona:
            persona_atual = st.selectbox(
                "Especialista Ativo:", 
                ["Bioquímico Sênior", "Auditor de Qualidade", "Cientista de Dados", "Engenheiro de Prompt"]
            )

    # Dicionário de Ferramentas (Corrigido)
    dict_ferramentas = {
        "Lovable": {"desc": "Criação de interfaces web.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Geração de slides e apresentações.", "url": "https://gamma.app/"},
        "SciSpace": {"desc": "Pesquisa em papers acadêmicos.", "url": "https://typeset.io/"},
        "AlphaFold DB": {"desc": "Banco de dados de estruturas proteicas.", "url": "https://alphafold.ebi.ac.uk/"}
    }

    # Container de Chat
    chat_container = st.container(height=500)
    with chat_container:
        if not st.session_state[chave_hist]:
            st.markdown(f"*O sistema está pronto. Especialista **{persona_atual}** online.*")
        
        for msg in st.session_state[chave_hist]:
            st.chat_message(msg["role"]).write(msg["content"])

    # --- ÁREA DE INPUT (A Lógica Complexa) ---
    st.write("") # Espaçamento
    col_tools, col_mic, col_input = st.columns([0.1, 0.1, 0.8])

    # 1. Botão de Ferramentas e Upload
    with col_tools:
        with st.popover("➕", use_container_width=True):
            st.caption("📂 **Análise de Arquivos**")
            arquivo_upload = st.file_uploader("", type=["pdf", "csv", "txt"], key="main_uploader")
            
            # Processamento imediato do arquivo
            if arquivo_upload:
                if st.session_state.nome_arquivo != arquivo_upload.name:
                    with st.spinner("Processando dados..."):
                        processar_arquivo(arquivo_upload)
                        st.success("Dados carregados na memória!")

            st.divider()
            st.caption("🛠️ **Ferramentas Externas**")
            ferramenta = st.selectbox("Link Rápido:", list(dict_ferramentas.keys()))
            if st.button("Acessar Link", use_container_width=True):
                st.markdown(f"[Abrir {ferramenta}]({dict_ferramentas[ferramenta]['url']})")
            
            if st.button("🗑️ Limpar Memória", type="primary", use_container_width=True):
                st.session_state[chave_hist] = []
                st.session_state.conteudo_arquivo = None
                st.session_state.nome_arquivo = None
                st.rerun()

    # 2. Botão de Microfone
    audio_input_data = None
    with col_mic:
        # mic_recorder retorna um dict quando termina a gravação
        audio_input_data = mic_recorder(
            start_prompt="🎙️", 
            stop_prompt="⏹️", 
            just_once=True,
            key="recorder_main"
        )

    # 3. Input de Texto
    with col_input:
        texto_input = st.chat_input("Digite sua pergunta técnica...")

    # --- LÓGICA DE UNIFICAÇÃO DE ENTRADA ---
    prompt_final = None

    # Prioridade 1: Texto digitado
    if texto_input:
        prompt_final = texto_input
    
    # Prioridade 2: Áudio gravado (se houver dados novos)
    elif audio_input_data and 'bytes' in audio_input_data:
        with st.spinner("Transcrevendo áudio..."):
            texto_transcrito = transcrever_audio(audio_input_data)
            if texto_transcrito:
                prompt_final = texto_transcrito

    # Execução da Resposta
    if prompt_final:
        # Exibe pergunta do usuário
        with chat_container:
            st.chat_message("user").write(prompt_final)
        
        # Salva no histórico
        st.session_state[chave_hist].append({"role": "user", "content": prompt_final})

        # Gera resposta da IA
        with chat_container:
            with st.chat_message("assistant"):
                # Aviso visual se houver arquivo em contexto
                if st.session_state.conteudo_arquivo:
                    st.caption(f"📎 Analisando com base em: {st.session_state.nome_arquivo}")
                
                # Chama a IA
                resposta = responder_ia(
                    prompt_final, 
                    st.session_state[chave_hist], 
                    st.session_state.conteudo_arquivo, 
                    persona_atual
                )
                
                # Salva resposta no histórico (necessário pois o responder_ia faz stream mas não salva direto no state)
                st.session_state[chave_hist].append({"role": "assistant", "content": resposta})
        
        # Recarrega para limpar o input e preparar próxima interação
        st.rerun()

if __name__ == "__main__":
    if "GROQ_API_KEY" not in st.secrets:
        st.error("⛔ PARE: Você precisa configurar a 'GROQ_API_KEY' no arquivo .streamlit/secrets.toml")
        st.info("Crie uma conta em https://console.groq.com/keys e adicione a chave.")
    else:
        show_interface()
