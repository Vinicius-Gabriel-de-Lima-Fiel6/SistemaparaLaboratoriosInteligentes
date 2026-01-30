import streamlit as st
import pandas as pd
from supabase import create_client

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
            st.warning("Permissão negada.")
        else:
            c1, c2 = st.columns(2)
            nome_proj = c1.text_input("Nome do Projeto/Pesquisa")
            responsavel = c2.text_input("Pesquisador Responsável")
            status = st.selectbox("Status Inicial", ["Ativo", "Pausado", "Concluído"])
            
            if st.button("🚀 Criar Projeto", use_container_width=True):
                if nome_proj:
                    supabase.table("projetos").insert({
                        "nome": nome_proj, "responsavel": responsavel, 
                        "status": status, "org_name": org_usuario
                    }).execute()
                    st.success("Projeto iniciado!")
                    st.rerun()

    st.divider()

    # --- 2. LISTAGEM E AÇÕES ---
    try:
        res = supabase.table("projetos").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.subheader("📋 Projetos da Organização")
            st.dataframe(df[['id', 'nome', 'responsavel', 'status', 'created_at']], use_container_width=True, hide_index=True)

            if role_usuario in ["ADM", "Tecnico"]:
                col_edit, col_del = st.columns(2)

                with col_edit:
                    with st.expander("🔄 Atualizar Status/Nome"):
                        id_edit = st.selectbox("ID do Projeto", options=df['id'].tolist(), key="ed_proj")
                        novo_nome = st.text_input("Mudar Nome", key="new_n_proj")
                        novo_status = st.selectbox("Mudar Status", ["Ativo", "Pausado", "Concluído", "Arquivado"], key="new_st_proj")
                        if st.button("Salvar Alterações", use_container_width=True):
                            upd_data = {"status": novo_status}
                            if novo_nome: upd_data["nome"] = novo_nome
                            supabase.table("projetos").update(upd_data).eq("id", id_edit).execute()
                            st.rerun()

                with col_del:
                    with st.expander("🗑️ Encerrar/Excluir Projeto"):
                        id_del = st.selectbox("ID para excluir", options=df['id'].tolist(), key="del_proj")
                        st.warning("CUIDADO: Isso pode afetar os relatórios vinculados.")
                        if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                            supabase.table("projetos").delete().eq("id", id_del).execute()
                            st.rerun()
        else:
            st.info("Nenhum projeto registrado.")
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {e}")
