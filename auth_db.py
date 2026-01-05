import streamlit as st
from supabase import create_client, Client
import bcrypt

# Buscando as credenciais de forma segura nos Secrets do Streamlit
# Você vai configurar isso no painel do Streamlit Cloud depois
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Erro ao carregar credenciais do Supabase. Verifique os Secrets.")

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    # O Supabase retorna a senha como string, garantimos a codificação aqui
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def cadastrar_usuario(username, email, senha_limpa):
    try:
        senha_protegida = hash_senha(senha_limpa)
        data = {
            "username": username,
            "email": email,
            "password": senha_protegida
        }
        # Insere na tabela 'users' do Supabase
        response = supabase.table("users").insert(data).execute()
        return True, "Usuário cadastrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao cadastrar: {str(e)}"

def buscar_usuario(username):
    try:
        # Busca o usuário pelo nome na tabela
        response = supabase.table("users").select("*").eq("username", username).execute()
        if len(response.data) > 0:
            return response.data[0] # Retorna os dados do usuário encontrado
        return None
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return None
