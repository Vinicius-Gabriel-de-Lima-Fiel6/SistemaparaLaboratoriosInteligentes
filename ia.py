import streamlit as st
import pandas as pd
from groq import Groq
import PyPDF2
import io
import time
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURAÇÃO DE AMBIENTE E CSS ---
def aplicar_estilo_customizado():
    """Aplica o CSS definitivo para alinhamento na base e design industrial."""
    st.markdown("""
        <style>
        /* Ajuste de padding do container principal */
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
        
        /* Alinhamento das colunas do input na base (Crucial para o visual da foto) */
        [data-testid="column"] {
            display: flex;
            align-items: flex-end !important;
            justify-content: center;
            padding-bottom: 10px;
        }

        /* Nivelamento do Popover e do Microfone com o Chat Input */
        .stPopover, .stMicRecorder {
            margin-bottom: 12px !important;
        }

        /* Estilo para botões dentro do Popover */
        .stPopover button {
            border-radius: 8px;
        }

        /* Customização das mensagens de chat para legibilidade técnica */
        .stChatMessage {
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 10px;
        }

        /* Esconder labels vazios para evitar avisos de acessibilidade */
        div[data-testid="stMarkdownContainer"] p {
            margin-bottom: 0px;
        }
        </style>
        """, unsafe_allow_html=True)

# --- 2. MOTOR DE INTELIGÊNCIA (GROQ CORE) ---
def inicializar_motor():
    """Inicializa o cliente Groq com o modelo Llama 3.3 70B."""
    if "GROQ_API_KEY" not in st.secrets:
        return None, "CHAVE_API_AUSENTE"
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        # Modelo atualizado conforme solicitação do usuário
        return client, "llama-3.3-70b-versatile"
    except Exception:
        return None, "ERRO_CONEXAO"

client_groq, modelo_ativo = inicializar_motor()

# --- 3. FUNÇÕES TÉCNICAS (PROCESSAMENTO DE DADOS) ---

def transcrever_audio(audio_bytes):
    """Converte áudio (bytes) em texto usando Whisper-Large-v3."""
    if not client_groq or not audio_bytes:
        return None
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio_temp.wav"
        transcricao = client_groq.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3",
            response_format="text",
            language="pt"
        )
        return transcricao
    except Exception as e:
        st.toast(f"🎤 Erro na transcrição: {str(e)}", icon="⚠️")
        return None

def extrair_dados_tecnicos(arquivo):
    """Extrai texto de múltiplos formatos (PDF, CSV, TXT) com tratamento de erro."""
    if not arquivo:
        return None
    try:
        extensao = arquivo.name.split('.')[-1].lower()
        if extensao == 'pdf':
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            return "\n".join([pagina.extract_text() for pagina in leitor.pages if pagina.extract_text()])
        elif extensao == 'csv':
            df = pd.read_csv(arquivo)
            return df.to_string()
        elif extensao == 'txt':
            return arquivo.read().decode("utf-8")
        return "Formato não suportado."
    except Exception as e:
        st.toast(f"📂 Falha no processamento do arquivo: {str(e)}", icon="❌")
        return None

def responder_ia(prompt, historico, dados_contexto=None, especialidade="Geral"):
    """Gerador de respostas com rigor científico PhD e Negação de Alucinação."""
    if not client_groq:
        return "🚨 ERRO SISTÊMICO: Núcleo Groq não inicializado."

    diretriz_phd = (
        f"VOCÊ É O NÚCLEO LABSMART AI - DOUTORADO EM {especialidade.upper()}.\n"
        "STATUS: OPERAÇÃO EM TEMPO REAL (FEVEREIRO 2026).\n\n"
        "PROTOCOLOS RÍGIDOS:\n"
        "1. PENSAMENTO PROCEDIMENTAL: Decompunha o problema: [DADOS] > [TEORIA APLICADA] > [CÁLCULO] > [VALIDAÇÃO].\n"
        "2. RIGOR MATEMÁTICO: Use 8 casas decimais. Forneça o código Python para simulação completa de cada conta.\n"
        "3. SEGURANÇA: Verifique interações CYP450, farmacocinética e normas ABNT/ISO/FDA. Se houver risco >= 0.01%, aplique VETO TERMINAL.\n"
        "4. NEGAÇÃO DE ALUCINAÇÃO: Se faltar dado, responda estritamente: 'ESTADO DE INCERTEZA SISTÊMICA'.\n"
        "5. VISUALIZAÇÃO: Descreva a estrutura para um mini-gráfico referente aos dados analisados."
    )

    mensagens = [{"role": "system", "content": diretriz_phd}]
    
    # Mantém contexto histórico sem sobrecarga (últimas 10 interações)
    for m in historico[-10:]:
        if m["role"] != "system":
            mensagens.append({"role": m["role"], "content": m["content"]})
    
    # Inserção de contexto de arquivo se existir
    input_formatado = f"CONTEXTO TÉCNICO:\n{dados_contexto}\n\nPERGUNTA: {prompt}" if dados_contexto else prompt
    mensagens.append({"role": "user", "content": input_formatado})

    try:
        response = client_groq.chat.completions.create(
            model=modelo_ativo,
            messages=mensagens,
            temperature=0.0,  # Zero para máxima precisão científica
            max_tokens=4096
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ ESTADO DE INCERTEZA SISTÊMICA: Erro na conexão ({str(e)})"

# --- 4. INTERFACE DO USUÁRIO (MODULE ENTRY POINT) ---

def show_chatbot():
    """Função principal que renderiza o Hub de IA."""
    aplicar_estilo_customizado()

    # Inicialização de estados (Session State)
    if "messages_geral" not in st.session_state: st.session_state.messages_geral = []
    if "messages_agente" not in st.session_state: st.session_state.messages_agente = []
    
    st.subheader("🔬 Synapse AI - Hub de Inteligência")

    # Seleção de Ambiente (Tabs)
    escolha_aba = st.radio(
        "Ambiente:", 
        ["💬 Chat Científico", "👥 Squad de Agentes"], 
        horizontal=True, 
        label_visibility="collapsed"
    )
    st.divider()

    # Dicionário de Ferramentas (Mantendo a estrutura original solicitada)
    dict_ferramentas = {
        "Lovable": {"desc": "Crie interfaces e protótipos de sistemas internos sem programar.", "url": "https://lovable.dev/"},
        "Gamma": {"desc": "Transforme dados em apresentações profissionais em segundos.", "url": "https://gamma.app/"},
        "Manus": {"desc": "Agente de IA para execução de tarefas digitais e pesquisas.", "url": "https://manus.ai/"},
        "Perplexity": {"desc": "Buscador técnico para verificação de artigos e fatos.", "url": "https://www.perplexity.ai/"},
        "AlphaFold": {
            "desc": "IA para predição de estruturas de proteínas.",
            "sub": {
                "Protein Database": {"desc": "Acesso a 200M+ estruturas de proteínas.", "url": "https://alphafold.ebi.ac.uk/"},
                "AlphaFold Server": {"desc": "Ferramenta para prever novas interações.", "url": "https://alphafoldserver.com/"},
                "AlphaFold Colab": {"desc": "Execução via código para pesquisas.", "url": "https://colab.research.google.com/"}
            }
        }
    }

    # Definição de Persona baseada na aba
    if escolha_aba == "💬 Chat Científico":
        h_key, persona = "messages_geral", "Consultor Sênior em Engenharia e Medicina"
    else:
        h_key = "messages_agente"
        col_esp, _ = st.columns([1, 2])
        with col_esp:
            persona = st.selectbox("Especialista Ativo:", ["Bioquímico Sênior", "Auditor de Qualidade", "Escritor Técnico"])

    # Exibição do Histórico de Mensagens
    chat_container = st.container(height=500, border=False)
    with chat_container:
        for m in st.session_state[h_key]:
            with st.chat_message(m["role"]):
                st.write(m["content"])

    # --- BARRA DE COMANDO (ALINHADA À FASE DE INPUT) ---
    input_row = st.container()
    with input_row:
        c_plus, c_mic, c_txt = st.columns([0.07, 0.07, 0.86])
        
        with c_plus:
            with st.popover("➕", use_container_width=True):
                st.markdown("### 📎 Arquivos e Ferramentas")
                # RESOLUÇÃO DO ERRO DE LABEL: Label com texto ocultado via visibility
                up_file = st.file_uploader("Enviar base de dados técnica", type=["pdf", "csv", "txt"], label_visibility="collapsed", key="uploader_principal")
                
                st.divider()
                st.markdown("### 🛠️ Auxiliares")
                ft_sel = st.selectbox("Selecionar Ferramenta:", list(dict_ferramentas.keys()), label_visibility="visible")
                
                if ft_sel == "AlphaFold":
                    sub_sel = st.selectbox("Tipo de acesso:", list(dict_ferramentas["AlphaFold"]["sub"].keys()))
                    info = dict_ferramentas["AlphaFold"]["sub"][sub_sel]
                else:
                    info = dict_ferramentas[ft_sel]

                st.info(info["desc"])
                st.link_button(f"Abrir {ft_sel}", info["url"], use_container_width=True)

                if st.button("🗑️ Limpar Conversa", type="primary", use_container_width=True):
                    st.session_state[h_key] = []
                    st.rerun()

        with c_mic:
            # Key dinâmica para evitar conflito entre abas
            gravacao = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=f"mic_{h_key}")

        with c_txt:
            prompt_texto = st.chat_input("Digite sua dúvida técnica ou use o microfone...")

    # --- PROCESSAMENTO DE ENTRADA (LÓGICA BLINDADA) ---
    entrada_final = None

    if prompt_texto:
        entrada_final = prompt_texto
    elif gravacao and gravacao.get('bytes'):
        with st.spinner("Decodificando áudio..."):
            entrada_final = transcrever_audio(gravacao['bytes'])

    if entrada_final:
        # Adiciona entrada ao histórico
        st.session_state[h_key].append({"role": "user", "content": entrada_final})
        with chat_container:
            with st.chat_message("user"):
                st.write(entrada_final)

        # Extração de contexto de arquivo
        conteudo_anexo = extrair_dados_tecnicos(up_file) if up_file else None

        # Resposta da IA
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"O {persona} está processando..."):
                    resposta_ia = responder_ia(entrada_final, st.session_state[h_key], conteudo_anexo, persona)
                    st.write(resposta_ia)
                    st.session_state[h_key].append({"role": "assistant", "content": resposta_ia})
        
        # Rerun controlado para atualizar interface
        st.rerun()

# --- DISPARO DO MÓDULO ---
if __name__ == "__main__":
    show_chatbot()
