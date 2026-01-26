import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client
import plotly.express as px # Adicionado para os acréscimos visuais

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
    username_atual = user_data.get('username', 'Usuário')

    try:
        # --- BUSCA DADOS NO SUPABASE FILTRANDO PELA EMPRESA ---
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        # Busca logs para a Inteligência de Dados
        logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(100).execute()
        df_logs = pd.DataFrame(logs_res.data)

        if not df.empty:
            # --- CRIAÇÃO DAS SUB-ABAS (ACRÉSCIMO) ---
            tab_inv, tab_ia, tab_hist, tab_manut = st.tabs([
                "📋 Inventário e Compras", "🧠 Inteligência 2026", "📜 Histórico de Logs", "🛠️ Equipamentos"
            ])

            with tab_inv:
                # --- SEÇÃO DE ALERTAS E MÉTRICAS (SUA LÓGICA ORIGINAL) ---
                col1, col2, col3 = st.columns([1, 1, 1])
                df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
                
                itens_baixos = df[df['quantidade'] < 10]
                col1.metric("Total no Inventário", len(df))
                col2.metric("Itens para Reposição", len(itens_baixos), delta_color="inverse")

                # Acréscimo Visual 2026: Saúde do Estoque (Gráfico Donut)
                df['Status'] = df['quantidade'].apply(lambda x: "🔴 ESGOTADO" if x <= 0 else ("🟡 BAIXO" if x < 10 else "🟢 OK"))
                status_counts = df['Status'].value_counts()
                fig_saude = px.pie(names=status_counts.index, values=status_counts.values, 
                                 hole=0.6, height=150, color=status_counts.index,
                                 color_discrete_map={"🟢 OK": "#28a745", "🟡 BAIXO": "#ffc107", "🔴 ESGOTADO": "#dc3545"})
                fig_saude.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                col3.plotly_chart(fig_saude, use_container_width=True)

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

                # --- TABELA DE EDIÇÃO (SUA LÓGICA ORIGINAL + STATUS) ---
                st.subheader(f"📝 Inventário: {org_usuario}")
                is_disabled = (role_usuario == "Visualizador")
                
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

                # Botão de salvar (SUA LÓGICA ORIGINAL + LOGS)
                if role_usuario in ["ADM", "Tecnico"]:
                    if st.button("💾 Salvar Alterações no Banco"):
                        with st.spinner("Sincronizando com a nuvem..."):
                            for _, row in edited_df.iterrows():
                                original_row = df.loc[df['id'] == row['id']].iloc[0]
                                if float(row['quantidade']) != float(original_row['quantidade']):
                                    # Update na substancias (Original)
                                    supabase.table("substancias").update({
                                        "nome": row['nome'],
                                        "quantidade": row['quantidade'],
                                        "unidade": row['unidade'] if 'unidade' in row else "un"
                                    }).eq("id", row['id']).execute()

                                    # Insert na logs_estoque (Necessário para a IA)
                                    supabase.table("logs_estoque").insert({
                                        "usuario": username_atual,
                                        "substancia": row['nome'],
                                        "quantidade_antiga": original_row['quantidade'],
                                        "quantidade_nova": row['quantidade'],
                                        "org_name": org_usuario
                                    }).execute()
                            
                            st.success("Estoque salvo e logs registrados!")
                            st.rerun()

            with tab_ia:
                st.subheader("🧠 Inteligência Preditiva e BI")
                if not df_logs.empty:
                    df_saidas = df_logs[df_logs['quantidade_nova'] < df_logs['quantidade_antiga']].copy()
                    df_saidas['consumo'] = df_saidas['quantidade_antiga'] - df_saidas['quantidade_nova']
                    
                    if not df_saidas.empty:
                        # Gráfico de tendência de uso
                        fig = px.line(df_saidas, x='created_at', y='consumo', color='substancia', title="Histórico de Consumo")
                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()
                        # Lógica de Predição
                        analise_item = st.selectbox("Analisar tendência de:", df['nome'].unique())
                        qtd_atual = df.loc[df['nome'] == analise_item, 'quantidade'].values[0]
                        logs_especificos = df_saidas[df_saidas['substancia'] == analise_item]
                        
                        if not logs_especificos.empty:
                            media = logs_especificos['consumo'].mean()
                            previsao = qtd_atual / media if media > 0 else 0
                            
                            c_ia1, c_ia2 = st.columns(2)
                            c_ia1.metric("Média de Consumo", f"{media:.2f} /uso")
                            if previsao < 5:
                                c_ia2.error(f"Predição: Esgota em ~{previsao:.1f} usos")
                            else:
                                c_ia2.success(f"Predição: Seguro por ~{previsao:.1f} usos")
                        else:
                            st.info("Dados insuficientes para prever este item.")
                    else:
                        st.info("Nenhuma saída de material detectada para análise.")
                else:
                    st.info("Histórico de logs vazio.")

            with tab_hist:
                st.subheader("📜 Movimentações Recentes")
                if not df_logs.empty:
                    st.dataframe(df_logs, use_container_width=True)

            with tab_manut:
                st.subheader("🛠️ Manutenção de Equipamentos")
                manut_res = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if manut_res.data:
                    st.dataframe(pd.DataFrame(manut_res.data), use_container_width=True)
                else:
                    st.info("Nenhuma manutenção agendada.")

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
