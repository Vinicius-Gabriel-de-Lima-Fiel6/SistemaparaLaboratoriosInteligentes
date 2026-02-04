import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# Configuração Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def render_projetos():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    st.title("📂 Gestão de Projetos")

    # --- 1. CADASTRO ---
    with st.container(border=True):
        st.subheader("Abrir Novo Projeto")
        if role_usuario == "Visualizador":
            st.warning("Permissão negada para criação.")
        else:
            c1, c2 = st.columns(2)
            nome_proj = c1.text_input("Nome do Projeto/Pesquisa")
            responsavel = c2.text_input("Pesquisador Responsável")
            
            c3, c4 = st.columns(2)
            status = c3.selectbox("Status Inicial", ["Ativo", "Pausado", "Concluído"])
            prioridade = c4.selectbox("Prioridade", ["Baixa", "Média", "Alta"])
            
            objetivo = st.text_area("Objetivo do Projeto")
            data_inicio = st.date_input("Data de Início", value=date.today())
            
            if st.button("🚀 Criar Projeto", use_container_width=True):
                if nome_proj and responsavel:
                    try:
                        supabase.table("projetos").insert({
                            "nome": nome_proj, 
                            "responsavel": responsavel, 
                            "status": status, 
                            "org_name": org_usuario,
                            "data_inicio": str(data_inicio),
                            "prioridade": prioridade,
                            "objetivo": objetivo
                        }).execute()
                        st.success("Projeto iniciado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao inserir no banco: {e}")
                else:
                    st.error("Por favor, preencha o nome e o responsável.")

    st.divider()

    # --- 2. LISTAGEM E AÇÕES ---
    try:
        # Busca os dados filtrando pela organização
        res = supabase.table("projetos").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.subheader("📋 Projetos da Organização")
            
            # Formatação para exibição
            display_df = df[['id', 'nome', 'responsavel', 'status', 'prioridade', 'data_inicio']].copy()
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            if role_usuario in ["ADM", "Tecnico"]:
                col_edit, col_del = st.columns(2)

                with col_edit:
                    with st.expander("🔄 Atualizar Projeto"):
                        # Usamos o ID (UUID) como referência
                        id_edit = st.selectbox("Selecionar Projeto para editar", options=df['id'].tolist(), 
                                             format_func=lambda x: df[df['id']==x]['nome'].values[0])
                        
                        novo_nome = st.text_input("Novo Nome (deixe vazio para manter)")
                        novo_status = st.selectbox("Mudar Status", ["Ativo", "Pausado", "Concluído", "Arquivado"])
                        nova_prioridade = st.selectbox("Mudar Prioridade", ["Baixa", "Média", "Alta"])

                        if st.button("Salvar Alterações", use_container_width=True):
                            upd_data = {
                                "status": novo_status,
                                "prioridade": nova_prioridade
                            }
                            if novo_nome: 
                                upd_data["nome"] = novo_nome
                            
                            supabase.table("projetos").update(upd_data).eq("id", id_edit).execute()
                            st.success("Projeto atualizado!")
                            st.rerun()

                with col_del:
                    with st.expander("🗑️ Excluir Projeto"):
                        id_del = st.selectbox("Selecionar Projeto para excluir", options=df['id'].tolist(),
                                            format_func=lambda x: df[df['id']==x]['nome'].values[0])
                        st.warning("Atenção: Esta ação não pode ser desfeita.")
                        if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                            supabase.table("projetos").delete().eq("id", id_del).execute()
                            st.success("Projeto removido.")
                            st.rerun()
        else:
            st.info("Nenhum projeto registrado para esta organização.")
            
    except Exception as e:
        st.error(f"Erro crítico ao carregar interface: {e}")
