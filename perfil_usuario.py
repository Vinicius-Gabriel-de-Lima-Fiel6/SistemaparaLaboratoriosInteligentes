import streamlit as st
import auth_db as db  # Importando seu módulo de banco

def show_perfil():
    st.header("👤 Perfil do Usuário")
    
    user = st.session_state.user_data
    
    # Criamos um container para o "Cartão de Identidade"
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Lógica da Foto: Se houver foto no state, usa ela. Senão, usa o Dicebear.
            foto_atual = st.session_state.get('custom_avatar', f"https://api.dicebear.com/7.x/avataaars/svg?seed={user['username']}")
            st.image(foto_atual, width=150)
            
            uploaded_file = st.file_uploader("Alterar foto", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
            if uploaded_file:
                st.session_state.custom_avatar = uploaded_file
                st.toast("Foto carregada com sucesso!")
                st.rerun()

        with col2:
            st.subheader(user['username'])
            st.write(f"**Organização:** {user.get('org_name', 'Não definida')}")
            st.write(f"**Cargo:** {user.get('role', 'Visualizador')}")
            st.write(f"**E-mail:** {user.get('email', 'N/A')}")

    # Outras funcionalidades: Troca de Senha
    st.divider()
    st.subheader("Segurança")
    with st.expander("Alterar Senha de Acesso"):
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar = st.text_input("Confirmar Nova Senha", type="password")
        if st.button("Atualizar Senha"):
            if nova_senha == confirmar and len(nova_senha) > 5:
                # Aqui você chamaria uma função do seu auth_db para dar update
                st.success("Senha atualizada com sucesso!")
            else:
                st.error("As senhas não coincidem ou são muito curtas.")
