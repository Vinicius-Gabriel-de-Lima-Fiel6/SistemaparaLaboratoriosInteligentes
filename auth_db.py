import streamlit as st
from supabase import create_client, Client
import bcrypt

# --- Inicialização ---
try:
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

# --- Funções de Negócio ---

def cadastrar_usuario(username, email, senha_limpa, org_name, role):
    global supabase
    if supabase is None: return False, "Erro de conexão."
    
    try:
        senha_protegida = hash_senha(senha_limpa)
        data = {
            "username": username,
            "email": email,
            "password_hash": senha_protegida,
            "org_name": org_name, # Nome da empresa informado no cadastro
            "role": role         # ADM, Tecnico ou Visualizador
        }
        supabase.table("users").insert(data).execute()
        return True, "Cadastro realizado com sucesso!"
    except Exception as e:
        return False, f"Erro: Este e-mail já pode estar em uso."

def buscar_usuario_por_email(email):
    global supabase
    if supabase is None: return None
    try:
        # Mudamos a busca de 'username' para 'email'
        response = supabase.table("users").select("*").eq("email", email).execute()
        if len(response.data) > 0:
            return response.data[0] 
        return None
    except Exception as e:
        return None
