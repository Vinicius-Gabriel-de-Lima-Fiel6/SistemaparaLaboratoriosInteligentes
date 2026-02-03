import streamlit as st
import base64

def convert_image_to_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        return f"data:image/png;base64,{base64_str}"
    return None

def show_perfil():
    from __main__ import supabase # Usa a conexão já aberta no app.py
    user = st.session_state.user_data
    
    st.header("👤 Perfil do Usuário")
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            # Puxa a foto da nova coluna 'avatar_url' ou usa default
            foto_atual = user.get('avatar_url') if user.get('avatar_url') else f"https://api.dicebear.com/7.x/avataaars/svg?seed={user['username']}"
            st.image(foto_atual, width=180)
            
            uploaded_file = st.file_uploader("Alterar foto de perfil", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                base64_img = convert_image_to_base64(uploaded_file)
                try:
                    supabase.table("users").update({"avatar_url": base64_img}).eq("id", user['id']).execute()
                    st.session_state.user_data['avatar_url'] = base64_img
                    st.success("Foto atualizada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        
        with col2:
            st.subheader(f"Dados de {user['username']}")
            st.write(f"**E-mail:** {user.get('email')}")
            st.write(f"**Organização:** {user.get('org_name')}")
            st.write(f"**Cargo:** {user.get('role')}")
            st.write(f"**WhatsApp:** {user.get('whatsapp', 'Não informado')}")
            st.write(f"**CPF/CNPJ:** {user.get('cpf_cnpj', 'Não informado')}")
