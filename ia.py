import streamlit as st
import google.generativeai as genai

def inicializar_ia_final():
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return None, "Chave ausente."
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        
        # 1. Configuração com transporte REST (mais estável para Cloud)
        genai.configure(api_key=api_key, transport='rest')
        
        # 2. Tentar o modelo 'gemini-pro' (1.0), que é o mais aceito globalmente 
        # em servidores onde o 1.5 Flash sofre bloqueio regional.
        modelos = ['gemini-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']
        
        for nome in modelos:
            try:
                model = genai.GenerativeModel(nome)
                # Teste com uma pergunta neutra
                model.generate_content("Hello", generation_config={"max_output_tokens": 1})
                return model, nome
            except Exception as e:
                if "location" in str(e).lower():
                    continue # Pula para o próximo se o erro for localização
                continue
        
        return None, "Bloqueio Regional do Google: O servidor do Streamlit não tem permissão nesta zona."
    except Exception as e:
        return None, str(e)

# O restante do seu código (classe LabSmartAI e show_chatbot) continua igual.
