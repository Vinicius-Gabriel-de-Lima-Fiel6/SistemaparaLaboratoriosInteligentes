import streamlit as st
from supabase import create_client, Client
import bcrypt

# --- Inicialização do Cliente ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Erro ao carregar credenciais: {e}")
    supabase = None

# --- Segurança ---
def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

# --- Funções de Banco ---

def cadastrar_usuario(username, email, senha_limpa, org_id=None, role="tecnico"):
    """
    Cadastra o usuário vinculado a uma organização e com um nível de acesso.
    """
    global supabase
    if supabase is None:
        return False, "Conexão com o banco de dados não disponível."
    
    try:
        senha_protegida = hash_senha(senha_limpa)
        data = {
            "username": username,
            "email": email,
            "password_hash": senha_protegida,
            "org_id": org_id, # ID da Empresa vinculada
            "role": role      # Nível: admin, tecnico ou visualizador
        }
        
        response = supabase.table("users").insert(data).execute()
        return True, "Usuário cadastrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao cadastrar: {str(e)}"

def buscar_usuario(username):
    """
    Busca o usuário e retorna todos os campos, incluindo org_id e role.
    """
    global supabase
    if supabase is None:
        return None
    try:
        # Buscamos todos os campos para alimentar o session_state no app.py
        response = supabase.table("users").select("*").eq("username", username).execute()
        if len(response.data) > 0:
            return response.data[0] 
        return None
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return None

def obter_dados_empresa(org_id):
    """
    Opcional: Busca o nome e informações da empresa do usuário.
    """
    if not org_id or supabase is None:
        return None
    try:
        response = supabase.table("organizations").select("*").eq("id", org_id).execute()
        return response.data[0] if response.data else None
    except:
        return None
