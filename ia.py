import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURAÇÃO DE FORÇA BRUTA (EXTERNA À CLASSE) ---
def inicializar_modelo_seguro():
    """Tenta conectar em todos os modelos possíveis para evitar erro 404."""
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "Chave não encontrada nos Secrets"
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Lista exaustiva para o teste de força bruta
        modelos_disponiveis = [
            'gemini-1.5-flash', 
            'gemini-1.5-pro', 
            'gemini-pro', 
            'gemini-1.0-pro',
            'gemini-1.5-flash-8b'
        ]
        
        for nome in modelos_disponiveis:
            try:
                model = genai.GenerativeModel(nome)
                # Teste de comunicação (Smoke Test)
                model.generate_content("oi", generation_config={"max_output_tokens": 1})
                return model, nome  # Retorna o primeiro que responder com sucesso
            except Exception:
                continue
                
        return None, "Nenhum modelo disponível para esta chave"
    except Exception as e:
        return None, str(e)

# Inicialização global para performance
modelo_global, nome_modelo_ativo = inicializar_modelo_seguro()

# --- 2. CLASSE DE INTEGRAÇÃO ---
class LabSmartAI:
    def __init__(self):
        self.model = modelo_global
        self.nome_modelo = nome_modelo_ativo

    def get_ai_answer(self, user_text: str):
        if self.model is None:
            return f"Erro de Conexão: {self.nome_modelo}. Verifique sua API Key."
        
        try:
            # Contexto de assistente de laboratório
            prompt_eng = f"Você é um assistente técnico de laboratório especializado. Responda em português: {user_text}"
            response = self.model.generate_content(prompt_eng)
            return response.text
        except Exception as e:
            return f"Erro ao processar consulta com o modelo {self.nome_modelo}: {e}"

# --- 3. FUNÇÃO MESTRA (CHAMADA PELO SEU SISTEMA PRINCIPAL) ---
def show_chatbot():
    """Função de interface chamada pelo app.py"""
    st.header("🤖 Assistente Científico LabSmart")

    # Garante que a classe está instanciada na sessão do Streamlit
    if "ia_engine" not in st.session_state:
        st.session_state.ia_engine = LabSmartAI()
    
    bot = st.session_state.ia_engine

    # Painel de Diagnóstico (Ajuda a identificar qual modelo funcionou)
    if bot.model:
        st.success(f"✅ Motor de IA Ativo: **{bot.nome_modelo}**")
    else:
        st.error(f"❌ Falha Crítica: {bot.nome_modelo}")
        st.info("Dica: Verifique se o seu requirements.txt contém: google-generativeai>=0.8.3")

    st.divider()

    # Histórico de Conversas
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada do Usuário para o Teste
    if prompt := st.chat_input("Digite 'Oi' para testar a força bruta..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"Consultando {bot.nome_modelo}..."):
                resposta = bot.get_ai_answer(prompt)
                st.markdown(resposta)
                st.session_state.chat_history.append({"role": "assistant", "content": resposta})
