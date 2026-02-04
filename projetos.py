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
            nome_proj = c1.text_input("Nome do Projeto/Pesquisa", key="input_nome_proj")
            responsavel = c2.text_input("Pesquisador Responsável", key="input_resp_proj")
            
            c3, c4 = st.columns(2)
            status = c3.selectbox("Status Inicial", ["Ativo", "Pausado", "Concluído"], key="select_status_ini")
            prioridade = c4.selectbox("Prioridade", ["Baixa", "Média", "Alta"], key="select_prio_ini")
            
            objetivo = st.text_area("Objetivo do Projeto", key="area_obj_proj")
            data_inicio = st.date_input("Data de Início", value=date.today(), key="date_proj")
            
            # KEY ADICIONADA AQUI
            if st.button("🚀 Criar Projeto", use_container_width=True, key="btn_criar_projeto"):
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
        res = supabase.table("projetos").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.subheader("📋 Projetos da Organização")
            display_df = df[['id', 'nome', 'responsavel', 'status', 'prioridade', 'data_inicio']].copy()
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            if role_usuario in ["ADM", "Tecnico"]:
                col_edit, col_del = st.columns(2)

                with col_edit:
                    with st.expander("🔄 Atualizar Projeto"):
                        id_edit = st.selectbox("Selecionar Projeto para editar", options=df['id'].tolist(), 
                                             format_func=lambda x: df[df['id']==x]['nome'].values[0],
                                             key="select_edit_id")
                        
                        novo_nome = st.text_input("Novo Nome (deixe vazio para manter)", key="edit_nome_input")
                        novo_status = st.selectbox("Mudar Status", ["Ativo", "Pausado", "Concluído", "Arquivado"], key="edit_status_select")
                        nova_prioridade = st.selectbox("Mudar Prioridade", ["Baixa", "Média", "Alta"], key="edit_prio_select")

                        # KEY ADICIONADA AQUI
                        if st.button("Salvar Alterações", use_container_width=True, key="btn_save_changes"):
                            upd_data = {"status": novo_status, "prioridade": nova_prioridade}
                            if novo_nome: upd_data["nome"] = novo_nome
                            
                            supabase.table("projetos").update(upd_data).eq("id", id_edit).execute()
                            st.success("Projeto atualizado!")
                            st.rerun()

                with col_del:
                    with st.expander("🗑️ Excluir Projeto"):
                        id_del = st.selectbox("Selecionar Projeto para excluir", options=df['id'].tolist(),
                                            format_func=lambda x: df[df['id']==x]['nome'].values[0],
                                            key="select_del_id")
                        st.warning("Atenção: Esta ação não pode ser desfeita.")
                        
                        # KEY ADICIONADA AQUI
                        if st.button("Confirmar Exclusão", type="primary", use_container_width=True, key="btn_confirm_del"):
                            supabase.table("projetos").delete().eq("id", id_del).execute()
                            st.success("Projeto removido.")
                            st.rerun()
        else:
            st.info("Nenhum projeto registrado para esta organização.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
