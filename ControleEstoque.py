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
    # Acréscimo para o Log:
    username_atual = user_data.get('username', 'Usuário')

    try:
        # --- BUSCA DADOS NO SUPABASE FILTRANDO PELA EMPRESA ---
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # --- CRIAÇÃO DAS SUB-ABAS (ACRÉSCIMO SEM ALTERAR O RESTO) ---
            tab_principal, tab_logs, tab_manutencao = st.tabs(["📋 Inventário e Compras", "📜 Histórico de Logs", "🛠️ Equipamentos"])

            with tab_principal:
                # --- SEÇÃO DE ALERTAS E MÉTRICAS (SUA LÓGICA ORIGINAL) ---
                col1, col2 = st.columns(2)
                df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
                
                itens_baixos = df[df['quantidade'] < 10]
                col1.metric("Total no Inventário", len(df))
                col2.metric("Itens para Reposição", len(itens_baixos), delta_color="inverse")

                # --- SEÇÃO DE COMPRAS DIRETAS (SUA LÓGICA ORIGINAL) ---
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

                # --- TABELA DE EDIÇÃO (SUA LÓGICA ORIGINAL COM ACRÉSCIMO DE STATUS VISUAL) ---
                st.subheader(f"📝 Inventário: {org_usuario}")
                
                is_disabled = (role_usuario == "Visualizador")
                
                # Acréscimo de coluna de Status Visual no DataFrame
                df['Status'] = df['quantidade'].apply(lambda x: "🔴 ESGOTADO" if x <= 0 else ("🟡 BAIXO" if x < 10 else "🟢 OK"))

                edited_df = st.data_editor(
                    df, 
                    use_container_width=True, 
                    hide_index=True, 
                    disabled=is_disabled,
                    column_config={
                        "org_name": st.column_config.TextColumn("Empresa", disabled=True),
                        "Status": st.column_config.TextColumn("Status", disabled=True)
                    },
                    column_order=("Status", "nome", "quantidade", "unidade", "org_name")
                )

                # Botão de salvar (LÓGICA ORIGINAL + ACRÉSCIMO DE SALVAR EM LOGS_ESTOQUE)
                if role_usuario in ["ADM", "Tecnico"]:
                    if st.button("💾 Salvar Alterações no Banco"):
                        with st.spinner("Sincronizando com a nuvem..."):
                            for _, row in edited_df.iterrows():
                                # Comparação para saber se houve alteração e gerar log
                                original_row = df.loc[df['id'] == row['id']].iloc[0]
                                if float(row['quantidade']) != float(original_row['quantidade']):
                                    
                                    # 1. Update na substancias (Original)
                                    supabase.table("substancias").update({
                                        "nome": row['nome'],
                                        "quantidade": row['quantidade'],
                                        "unidade": row['unidade'] if 'unidade' in row else "un"
                                    }).eq("id", row['id']).execute()

                                    # 2. Insert na logs_estoque (Acréscimo conforme sua imagem)
                                    supabase.table("logs_estoque").insert({
                                        "usuario": username_atual,
                                        "substancia": row['nome'],
                                        "quantidade_antiga": original_row['quantidade'],
                                        "quantidade_nova": row['quantidade'],
                                        "org_name": org_usuario
                                    }).execute()
                            
                            st.success("Estoque salvo e log gerado permanentemente!")
                            st.rerun()

            with tab_logs:
                st.subheader("📜 Histórico de Movimentações")
                # Busca logs no banco (Acréscimo)
                logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).execute()
                if logs_res.data:
                    st.dataframe(pd.DataFrame(logs_res.data), use_container_width=True)
                else:
                    st.info("Nenhum registro de alteração encontrado.")

            with tab_manutencao:
                st.subheader("🛠️ Manutenção de Equipamentos")
                # Busca equipamentos/manutenção (Acréscimo conforme sua imagem)
                manut_res = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if manut_res.data:
                    st.dataframe(pd.DataFrame(manut_res.data), use_container_width=True)
                else:
                    st.info("Nenhuma manutenção registrada para esta organização.")

        else:
            st.warning(f"O inventário da empresa {org_usuario} está vazio.")
            if role_usuario != "Visualizador":
                if st.button("➕ Criar Primeiro Item"):
                    supabase.table("substancias").insert({"nome": "Novo Item", "quantidade": 0, "org_name": org_usuario}).execute()
                    st.rerun()

    except Exception as e:
        st.error(f"Erro de Conexão: {e}")

    # --- BUSCA GERAL (SUA LÓGICA ORIGINAL) ---
    st.divider()
    st.subheader("🌐 Pesquisa Externa")
    busca_livre = st.text_input("Procurar qualquer reagente para compra:")
    if busca_livre:
        q_livre = urllib.parse.quote(busca_livre)
        st.link_button(f"Comprar {busca_livre} agora", f"https://www.google.com/search?q=comprar+{q_livre}")
