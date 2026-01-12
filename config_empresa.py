import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db

# Inicializa conexão
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    st.markdown("## ⚙️ Painel Administrativo")
    
    # Recupera dados da empresa do usuário logado
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    # --- ABA 1: GESTÃO DE EQUIPE ---
    with aba_equipe:
        st.subheader(f"Membros do {org_name}")
        
        # 1. Formulário de Cadastro (Melhorado)
        with st.expander("➕ Adicionar Novo Funcionário"):
            with st.form("cadastrar_interno", clear_on_submit=True):
                col1, col2 = st.columns(2)
                nome_func = col1.text_input("Nome Completo")
                email_func = col2.text_input("E-mail de Login")
                senha_func = col1.text_input("Senha Provisória", type="password")
                cargo_func = col2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                
                if st.form_submit_button("Liberar Acesso"):
                    if nome_func and email_func and senha_func:
                        sucesso, msg = db.cadastrar_usuario(
                            nome_func, email_func, senha_func, org_name, cargo_func
                        )
                        if sucesso:
                            st.success(f"✅ Acesso liberado para {nome_func}!")
                            st.rerun()
                        else:
                            st.error(msg)

        st.divider()
        
        # 2. Lista de Equipe com Ações (Cards em vez de Tabela simples)
        st.write("### Equipe Ativa")
        try:
            usuarios = supabase.table("users").select("*").eq("org_id", org_id).execute()
            
            if usuarios.data:
                for func in usuarios.data:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        c1.write(f"**{func['username']}**")
                        c1.caption(f"📧 {func['email']}")
                        c2.write(f"🏷️ `{func['role']}`")
                        
                        # Botão de remover (Evita que o ADM se exclua)
                        if func['email'] != user_data['email']:
                            if c3.button("Remover", key=f"del_{func['email']}", type="secondary"):
                                supabase.table("users").delete().eq("email", func['email']).execute()
                                st.toast(f"Membro {func['username']} removido.")
                                st.rerun()
                        else:
                            c3.write("✨ (Você)")
            else:
                st.info("Nenhum membro cadastrado além de você.")
        except Exception as e:
            st.error("Erro ao carregar lista de membros.")

    # --- ABA 2: DADOS DA EMPRESA (RECHEADA) ---
    with aba_laboratorio:
        st.subheader("Configurações do Laboratório")
        
        # Busca dados atualizados da organização
        try:
            org_info = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
            dados = org_info.data

            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Razão Social:** {dados['name']}")
                st.write(f"**ID da Organização:**")
                st.code(org_id)
            
            with col_b:
                # Exibindo dados do Plano (Hotmart Style)
                status = dados.get('status_assinatura', 'Ativo').upper()
                st.success(f"**Status da Assinatura:** {status} ✅")
                st.write(f"**Plano:** {dados.get('plano_ativo', 'Personalizado')}")
                st.write(f"**Método de Cobrança:** {dados.get('metodo_pagto', 'N/A')}")

            st.divider()
            
            # Espaço para edição
            with st.expander("📝 Editar Informações Gerais"):
                with st.form("edit_org"):
                    novo_nome = st.text_input("Alterar Nome Fantasia", value=dados['name'])
                    if st.form_submit_button("Salvar Alterações"):
                        supabase.table("organizations").update({"name": novo_nome}).eq("id", org_id).execute()
                        st.success("Dados atualizados! Reinicie para ver as mudanças.")
                        
        except Exception as e:
            st.error("Não foi possível carregar os detalhes da empresa.")
