import streamlit as st
import base64
from PIL import Image
import io

def convert_image_to_base64(uploaded_file):
    """Converte o arquivo carregado em string Base64 para salvar no banco."""
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        return f"data:image/png;base64,{base64_str}"
    return None

def show_perfil():
    st.header("👤 Perfil do Usuário")
    
    # Busca dados atualizados da sessão
    user = st.session_state.user_data
    supabase = st.connection("supabase") if "supabase" in st.secrets else None 
    # Nota: Usei a conexão padrão, mas no seu app usamos o objeto 'supabase' global do app.py
    # Para garantir, vamos usar o objeto do estado se necessário ou passar como parâmetro.
    from __main__ import supabase 

    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Prioridade de exibição: 1. Foto do banco | 2. Avatar Temporário | 3. Default
            foto_no_banco = user.get('avatar_url')
            foto_exibicao = foto_no_banco if foto_no_banco else f"https://api.dicebear.com/7.x/avataaars/svg?seed={user['username']}"
            
            st.image(foto_exibicao, width=150)
            
            uploaded_file = st.file_uploader("Trocar foto", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
            
            if uploaded_file:
                with st.spinner("Processando imagem..."):
                    base64_image = convert_image_to_base64(uploaded_file)
                    
                    # Atualiza no Supabase
                    try:
                        res = supabase.table("users").update({"avatar_url": base64_image}).eq("id", user['id']).execute()
                        
                        # Atualiza a sessão local para refletir a mudança imediatamente
                        st.session_state.user_data['avatar_url'] = base64_image
                        st.success("Imagem salva no banco de dados!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")

        with col2:
            st.subheader(f"Olá, {user['username']}!")
            st.info(f"📍 **Organização:** {user.get('org_name', 'N/A')}")
            st.write(f"📧 **E-mail:** {user.get('email', 'N/A')}")
            st.write(f"🛡️ **Nível de Acesso:** {user.get('role', 'Visualizador')}")
            st.write(f"📱 **WhatsApp:** {user.get('whatsapp', 'Não informado')}")

    st.divider()
    st.subheader("Segurança da Conta")
    with st.expander("Alterar Senha"):
        st.info("Funcionalidade em desenvolvimento. Conecte ao seu auth_db.")
