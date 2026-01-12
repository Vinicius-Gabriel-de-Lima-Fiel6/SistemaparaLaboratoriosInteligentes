import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db

# Inicializa conexão original
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    # Estilo CSS para melhorar a aparência dos containers
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; color: #1f77b4; }
        .st-emotion-cache-1cvow48 { border-radius: 10px; border: 1px solid #f0f2f6; padding: 15px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("⚙️ Configurações Administrativas")
    
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    with aba_equipe:
        # --- CABEÇALHO COM DASHBOARD ---
        try:
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)

            if not df.empty:
                # Dashboard mais limpo
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    st.metric("Total Membros", len(df), delta="Equipe Ativa", delta_color="normal")
                with c2:
                    tecnicos = len(df[df['role'] == 'Tecnico'])
                    st.metric("Técnicos", tecnicos, help="Membros com acesso operacional")
                with c3:
                    # Gráfico menor e mais elegante
                    st.write("📊 **Distribuição de Acessos**")
                    st.bar_chart(df['role'].value_counts(), height=150)

            st.divider()

            # --- FORMULÁRIO DE CADASTRO EM UM EXPANDER MODERNO ---
            with st.expander("✨ **Cadastrar Novo Membro**", expanded=False):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    c_nome, c_email = st.columns(2)
                    nome_func = c_nome.text_input("Nome Completo", placeholder="Ex: João Silva")
                    email_func = c_email.text_input("E-mail Corporativo", placeholder="joao@empresa.com")
                    
                    c_senha, c_cargo = st.columns(2)
                    senha_func = c_senha.text_input("Senha Inicial", type="password")
                    cargo_func = c_cargo.selectbox("Nível de Permissão", ["Visualizador", "Tecnico", "ADM"])
                    
                    submit = st.form_submit_button("🚀 Finalizar Cadastro", use_container_width=True)
                    if submit:
                        if nome_func and email_func and senha_func:
                            sucesso, msg = db.cadastrar_usuario(nome_func, email_func, senha_func, org_name, cargo_func)
                            if sucesso:
                                st.success("✅ Funcionário cadastrado com sucesso!")
                                st.rerun()
                            else:
                                st.error(msg)

            # --- LISTA DE MEMBROS ESTILIZADA ---
            st.write("### 📋 Listagem de Equipe")
            if not df.empty:
                for _, func in df.iterrows():
                    # Lógica de ícones por cargo
                    icon = "⚡" if func['role'] == "Tecnico" else "🔐" if func['role'] == "ADM" else "👁️"
                    
                    with st.container(border=True):
                        col_avatar, col_txt, col_btn = st.columns([0.5, 3, 1])
                        
                        col_avatar.markdown(f"<h1 style='text-align: center; margin:0;'>{icon}</h1>", unsafe_allow_html=True)
                        
                        with col_txt:
                            st.markdown(f"**{func['username']}**")
                            st.caption(f"📧 {func['email']} | Cargo: {func['role']}")
                        
                        if func['email'] != user_data['email']:
                            if col_btn.button("Remover", key=f"del_{func['id']}", use_container_width=True, type="secondary"):
                                if db.excluir_usuario_por_id(func['id'])[0]:
                                    st.toast(f"Membro {func['username']} removido!")
                                    st.rerun()
                        else:
                            col_btn.info("Você")

        except Exception as e:
            st.error(f"Erro ao carregar dashboard: {e}")

    with aba_laboratorio:
        # --- ABA EMPRESA COM VISUAL DE CARTÃO ---
        st.subheader("🏢 Dados da Organização")
        
        try:
            org_res = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
            dados = org_res.data
            
            # Layout em cards informativos
            c_info, c_status = st.columns(2)
            
            with c_info:
                with st.container(border=True):
                    st.write("📌 **Informações de Registro**")
                    st.write(f"**Razão Social:** {org_name}")
                    st.write(f"**ID Unificado:**")
                    st.code(org_id, language="text")
            
            with c_status:
                with st.container(border=True):
                    st.write("💳 **Plano e Faturamento**")
                    plano = dados.get('plano_ativo', 'Trial')
                    st.markdown(f"**Plano:** `:blue[{plano}]`")
                    st.markdown(f"**Status:** `:green[Ativo]`")
                    st.caption(f"Cobrança via: {dados.get('metodo_pagto', 'Padrão')}")
            
            st.divider()
            st.warning("⚠️ **Nota:** Para alterar dados de faturamento, entre em contato com o suporte.")

        except Exception as e:
            st.info("Informações detalhadas da organização ainda não disponíveis.")
