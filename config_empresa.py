import streamlit as st
import auth_db as db
import pandas as pd

def show_config_empresa():
    st.title("⚙️ Painel Administrativo")
    
    # Dados da sessão
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    # --- ABA: GESTÃO DE EQUIPE ---
    with aba_equipe:
        st.subheader(f"Membros do {org_name}")
        
        # Formulário para adicionar novos membros
        with st.expander("➕ Adicionar Novo Funcionário"):
            with st.form("cadastrar_interno", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nome_func = c1.text_input("Nome Completo")
                email_func = c2.text_input("E-mail de Login")
                senha_func = c1.text_input("Senha Provisória", type="password")
                cargo_func = c2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                
                if st.form_submit_button("Liberar Acesso"):
                    if nome_func and email_func and senha_func:
                        # PASSANDO ORG_ID MANUALMENTE PARA EVITAR O ERRO
                        sucesso, msg = db.cadastrar_usuario(
                            nome_func, email_func, senha_func, 
                            org_name, cargo_func, org_id_manual=org_id
                        )
                        if sucesso:
                            st.success(f"Acesso liberado para {nome_func}!")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Preencha todos os campos.")

        st.divider()
        st.write("### Equipe Ativa")
        
        try:
            # Busca membros da empresa no banco
            res = db.supabase.table("users").select("*").eq("org_id", org_id).execute()
            if res.data:
                for func in res.data:
                    with st.container(border=True):
                        col_info, col_btn = st.columns([4, 1])
                        col_info.write(f"**{func['username']}** ({func['role']})")
                        col_info.caption(f"E-mail: {func['email']}")
                        
                        # Botão de remover (ADM não se exclui)
                        if func['email'] != user_data['email']:
                            if col_btn.button("Remover", key=f"del_{func['id']}", type="secondary"):
                                db.excluir_usuario(func['id'])
                                st.rerun()
                        else:
                            col_btn.write("✨ (Você)")
            else:
                st.info("Apenas você está na equipe no momento.")
        except Exception as e:
            st.error("Erro ao carregar lista de membros.")

    # --- ABA: DADOS DA EMPRESA ---
    with aba_laboratorio:
        st.subheader("Configurações do Laboratório")
        
        # Busca dados da empresa (incluindo assinatura)
        org_res = db.supabase.table("organizations").select("*").eq("id", org_id).single().execute()
        if org_res.data:
            dados = org_res.data
            st.write(f"**Nome Registrado:** {dados['name']}")
            st.write(f"**ID da Organização:** `{org_id}`")
            
            st.divider()
            st.subheader("💳 Assinatura e Plano")
            col_a, col_b = st.columns(2)
            col_a.metric("Plano Atual", dados.get('plano_ativo', 'Trial'))
            col_b.metric("Status", "Ativo ✅")
            st.write(f"**Método de Pagamento:** {dados.get('metodo_pagto', 'Não informado')}")
        else:
            st.error("Dados da empresa não encontrados.")
