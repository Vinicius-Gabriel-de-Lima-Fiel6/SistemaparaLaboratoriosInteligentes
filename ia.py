import streamlit as st
import google.generativeai as genai
import os

# --- MOTOR DE CONEXÃO DEFINITIVO ---
def inicializar_ia_total():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "Chave GOOGLE_API_KEY não configurada nos Secrets."
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        
        # FORÇA O USO DE REST (HTTP) EM VEZ DE GRPC
        # Isso resolve 90% dos problemas de 'Model not found' no Streamlit Cloud
        genai.configure(api_key=api_key, transport='rest')
        
        # Lista de modelos para teste
        modelos_para_tentar = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        detalhes_erro = []

        for nome in modelos_para_tentar:
            try:
                model = genai.GenerativeModel(nome)
                # Teste de resposta
                model.generate_content("oi", generation_config={"max_output_tokens": 1})
                return model, nome
            except Exception as e:
                detalhes_erro.append(f"{nome}: {str(e)}")
                continue
        
        return None, " | ".join(detalhes_erro)
    except Exception as e:
        return None, f"Erro Geral: {str(e)}"

# Inicialização
motor_ia, modelo_vencedor = inicializar_ia_total()

class LabSmartAI:
    def __init__(self):
        self.model = motor_ia

    def get_ai_answer(self, user_text: str):
        if self.model is None:
            return f"Erro técnico: {modelo_vencedor}"
        try:
            response = self.model.generate_content(user_text)
            return response.text
        except Exception as e:
            return f"Erro na resposta: {e}"

def show_chatbot():
    st.header("🤖 Assistente Científico")
    
    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    if bot.model:
        st.success(f"✅ IA Conectada: {modelo_vencedor}")
    else:
        st.error("❌ Falha Crítica de Conexão")
        with st.expander("Ver Erro Real do Google"):
            st.code(modelo_vencedor)
        st.warning("Se o erro acima mencionar 'User location not supported', o Streamlit Cloud está bloqueado na sua região.")

    # ... restante do seu código de Chat e Botões (PubMed, etc)
    if prompt := st.chat_input("Pergunte algo..."):
        st.chat_message("user").markdown(prompt)
        resposta = bot.get_ai_answer(prompt)
        st.chat_message("assistant").markdown(resposta)
