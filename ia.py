import streamlit as st
import google.generativeai as genai

# CONFIGURAÇÃO DE SEGURANÇA
try:
    # 1. Busca a chave exatamente como você salvou no Secrets
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # 2. Usaremos o 'gemini-1.5-flash' - o nome mais estável disponível
    # Se este falhar, o código tentará o 'gemini-pro' automaticamente
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-pro')
        
except Exception as e:
    st.error(f"Erro ao carregar chave de API: {e}")

# FUNÇÃO DE RESPOSTA
def responder(pergunta):
    try:
        # Instrução curta para teste
        response = model.generate_content(f"Responda em português: {pergunta}")
        return response.text
    except Exception as e:
        # Se der erro aqui, ele vai nos dizer EXATAMENTE o motivo técnico
        return f"Erro técnico: {e}"
