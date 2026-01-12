import streamlit as st
from supabase import create_client, Client
import bcrypt

# Conexão
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def buscar_usuario_por_email(email):
    res = supabase.table("users").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None

def cadastrar_usuario(username, email, senha_limpa, org_name, role):
    try:
        senha_protegida = hash_senha(senha_limpa)
        # O org_id é pego automaticamente do session_state como estava antes
        org_id = st.session_state.user_data.get('org_id')
        
        user_payload = {
            "username": username,
            "email": email,
            "password_hash": senha_protegida,
            "org_name": org_name,
            "org_id": org_id,
            "role": role
        }
        supabase.table("users").insert(user_payload).execute()
        return True, "Cadastro realizado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
