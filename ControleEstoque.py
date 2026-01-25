import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client

# Configurações do Supabase (buscando as chaves do seu st.secrets)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_estoque():
    st.title("📦 Controle de Estoque e Gestão Integrada")
    
    # Recupera os dados do usuário logado no app.py
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário Desconhecido')

    try:
        # --- BUSCA DADOS NO SUPABASE ---
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        # Busca logs para a aba de histórico
        res_logs = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(50).execute()
        df_logs = pd.DataFrame(res_logs.data)

        # --- CRIAÇÃO DAS SUB-ABAS (ACRÉSCIMO) ---
        tab_estoque, tab_visual, tab_historico, tab_manutencao = st.tabs([
            "📋 Inventário", "📊 Análise Visual", "📜 Histórico de Logs", "🛠️ Manutenções"
        ])

        if not df.empty:
            # Tratamento de dados padrão que já existia
            df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
            itens_baixos = df[df['quantidade'] < 10]

            # --- CONTEÚDO DA ABA 1: INVENTÁRIO (O QUE JÁ TINHA) ---
            with tab_estoque:
                col1, col2 = st.columns(2)
                col1.metric("Total no Inventário", len(df))
                col2.metric("Itens para Reposição", len(itens_baixos), delta_color="inverse")

                # Seção de Compras Diretas (Mantido exatamente como estava)
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
                st.subheader(f"📝 Inventário: {org_usuario}")
                
                # Lógica de Status Dinâmico (Acréscimo visual)
                def get_status(row):
                    if row['quantidade'] <= 0: return "🔴 ESGOTADO"
                    if row['quantidade'] < 10: return "🟡 BAIXO"
                    return "🟢 OK"
                df['Status'] = df.apply(get_status, axis=1)

                is_disabled = (role_usuario == "Visualizador")
                
                edited_df = st.data_editor(
                    df, 
                    use_container_width=True, 
                    hide_index=True, 
                    disabled=is_disabled,
                    column_config={
                        "org_name": st.column_config.TextColumn("Empresa", disabled=True),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                        "quantidade": st.column_config.NumberColumn("Qtd Atual"),
                        "id": None # Esconde o ID para ficar mais limpo
                    },
                    column_order=("Status", "nome", "quantidade", "unidade", "org_name")
                )

                # Botão de salvar (Lógica de Logs integrada)
                if role_usuario in ["ADM", "Tecnico"]:
                    if st.button("💾 Salvar Alterações e Registrar no Histórico"):
                        with st.spinner("Salvando..."):
                            mudou = False
                            for index, row in edited_df.iterrows():
                                original = df.loc[df['id'] == row['id']].iloc[0]
                                if float(row['quantidade']) != float(original['quantidade']):
                                    mudou = True
                                    # Salva na tabela substancias
                                    supabase.table("substancias").update({
                                        "nome": row['nome'],
                                        "quantidade": row['quantidade'],
                                        "unidade": row['unidade']
                                    }).eq("id", row['id']).execute()
                                    
                                    # Registra na logs_estoque (Acréscimo solicitado)
                                    supabase.table("logs_estoque").insert({
                                        "usuario": username_atual,
                                        "substancia": row['nome'],
                                        "quantidade_antiga": original['quantidade'],
                                        "quantidade_nova": row['quantidade'],
                                        "org_name": org_usuario
                                    }).execute()
                            
                            if mudou:
                                st.success("Estoque e Histórico atualizados!")
                                st.rerun()

            # --- ABA 2: ANÁLISE VISUAL (ACRÉSCIMO) ---
            with tab_visual:
                st.subheader("📊 Níveis de Estoque")
                st.bar_chart(df.set_index("nome")["quantidade"])

            # --- ABA 3: HISTÓRICO DE LOGS (ACRÉSCIMO) ---
            with tab_historico:
                st.subheader("📜 Movimentações Recentes")
                if not df_logs.empty:
                    st.dataframe(df_logs[["created_at", "usuario", "substancia", "quantidade_antiga", "quantidade_nova"]], use_container_width=True)
                else:
                    st.info("Nenhuma movimentação registrada.")

            # --- ABA 4: MANUTENÇÕES (INTEGRAÇÃO COM A IMAGEM QUE VOCÊ MANDOU) ---
            with tab_manutencao:
                st.subheader("🛠️ Manutenção de Equipamentos")
                res_m = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if res_m.data:
                    st.dataframe(pd.DataFrame(res_m.data), use_container_width=True)
                else:
                    st.info("Nenhuma manutenção agendada para esta organização.")

        else:
            st.warning(f"O inventário da empresa {org_usuario} está vazio.")
            if role_usuario != "Visualizador":
                if st.button("➕ Criar Primeiro Item"):
                    supabase.table("substancias").insert({"nome": "Novo Item", "quantidade": 0, "org_name": org_usuario}).execute()
                    st.rerun()

    except Exception as e:
        st.error(f"Erro de Conexão: {e}")

    # --- BUSCA GERAL (Mantida exatamente no mesmo lugar) ---
    st.divider()
    st.subheader("🌐 Pesquisa Externa")
    busca_livre = st.text_input("Procurar qualquer reagente para compra:")
    if busca_livre:
        q_livre = urllib.parse.quote(busca_livre)
        st.link_button(f"Comprar {busca_livre} agora", f"https://www.google.com/search?q=comprar+{q_livre}")

# Seria interessante eu adicionar uma notificação por e-mail quando o item chega em "🔴 ESGOTADO"?
