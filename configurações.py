import streamlit as st
import io

def show_configuracoes(supabase, user_data):
    st.subheader("⚙️ Configurações de Perfil e Sistema")
    
    tab1, tab2 = st.tabs(["👤 Meu Perfil", "🖥️ Sistema"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Exibe a foto atual
            foto_atual = user_data.get('avatar_url') if user_data.get('avatar_url') else f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_data['username']}"
            st.image(foto_atual, width=150, caption="Foto Atual")
            
        with col2:
            novo_nome = st.text_input("Nome de Exibição", value=user_data['username'])
            arquivo_foto = st.file_uploader("Upload de nova foto", type=['jpg', 'png', 'jpeg'])
            
            if st.button("Salvar Alterações de Perfil"):
                updates = {"username": novo_nome}
                
                # Lógica de Upload para Supabase Storage (se houver arquivo)
                if arquivo_foto:
                    file_extension = arquivo_foto.name.split('.')[-1]
                    file_path = f"avatars/{user_data['id']}.{file_extension}"
                    
                    # Upload do arquivo
                    supabase.storage.from_('labsmart_assets').upload(
                        file_path, arquivo_foto.getvalue(), 
                        {"content-type": f"image/{file_extension}", "upsert": "true"}
                    )
                    
                    # Gera URL pública
                    url_publica = supabase.storage.from_('labsmart_assets').get_public_url(file_path)
                    updates["avatar_url"] = url_publica
                
                # Atualiza tabela de usuários
                try:
                    supabase.table("usuarios").update(updates).eq("id", user_data['id']).execute()
                    st.session_state.user_data.update(updates) # Atualiza sessão local
                    st.success("Perfil atualizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    with tab2:
        st.write("### Preferências da Organização")
        st.info(f"Conectado a: {user_data.get('org_name')}")
        st.checkbox("Habilitar Logs de Auditoria em Tempo Real", value=True)
        st.checkbox("Alertas de Validade de Reagentes (E-mail)", value=True)
        st.selectbox("Fuso Horário do Sistema", ["UTC-3 (Brasília)", "UTC-4 (Manaus)", "UTC+0"])
