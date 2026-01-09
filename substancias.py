import streamlit as st
import pandas as pd
from supabase import create_client

# Conexão com o Banco de Dados na Nuvem
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_substances():
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    # Recupera os dados da empresa logada
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. CADASTRO DE SUBSTÂNCIAS ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        
        # Bloqueia cadastro para quem é apenas Visualizador
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
                            "org_name": org_usuario  # Identificador da empresa
                        }
                        supabase.table("substancias").insert(data_insert).execute()
                        st.success(f"'{nome}' cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("Preencha ao menos Nome e Quantidade.")

    st.divider()

    # --- 2. EXIBIÇÃO DO INVENTÁRIO (Sincronizado com o Estoque) ---
    st.subheader(f"📋 Inventário: {org_usuario}")
    
    try:
        # Busca apenas as substâncias da empresa logada
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            # Reorganizando as colunas para ficar visualmente melhor
            cols_ordem = ['id', 'nome', 'quantidade', 'concentracao', 'validade', 'finalidade']
            df = df[cols_ordem]
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # --- 3. EXCLUSÃO DE ITENS ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover Substância"):
                    st.write("Selecione o item para exclusão permanente:")
                    id_del = st.selectbox("ID para remover", options=df['id'].tolist())
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        supabase.table("substancias").delete().eq("id", id_del).execute()
                        st.warning(f"Item ID {id_del} foi removido do banco de dados.")
                        st.rerun()
        else:
            st.info(f"Nenhuma substância cadastrada para a empresa {org_usuario}.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
