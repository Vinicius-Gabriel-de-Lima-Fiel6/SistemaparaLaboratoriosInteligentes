import streamlit as st
from supabase import create_client

# Inicializa conexão
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    st.title("⚙️ Configurações e Gestão de Equipe")
    
    # Pegamos os dados da sessão (definidos no login)
    org_id = st.session_state.user_data.get('org_id')
    
    aba_equipe, aba_perfil = st.tabs(["👥 Membros e Permissões", "🏢 Dados da Empresa"])

    with aba_equipe:
        st.subheader("Gerenciar Colaboradores")
        
        # Form para o ADM convidar/cadastrar funcionário
        with st.expander("➕ Adicionar Novo Membro"):
            with st.form("form_add_user", clear_on_submit=True):
                c1, c2 = st.columns(2)
                novo_nome = c1.text_input("Nome Completo")
                novo_email = c2.text_input("E-mail de Acesso")
                novo_cargo = st.selectbox("Nível de Permissão", ["Visualizador", "Tecnico", "ADM"])
                nova_senha = st.text_input("Senha Provisória", type="password")
                
                if st.form_submit_button("Confirmar Cadastro"):
                    # Aqui usamos a função de cadastro do auth_db, mas passando o org_id automático
                    from auth_db import cadastrar_usuario
                    sucesso, msg = cadastrar_usuario(novo_nome, novo_email, nova_senha, st.session_state.user_data['org_name'], novo_cargo)
                    if sucesso: st.success("Funcionário cadastrado com sucesso!")
                    else: st.error(msg)

        st.divider()
        
        # Listagem automática de quem trabalha na empresa
        st.write("### Equipe Atual")
        res = supabase.table("users").select("username, email, role").eq("org_id", org_id).execute()
        if res.data:
            st.table(res.data)

    with aba_perfil:
        st.subheader("Dados do Laboratório")
        # Aqui você pode adicionar campos para editar nome da empresa, logo, etc.
        st.info("Funcionalidade de edição de perfil corporativo em desenvolvimento.")
