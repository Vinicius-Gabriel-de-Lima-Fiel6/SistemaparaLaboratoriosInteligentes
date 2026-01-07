import streamlit as st
import google.generativeai as genai

# --- 1. FUNÇÃO DE CONEXÃO (FORÇA BRUTA) ---
def configurar_ia():
    try:
        # Verifica se a chave existe nos Secrets do Streamlit
        if "GOOGLE_API_KEY" not in st.secrets:
            return None
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Lista de força bruta: tenta do mais moderno para o mais compatível
        modelos_para_testar = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        for nome_modelo in modelos_para_testar:
            try:
                model = genai.GenerativeModel(nome_modelo)
                # Teste de "fumaça": gera apenas 1 token para validar a conexão
                model.generate_content("oi", generation_config={"max_output_tokens": 1})
                return model # Se funcionar, retorna este modelo imediatamente
            except Exception:
                continue # Se der erro 404 ou 403, pula para o próximo da lista
        
        return None
    except Exception:
        return None

# --- 2. INICIALIZAÇÃO ---
# O modelo é carregado uma única vez ao iniciar o script
model_gemini = configurar_ia()

class LabSmartAI:
    def __init__(self):
        self.model = model_gemini

    def get_ai_answer(self, user_text: str):
        if self.model is None:
            return "Erro: Não foi possível conectar a nenhum modelo Gemini. Verifique sua chave de API e se a biblioteca google-generativeai está no requirements.txt."
        
        try:
            # Comando mestre para garantir resposta em Português
            response = self.model.generate_content(
                f"Você é um assistente técnico de laboratório inteligente. Responda em português: {user_text}"
            )
            return response.text
        except Exception as e:
            return f"Erro na comunicação com a IA: {e}"

# --- 3. INTERFACE DO CHATBOT (A SER CHAMADA PELO APP.PY) ---
def show_chatbot():
    st.header("🤖 Assistente Científico com IA")

    # Garante que a classe da IA está na memória da sessão
    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # Alerta visual caso a conexão falhe completamente
    if bot.model is None:
        st.error("⚠️ Falha na conexão de força bruta. Nenhum modelo (Flash ou Pro) respondeu.")
    else:
        # Mostra qual modelo foi selecionado pelo teste de força bruta
        st.success(f"Conectado com sucesso ao modelo: {bot.model.model_name}")

    st.divider()

    # Histórico do Chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Campo de entrada (O seu teste do 'Oi')
    if prompt := st.chat_input("Digite 'Oi' para testar a conexão..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("IA processando..."):
                resposta = bot.get_ai_answer(prompt)
                st.markdown(resposta)
                st.session_state.chat_history.append({"role": "assistant", "content": resposta})
