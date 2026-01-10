import streamlit as st
from supabase import create_client
import auth_db as db

# Inicializa conexão
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    st.title("⚙️ Painel Administrativo")
    
    # Recupera dados da empresa do usuário logado
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    with aba_equipe:
        st.subheader(f"Membros do {org_name}")
        
        # Área para o ADM cadastrar novos funcionários
        with st.expander("➕ Adicionar Novo Funcionário"):
            with st.form("cadastrar_interno", clear_on_submit=True):
                col1, col2 = st.columns(2)
                nome_func = col1.text_input("Nome Completo")
                email_func = col2.text_input("E-mail de Login")
                
                senha_func = col1.text_input("Senha Provisória", type="password")
                cargo_func = col2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                
                if st.form_submit_button("Liberar Acesso"):
                    if nome_func and email_func and senha_func:
                        # Chamamos o cadastro do auth_db passando o org_id da empresa atual
                        sucesso, msg = db.cadastrar_usuario(
                            nome_func, 
                            email_func, 
                            senha_func, 
                            org_name, 
                            cargo_func
                        )
                        if sucesso:
                            st.success(f"Acesso liberado para {nome_func}!")
                        else:
                            st.error(msg)
                    else:
                        st.warning("Preencha todos os campos para o cadastro.")

        st.divider()
        
        # Lista quem trabalha na empresa (Automático)
        st.write("### Equipe Ativa")
        try:
            usuarios = supabase.table("users").select("username, email, role").eq("org_name", org_name).execute()
            if usuarios.data:
                st.table(usuarios.data)
        except Exception as e:
            st.error("Erro ao carregar lista de membros.")

    with aba_laboratorio:
        st.subheader("Configurações do Laboratório")
        st.write(f"**ID da Organização:** `{org_id}`")
        st.write(f"**Nome Registrado:** {org_name}")
        st.info("Aqui você poderá, no futuro, alterar o logo e o plano de assinatura.")
