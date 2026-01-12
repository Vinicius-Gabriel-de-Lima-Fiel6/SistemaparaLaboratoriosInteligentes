import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db

# Inicializa conexão original
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    st.title("⚙️ Painel Administrativo")
    
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    with aba_equipe:
        st.subheader(f"Dashboard de Equipe - {org_name}")
        
        try:
            # Busca todos os funcionários da empresa
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)

            if not df.empty:
                # --- MÉTRICAS (Resumo da Equipe) ---
                total_membros = len(df)
                tecnicos = len(df[df['role'] == 'Tecnico'])
                adms = len(df[df['role'] == 'ADM'])
                visualizadores = len(df[df['role'] == 'Visualizador'])

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Total Membros", total_membros)
                col_m2.metric("Técnicos", tecnicos)
                col_m3.metric("Administradores", adms)
                col_m4.metric("Visualizadores", visualizadores)

                # --- GRÁFICO DE DISTRIBUIÇÃO ---
                st.write("#### Distribuição de Cargos")
                chart_data = df['role'].value_counts()
                st.bar_chart(chart_data)

            st.divider()

            # --- FORMULÁRIO DE CADASTRO ---
            with st.expander("➕ Adicionar Novo Funcionário"):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    nome_func = col1.text_input("Nome Completo")
                    email_func = col2.text_input("E-mail de Login")
                    senha_func = col1.text_input("Senha Provisória", type="password")
                    cargo_func = col2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                    
                    if st.form_submit_button("Liberar Acesso"):
                        if nome_func and email_func and senha_func:
                            sucesso, msg = db.cadastrar_usuario(nome_func, email_func, senha_func, org_name, cargo_func)
                            if sucesso:
                                st.success(f"Acesso liberado!")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Preencha todos os campos.")

            st.divider()
            
            # --- LISTA DE MEMBROS COM BOTÃO EXCLUIR ---
            st.write("### Equipe Ativa")
            if not df.empty:
                for index, func in df.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        c1.write(f"**{func['username']}**")
                        c1.caption(f"E-mail: {func['email']}")
                        c2.write(f"Cargo: `{func['role']}`")
                        
                        if func['email'] != user_data['email']:
                            if c3.button("Remover", key=f"del_{func['id']}", type="secondary"):
                                sucesso, msg = db.excluir_usuario_por_id(func['id'])
                                if sucesso:
                                    st.toast(msg)
                                    st.rerun()
                        else:
                            c3.write("✨ (Você)")
            else:
                st.info("Nenhum membro encontrado.")

        except Exception as e:
            st.error(f"Erro ao carregar dashboard: {e}")

    with aba_laboratorio:
        st.subheader("🏢 Informações do Laboratório")
        try:
            org_res = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
            dados_org = org_res.data
            
            col_inf1, col_inf2 = st.columns(2)
            with col_inf1:
                st.write(f"**Nome Registrado:** {org_name}")
                st.write(f"**ID da Organização:**")
                st.code(org_id)
            
            with col_inf2:
                st.success(f"**Status da Assinatura:** {dados_org.get('status_assinatura', 'Ativo')} ✅")
                st.write(f"**Plano:** {dados_org.get('plano_ativo', 'Mensal')}")
                st.write(f"**Método de Cobrança:** {dados_org.get('metodo_pagto', 'Cartão')}")
        except:
            st.write(f"**ID:** `{org_id}`")
            st.write(f"**Nome:** {org_name}")
