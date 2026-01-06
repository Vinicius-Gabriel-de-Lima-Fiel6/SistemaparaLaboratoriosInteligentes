import streamlit as st
from supabase import create_client, Client
import bcrypt

# Buscando as credenciais usando os nomes das etiquetas que você criou
try:
    # Aqui usamos o NOME da variável que está lá na aba branca (Secrets)
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Erro ao carregar credenciais: {e}")
    supabase = None

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def cadastrar_usuario(username, email, senha_limpa):
    global supabase
    if supabase is None:
        return False, "Conexão com o banco de dados não disponível."
    
    try:
        senha_protegida = hash_senha(senha_limpa)
        data = {
            "username": username,
            "email": email,
            "password_hash": senha_protegida  # Ajustado para bater com o SQL que rodamos
        }
        # Insere na tabela 'users' do Supabase
        response = supabase.table("users").insert(data).execute()
        return True, "Usuário cadastrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao cadastrar: {str(e)}"

def buscar_usuario(username):
    global supabase
    if supabase is None:
        return None
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if len(response.data) > 0:
            return response.data[0] 
        return None
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return None
