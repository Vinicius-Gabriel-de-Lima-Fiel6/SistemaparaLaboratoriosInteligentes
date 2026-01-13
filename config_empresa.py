import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db

# Inicializa conexão original
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    # Estilo CSS personalizado para fontes e métricas
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
        .st-emotion-cache-1cvow48 { border-radius: 12px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("⚙️ Painel de Controle")
    
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    # --- ABA: GESTÃO DE EQUIPE ---
    with aba_equipe:
        try:
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)

            if not df.empty:
                # Dashboard de Métricas Moderno
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Membros", len(df))
                c2.metric("Técnicos", len(df[df['role'] == 'Tecnico']))
                c3.metric("ADMs", len(df[df['role'] == 'ADM']))
                c4.metric("Visualizadores", len(df[df['role'] == 'Visualizador']))
                
                st.write("📊 **Distribuição de Cargos**")
                st.bar_chart(df['role'].value_counts(), height=180)

            st.divider()

            with st.expander("➕ **Adicionar Novo Membro à Equipe**"):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    nome_func = c1.text_input("Nome Completo")
                    email_func = c2.text_input("E-mail de Login")
                    senha_func = c1.text_input("Senha Provisória", type="password")
                    cargo_func = c2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                    
                    if st.form_submit_button("🚀 Liberar Acesso", use_container_width=True):
                        if nome_func and email_func and senha_func:
                            sucesso, msg = db.cadastrar_usuario(nome_func, email_func, senha_func, org_name, cargo_func)
                            if sucesso:
                                st.success(f"Acesso liberado para {nome_func}!")
                                st.rerun()
                            else:
                                st.error(msg)

            st.write("### 📋 Equipe Atual")
            if not df.empty:
                for _, func in df.iterrows():
                    with st.container(border=True):
                        col_txt, col_btn = st.columns([4, 1])
                        with col_txt:
                            # Badge de cor para o cargo
                            role_color = "blue" if func['role'] == "Tecnico" else "red" if func['role'] == "ADM" else "gray"
                            st.markdown(f"**{func['username']}** :{role_color}[({func['role']})]")
                            st.caption(f"📧 {func['email']}")
                        
                        if func['email'] != user_data['email']:
                            if col_btn.button("Remover", key=f"del_{func['id']}", type="secondary", use_container_width=True):
                                if db.excluir_usuario_por_id(func['id'])[0]:
                                    st.rerun()
                        else:
                            col_btn.write("✨ (Você)")
        except Exception as e:
            st.error(f"Erro ao carregar equipe: {e}")

    
    with aba_laboratorio:
        st.subheader("🏢 Perfil da Organização")
        
        try:
            # Busca dados detalhados
            org_res = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
            dados = org_res.data
            
    
            col_id, col_plano = st.columns(2)
            
            with col_id:
                with st.container(border=True):
                    st.markdown("### 🆔 Identidade")
                    st.write(f"**Nome do Laboratório:**\n{org_name}")
                    st.write("**ID Único da Empresa:**")
                    st.code(org_id, language="text")
                    st.caption("Utilize este ID para suporte técnico.")

            with col_plano:
                with st.container(border=True):
                    st.markdown("### 💳 Assinatura")
                    status = dados.get('status_assinatura', 'Ativo').upper()
                    st.markdown(f"**Status:** :green[{status} ✅]")
                    
                    plano = dados.get('plano_ativo', 'Trial / Beta')
                    st.markdown(f"**Plano Atual:** `{plano}`")
                    
                    metodo = dados.get('metodo_pagto', 'Não informado')
                    st.write(f"**Pagamento via:** {metodo}")
                    
                    if st.button("Gerenciar Assinatura", use_container_width=True):
                        st.info("Redirecionando para o portal financeiro...")

            st.divider()
            
      
            with st.container(border=True):
                st.markdown("### 🔒 Segurança e Dados")
                st.write("Os dados deste laboratório estão criptografados e seguem as normas da LGPD.")
                col_btn1, col_btn2 = st.columns(2)
                col_btn1.button("Exportar Backup dos Dados", use_container_width=True, disabled=True)
                col_btn2.button("Editar Informações Públicas", use_container_width=True)

        except Exception as e:
        
            st.warning("Não foi possível carregar os detalhes da assinatura.")
            with st.container(border=True):
                st.write(f"**Laboratório:** {org_name}")
                st.write(f"**ID:** `{org_id}`")
