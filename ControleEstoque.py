import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from datetime import datetime

# Configurações de Conexão
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])

def show_estoque():
    st.set_page_config(layout="wide")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    try:
        # Segurança: Filtro por org_name mantido em 100% das consultas
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(100).execute()
        df_logs = pd.DataFrame(logs_res.data)

        if not df.empty:
            df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
            df['Status'] = df['quantidade'].apply(lambda x: "🔴 ESGOTADO" if x <= 0 else ("🟡 BAIXO" if x < 10 else "🟢 OK"))
            
            st.title(f"🚀 Gestão de Insumos | {org_usuario}")
            
            # --- HEADER: MÉTRICAS E ROSCA COM PLANO DE FUNDO ---
            m1, m2, m3, m4 = st.columns([1, 1, 1, 2])
            itens_baixos = df[df['quantidade'] < 10]
            
            m1.metric("📦 Itens no Inventário", len(df))
            m2.metric("⚠️ Críticos", len(itens_baixos), delta_color="inverse")
            m3.info(f"📍 Unidade: {org_usuario}")
            
            with m4:
                status_counts = df['Status'].value_counts()
                fig_health = px.pie(
                    names=status_counts.index, 
                    values=status_counts.values, 
                    hole=0.6,
                    color=status_counts.index,
                    color_discrete_map={"🟢 OK": "#2E7D32", "🟡 BAIXO": "#F9A825", "🔴 ESGOTADO": "#C62828"}
                )
                fig_health.update_layout(
                    showlegend=False, 
                    margin=dict(t=10, b=10, l=10, r=10), 
                    height=100,
                    paper_bgcolor="#E1E4E8", # Plano de fundo solicitado
                    plot_bgcolor="#E1E4E8"
                )
                st.plotly_chart(fig_health, use_container_width=True)

            # --- ABAS COM ÍCONES E DETALHES ORIGINAIS ---
            tab_inv, tab_ia, tab_manut, tab_hist, tab_llama = st.tabs([
                "📋 Lista de Materiais", "📈 Consumo no Tempo", "🛠️ Equipamentos", "📜 Logs de Auditoria", "🤖 Assistente Llama 3.3"
            ])

            with tab_inv:
                if len(itens_baixos) > 0:
                    with st.expander("🛒 COMPRA RÁPIDA (Marketplace)", expanded=True):
                        item_sel = st.selectbox("O que precisa repor?", itens_baixos['nome'].unique())
                        if item_sel:
                            query = urllib.parse.quote(item_sel)
                            c1, c2, c3 = st.columns(3)
                            c1.link_button("🔍 Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop", use_container_width=True)
                            c2.link_button("🧪 Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}", use_container_width=True)
                            c3.link_button("📦 Amazon", f"https://www.amazon.com.br/s?k={query}", use_container_width=True)

                st.subheader("📝 Edição de Estoque")
                is_disabled = (role_usuario == "Visualizador")
                
                edited_df = st.data_editor(
                    df, use_container_width=True, hide_index=True, disabled=is_disabled,
                    column_config={
                        "org_name": st.column_config.TextColumn("Empresa", disabled=True),
                        "Status": st.column_config.TextColumn("Status", disabled=True),
                        "quantidade": st.column_config.NumberColumn("Qtd Atual", format="%.2f")
                    },
                    column_order=("Status", "nome", "quantidade", "unidade", "org_name")
                )

                if role_usuario in ["ADM", "Tecnico"]:
                    if st.button("💾 Sincronizar e Gravar Logs"):
                        for _, row in edited_df.iterrows():
                            orig = df.loc[df['id'] == row['id']].iloc[0]
                            if float(row['quantidade']) != float(orig['quantidade']):
                                supabase.table("substancias").update({
                                    "nome": row['nome'], "quantidade": row['quantidade'], "unidade": row['unidade']
                                }).eq("id", row['id']).eq("org_name", org_usuario).execute()

                                supabase.table("logs_estoque").insert({
                                    "usuario": username_atual, "substancia": row['nome'],
                                    "quantidade_antiga": orig['quantidade'],
                                    "quantidade_nova": row['quantidade'], "org_name": org_usuario
                                }).execute()
                        st.success("Dados atualizados!")
                        st.rerun()

            with tab_ia:
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    st.markdown("### 📈 Fluxo Diário de Uso 💡")
                    st.caption("A lâmpada indica: Este gráfico de linhas mostra o consumo exato por dia. Pontos altos indicam maior gasto.")
                    if not df_logs.empty:
                        df_saidas = df_logs[df_logs['quantidade_nova'] < df_logs['quantidade_antiga']].copy()
                        df_saidas['consumo'] = df_saidas['quantidade_antiga'] - df_saidas['quantidade_nova']
                        
                        # Gráfico de Linha (Substituindo a montanha)
                        fig_line = px.line(df_saidas, x='created_at', y='consumo', color='substancia', 
                                           markers=True, template="plotly_white")
                        st.plotly_chart(fig_line, use_container_width=True)

                with col_g2:
                    st.markdown("### 🗓️ Autonomia Estimada 💡")
                    st.caption("A lâmpada indica: A barra mostra quantos usos restam com base na sua média de consumo.")
                    analise_item = st.selectbox("Previsão para o item:", df['nome'].unique())
                    qtd_at = df.loc[df['nome'] == analise_item, 'quantidade'].values[0]
                    logs_item = df_saidas[df_saidas['substancia'] == analise_item] if not df_logs.empty else pd.DataFrame()
                    
                    if not logs_item.empty:
                        media = logs_item['consumo'].mean()
                        ciclos = qtd_at / media if media > 0 else 0
                        
                        # Bullet Chart (Substituindo o ponteiro colorido)
                        fig_bullet = go.Figure(go.Indicator(
                            mode = "number+gauge", value = ciclos,
                            gauge = {'shape': "bullet", 'axis': {'range': [None, 30]}, 'bar': {'color': "#2b3e50"}},
                            title = {'text': "Ciclos", 'font': {'size': 14}}
                        ))
                        fig_bullet.update_layout(height=150, margin=dict(t=40, b=20))
                        st.plotly_chart(fig_bullet, use_container_width=True)
                    else:
                        st.info("Sem histórico para este item.")

            with tab_manut:
                st.subheader("🛠️ Manutenções Programadas")
                manut_res = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if manut_res.data:
                    st.dataframe(pd.DataFrame(manut_res.data), use_container_width=True)
                else:
                    st.info("Nenhuma manutenção agendada.")

            with tab_hist:
                st.subheader("📜 Auditoria Completa")
                st.dataframe(df_logs, use_container_width=True, hide_index=True)

            with tab_llama:
                st.subheader("🤖 Consultor Técnico Llama 3.3-70B")
                st.markdown("*IA Profissional analisando os dados da sua unidade.*")
                
                contexto_estoque = df[['nome', 'quantidade', 'unidade', 'Status']].to_string()
                pre_prompt = f"""
                Você é um Gerente de Logística de Laboratório Profissional.
                Analise os dados da empresa {org_usuario}. NUNCA mencione outras empresas.
                Seja direto, técnico e use terminologia laboratorial.
                Dados atuais: {contexto_estoque}
                """
                
                user_input = st.chat_input("Pergunte ao Llama sobre sua logística...")
                if user_input:
                    with st.chat_message("assistant"):
                        chat_completion = client_groq.chat.completions.create(
                            messages=[{"role": "system", "content": pre_prompt}, {"role": "user", "content": user_input}],
                            model="llama-3.3-70b-versatile",
                        )
                        st.write(chat_completion.choices[0].message.content)

    except Exception as e:
        st.error(f"Erro no Sistema: {e}")

    st.divider()
    st.subheader("🌐 Busca Externa de Insumos")
    busca_livre = st.text_input("Não achou no estoque? Pesquise aqui:")
    if busca_livre:
        st.link_button("🔍 Buscar na Web", f"https://www.google.com/search?q=comprar+{urllib.parse.quote(busca_livre)}")
