import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client

# Configurações do Supabase (buscando as chaves do seu st.secrets)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_estoque():
    st.title("📦 Controle de Estoque e Compras")
    
    # Recupera os dados do usuário logado no app.py
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    try:
        # --- BUSCA DADOS NO SUPABASE FILTRANDO PELA EMPRESA ---
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # --- SEÇÃO DE ALERTAS E MÉTRICAS ---
            col1, col2 = st.columns(2)
            # Verifica se existe a coluna 'quantidade', senão usa 0
            df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
            
            # --- LÓGICA DE CORES (SEMÁFORO) ---
            # Criando a coluna visual baseada na quantidade
            def aplicar_cor(qtd):
                if qtd < 10:
                    return "🔴 CRÍTICO (Repor)"
                elif 10 <= qtd <= 20:
                    return "🟡 ATENÇÃO (Baixo)"
                else:
                    return "🟢 SEGURO (Ok)"
            
            df['Status'] = df['quantidade'].apply(aplicar_cor)

            itens_baixos = df[df['quantidade'] < 10]
            col1.metric("Total no Inventário", len(df))
            col2.metric("Itens para Reposição", len(itens_baixos), delta_color="inverse")

            # --- SEÇÃO DE COMPRAS DIRETAS ---
            if len(itens_baixos) > 0:
                with st.expander("🛒 COMPRA RÁPIDA (Itens com estoque baixo)", expanded=True):
                    st.write("Selecione um item para buscar fornecedores online:")
                    item_para_comprar = st.selectbox("Substância para repor:", itens_baixos['nome'].unique())
                    
                    if item_para_comprar:
                        query = urllib.parse.quote(item_para_comprar)
                        c1, c2, c3 = st.columns(3)
                        c1.link_button("🔍 Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop", use_container_width=True)
                        c2.link_button("🧪 Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}", use_container_width=True)
                        c3.link_button("📦 Amazon", f"https://www.amazon.com.br/s?k={query}", use_container_width=True)

            st.divider()

            # --- TABELA DE EDIÇÃO ---
            st.subheader(f"📝 Inventário: {org_usuario}")
            
            # Bloqueia edição para 'Visualizador'
            is_disabled = (role_usuario == "Visualizador")
            
            # Exibição com configuração de colunas para mostrar o Status
            edited_df = st.data_editor(
                df, 
                use_container_width=True, 
                hide_index=True, 
                disabled=is_disabled,
                # Impede o usuário de mudar o org_name e o Status manualmente
                column_config={
                    "org_name": st.column_config.TextColumn("Empresa", disabled=True),
                    "Status": st.column_config.TextColumn("Status Visual", disabled=True),
                    "id": None  # Oculta o ID para o usuário mas mantém no DataFrame para o update
                }
            )

            # Botão de salvar (Lógica de permissão mantida)
            if role_usuario in ["ADM", "Tecnico"]:
                if st.button("💾 Salvar Alterações no Banco"):
                    with st.spinner("Sincronizando com a nuvem..."):
                        for _, row in edited_df.iterrows():
                            # Faz o update linha por linha no Supabase usando o ID
                            supabase.table("substancias").update({
                                "nome": row['nome'],
                                "quantidade": row['quantidade'],
                                "unidade": row['unidade'] if 'unidade' in row else "un"
                            }).eq("id", row['id']).execute()
                        
                        st.success("Estoque salvo permanentemente na nuvem!")
                        st.rerun()

        else:
            st.warning(f"O inventário da empresa {org_usuario} está vazio.")
            if role_usuario != "Visualizador":
                if st.button("➕ Criar Primeiro Item"):
                    supabase.table("substancias").insert({"nome": "Novo Item", "quantidade": 0, "org_name": org_usuario}).execute()
                    st.rerun()

    except Exception as e:
        st.error(f"Erro de Conexão: {e}")

    # --- BUSCA GERAL ---
    st.divider()
    st.subheader("🌐 Pesquisa Externa")
    busca_livre = st.text_input("Procurar qualquer reagente para compra:")
    if busca_livre:
        q_livre = urllib.parse.quote(busca_livre)
        st.link_button(f"Comprar {busca_livre} agora", f"https://www.google.com/search?q=comprar+{q_livre}")
