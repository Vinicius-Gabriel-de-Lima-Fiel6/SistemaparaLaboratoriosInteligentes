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

# --- Funções de Segurança ---
def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

# --- Funções de Negócio ---

def cadastrar_usuario(username, email, senha_limpa, org_name, role):
    """
    Cria um usuário e, se for ADM, cria também a Organização no banco de dados.
    """
    global supabase
    if supabase is None: return False, "Erro de conexão."
    
    try:
        senha_protegida = hash_senha(senha_limpa)
        org_id = None

        # 1. LÓGICA DE ORGANIZAÇÃO
        if role == "ADM":
            org_payload = {"name": org_name}
            res_org = supabase.table("organizations").insert(org_payload).execute()
            
            if res_org.data:
                org_id = res_org.data[0]['id'] 
            else:
                return False, "Erro ao criar a organização no banco."
        else:
            if 'user_data' in st.session_state:
                org_id = st.session_state.user_data.get('org_id')
            
            if not org_id:
                return False, "Erro: Não foi possível vincular o funcionário a uma empresa."

        # 2. LÓGICA DE USUÁRIO
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
            return False, "Este e-mail já está cadastrado no sistema."
        return False, f"Erro ao cadastrar: {str(e)}"

def buscar_usuario_por_email(email):
    global supabase
    if supabase is None: return None
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if len(response.data) > 0:
            return response.data[0] 
        return None
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return None

def redefinir_senha(email, nova_senha):
    global supabase
    try:
        senha_protegida = hash_senha(nova_senha)
        supabase.table("users").update({"password_hash": senha_protegida}).eq("email", email).execute()
        return True, "Senha redefinida com sucesso!"
    except Exception as e:
        return False, f"Erro ao redefinir: {e}"
