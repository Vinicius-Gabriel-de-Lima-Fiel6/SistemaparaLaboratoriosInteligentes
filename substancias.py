import streamlit as st
import pandas as pd
from supabase import create_client

# Conexão com o Banco de Dados na Nuvem
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_substances():
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    # Recupera os dados críticos da sessão
    user_data = st.session_state.get('user_data', {})
    org_id = user_data.get('org_id')      # O "ID Único" para o banco de dados
    org_name = user_data.get('org_name')  # O "Nome" para a interface
    role_usuario = user_data.get('role', 'Visualizador')

    # Segurança extra: Se não houver org_id, interrompe o carregamento
    if not org_id:
        st.error("Erro de autenticação: Organização não identificada. Faça login novamente.")
        return

    # --- 1. CADASTRO DE SUBSTÂNCIAS ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        
        if role_usuario == "Visualizador":
            st.warning("Seu perfil é apenas para visualização. Contate o ADM para alterações.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substância")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentração")
                quantidade = st.number_input("Quantidade", min_value=0.0)
            with col3:
                validade = st.text_input("Validade (MM/AAAA)")
                
            if st.button("➕ Adicionar Substância", use_container_width=True):
                if nome and quantidade:
                    with st.spinner("Enviando para o banco de dados..."):
                        data_insert = {
                            "nome": nome,
                            "finalidade": finalidade,
                            "concentracao": concentracao,
                            "quantidade": quantidade,
                            "validade": validade,
                            "org_id": org_id,      # CARIMBO: Vínculo real no banco
                            "org_name": org_name   # Opcional: mantém o nome para referência rápida
                        }
                        supabase.table("substancias").insert(data_insert).execute()
                        st.success(f"'{nome}' cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("Preencha ao menos Nome e Quantidade.")

    st.divider()

    # --- 2. EXIBIÇÃO DO INVENTÁRIO (Filtrado por org_id) ---
    st.subheader(f"📋 Inventário: {org_name}")
    
    try:
        # BUSCA SEGURA: Filtramos apenas o que pertence ao org_id da empresa logada
        response = supabase.table("substancias").select("*").eq("org_id", org_id).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            # Reorganizando colunas (certificando-se de que existem no DF)
            cols_disponiveis = [c for c in ['id', 'nome', 'quantidade', 'concentracao', 'validade', 'finalidade'] if c in df.columns]
            df_display = df[cols_disponiveis]
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # --- 3. EXCLUSÃO DE ITENS ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover Substância"):
                    st.write("Selecione o item para exclusão permanente:")
                    # Aqui usamos o ID do DataFrame filtrado
                    id_del = st.selectbox("ID para remover", options=df['id'].tolist())
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        # Além de filtrar pelo ID, filtramos pelo org_id por segurança extra (Double Check)
                        supabase.table("substancias").delete().eq("id", id_del).eq("org_id", org_id).execute()
                        st.warning(f"Item ID {id_del} foi removido.")
                        st.rerun()
        else:
            st.info(f"Nenhum item encontrado no inventário de {org_name}.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
