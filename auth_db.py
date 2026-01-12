import streamlit as st
from supabase import create_client, Client
import bcrypt

# --- Inicialização ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    supabase = None

# --- Segurança ---
def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

# --- Funções de Usuário ---
def cadastrar_usuario(username, email, senha_limpa, org_name, role, org_id_manual=None):
    """
    Cadastra um usuário garantindo o vínculo com a empresa.
    """
    global supabase
    if supabase is None: return False, "Sem conexão com o banco."
    
    try:
        senha_protegida = hash_senha(senha_limpa)
        
        # Resolve o org_id: prioriza o manual (usado na gestão de equipe)
        # Se não houver, tenta buscar na sessão (usado no cadastro inicial)
        org_id = org_id_manual if org_id_manual else st.session_state.user_data.get('org_id')

        # Se ainda for nulo e não for um novo ADM criando empresa, barra o cadastro
        if not org_id and role != "ADM":
            return False, "Erro: Não foi possível vincular o funcionário a uma empresa."

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
        if "duplicate key" in str(e).lower():
            return False, "Este e-mail já está em uso."
        return False, f"Erro: {str(e)}"

def excluir_usuario(user_id):
    """Remove um membro da equipe."""
    try:
        supabase.table("users").delete().eq("id", user_id).execute()
        return True, "Membro removido."
    except Exception as e:
        return False, str(e)
