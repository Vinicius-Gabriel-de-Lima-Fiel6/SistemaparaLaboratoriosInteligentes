import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_estoque():
    st.set_page_config(layout="wide")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(100).execute()
        df_logs = pd.DataFrame(logs_res.data)

        if not df.empty:
            df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
            df['Status'] = df['quantidade'].apply(lambda x: "🔴 ESGOTADO" if x <= 0 else ("🟡 BAIXO" if x < 10 else "🟢 OK"))
            
            st.title(f"🚀 Dashboard de Gestão | {org_usuario}")
            
            m1, m2, m3, m4 = st.columns([1, 1, 1, 2])
            itens_baixos = df[df['quantidade'] < 10]
            
            m1.metric("Total Itens", len(df))
            m2.metric("Críticos", len(itens_baixos), delta_color="inverse")
            m3.metric("Org", org_usuario)
            
            with m4:
                status_counts = df['Status'].value_counts()
                fig_health = px.pie(
                    names=status_counts.index, 
                    values=status_counts.values, 
                    hole=0.6,
                    color=status_counts.index,
                    color_discrete_map={"🟢 OK": "#00CC96", "🟡 BAIXO": "#FFA15A", "🔴 ESGOTADO": "#EF553B"}
                )
                fig_health.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=100)
                st.plotly_chart(fig_health, use_container_width=True)

            tab_inv, tab_ia, tab_manut, tab_hist, tab_assistant = st.tabs([
                "📋 Inventário", "📊 BI & Predição", "🛠️ Manutenção", "📜 Logs", "🤖 Consultor IA"
            ])

            with tab_inv:
                if len(itens_baixos) > 0:
                    with st.expander("🛒 COMPRA RÁPIDA", expanded=True):
                        item_para_comprar = st.selectbox("Substância para repor:", itens_baixos['nome'].unique())
                        if item_para_comprar:
                            query = urllib.parse.quote(item_para_comprar)
                            c1, c2, c3 = st.columns(3)
                            c1.link_button("🔍 Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop", use_container_width=True)
                            c2.link_button("🧪 Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}", use_container_width=True)
                            c3.link_button("📦 Amazon", f"https://www.amazon.com.br/s?k={query}", use_container_width=True)

                st.subheader("📝 Edição de Inventário")
                is_disabled = (role_usuario == "Visualizador")
                
                edited_df = st.data_editor(
                    df, 
                    use_container_width=True, 
                    hide_index=True, 
                    disabled=is_disabled,
                    column_config={
                        "org_name": st.column_config.TextColumn("Empresa", disabled=True),
                        "Status": st.column_config.TextColumn("Status", disabled=True),
                        "quantidade": st.column_config.NumberColumn("Qtd Atual", format="%.2f")
                    },
                    column_order=("Status", "nome", "quantidade", "unidade", "org_name")
                )

                if role_usuario in ["ADM", "Tecnico"]:
                    if st.button("💾 Sincronizar Alterações"):
                        for _, row in edited_df.iterrows():
                            original_row = df.loc[df['id'] == row['id']].iloc[0]
                            if float(row['quantidade']) != float(original_row['quantidade']):
                                supabase.table("substancias").update({
                                    "nome": row['nome'], 
                                    "quantidade": row['quantidade'],
                                    "unidade": row['unidade']
                                }).eq("id", row['id']).execute()

                                supabase.table("logs_estoque").insert({
                                    "usuario": username_atual, 
                                    "substancia": row['nome'],
                                    "quantidade_antiga": original_row['quantidade'],
                                    "quantidade_nova": row['quantidade'], 
                                    "org_name": org_usuario
                                }).execute()
                        st.success("Base de dados atualizada!")
                        st.rerun()

            with tab_ia:
                g1, g2 = st.columns(2)
                
                if not df_logs.empty:
                    df_saidas = df_logs[df_logs['quantidade_nova'] < df_logs['quantidade_antiga']].copy()
                    df_saidas['consumo'] = df_saidas['quantidade_antiga'] - df_saidas['quantidade_nova']
                    
                    with g1:
                        st.markdown("### 📈 Fluxo de Saída")
                        fig_area = px.area(df_saidas, x='created_at', y='consumo', color='substancia',
                                          template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig_area, use_container_width=True)

                    with g2:
                        st.markdown("### 🗓️ Previsão de Esgotamento")
                        analise_item = st.selectbox("Selecionar Item:", df['nome'].unique())
                        qtd_atual = df.loc[df['nome'] == analise_item, 'quantidade'].values[0]
                        logs_item = df_saidas[df_saidas['substancia'] == analise_item]
                        
                        if not logs_item.empty:
                            media = logs_item['consumo'].mean()
                            previsao = qtd_atual / media if media > 0 else 0
                            
                            fig_gauge = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = previsao,
                                title = {'text': "Ciclos Restantes"},
                                gauge = {
                                    'axis': {'range': [None, 20]},
                                    'bar': {'color': "#636EFA"},
                                    'steps': [
                                        {'range': [0, 5], 'color': "red"},
                                        {'range': [5, 10], 'color': "yellow"},
                                        {'range': [10, 20], 'color': "green"}]
                                }
                            ))
                            fig_gauge.update_layout(height=250, margin=dict(t=30, b=0, l=10, r=10))
                            st.plotly_chart(fig_gauge, use_container_width=True)
                        else:
                            st.info("Aguardando mais logs de consumo.")

            with tab_manut:
                st.subheader("⚙️ Manutenções Agendadas")
                manut_res = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if manut_res.data:
                    df_m = pd.DataFrame(manut_res.data)
                    st.dataframe(df_m, use_container_width=True)
                else:
                    st.info("Sistema operando sem manutenções pendentes.")

            with tab_hist:
                st.subheader("📜 Log de Auditoria")
                st.dataframe(df_logs, use_container_width=True, hide_index=True)

            with tab_assistant:
                st.subheader("🤖 Consultor Estratégico IA")
                input_ia = st.text_input("Consultar Assistente:")
                if input_ia:
                    criticos = df[df['quantidade'] < 5]['nome'].tolist()
                    if criticos:
                        st.warning(f"**Análise Crítica:** Priorize a reposição de: {', '.join(criticos)}.")
                    else:
                        st.success("Nível de estoque estável em toda a unidade.")

        else:
            st.warning("Inventário não encontrado.")
            if role_usuario != "Visualizador":
                if st.button("➕ Adicionar Item"):
                    supabase.table("substancias").insert({"nome": "Novo Item", "quantidade": 0, "org_name": org_usuario}).execute()
                    st.rerun()

    except Exception as e:
        st.error(f"Erro de Conexão: {e}")

    st.divider()
    st.subheader("🌐 Marketplace Externo")
    busca_livre = st.text_input("Pesquisar Reagentes em Lojas Externas:")
    if busca_livre:
        q_livre = urllib.parse.quote(busca_livre)
        st.link_button("🌐 Iniciar Busca Global", f"https://www.google.com/search?q=comprar+{q_livre}")
