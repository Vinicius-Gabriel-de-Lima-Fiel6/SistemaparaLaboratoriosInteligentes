import streamlit as st
from supabase import create_client, Client
import bcrypt

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

# Esta função precisa ter exatamente este nome para o app.py funcionar
def buscar_usuario_por_email(email):
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        return None

def cadastrar_usuario(username, email, senha_limpa, org_name, role):
    try:
        senha_protegida = hash_senha(senha_limpa)
        # Tenta pegar o org_id do usuário logado
        org_id = st.session_state.user_data.get('org_id')
        
        user_payload = {
            "username": username, "email": email, "password_hash": senha_protegida,
            "org_name": org_name, "org_id": org_id, "role": role
        }
        supabase.table("users").insert(user_payload).execute()
        return True, "Sucesso"
    except Exception as e:
        return False, str(e)

def excluir_usuario_por_id(id_usuario):
    try:
        supabase.table("users").delete().eq("id", id_usuario).execute()
        return True, "Removido"
    except Exception as e:
        return False, str(e)
