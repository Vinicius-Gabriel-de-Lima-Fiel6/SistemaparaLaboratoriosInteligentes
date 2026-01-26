import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])

def show_estoque():
    st.title("📦 Sistema de Controle de Laboratório")
    
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
            
            m1, m2, m3, m4 = st.columns([1, 1, 1, 2])
            itens_baixos = df[df['quantidade'] < 10]
            
            m1.metric("Itens no Estoque", len(df))
            m2.metric("Acabando", len(itens_baixos), delta_color="inverse")
            m3.info(f"Lab: {org_usuario}")
            
            with m4:
                status_counts = df['Status'].value_counts()
                fig_health = px.pie(
                    names=status_counts.index, values=status_counts.values, hole=0.6,
                    color=status_counts.index,
                    color_discrete_map={"🟢 OK": "#00CC96", "🟡 BAIXO": "#FFA15A", "🔴 ESGOTADO": "#EF553B"}
                )
                fig_health.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=100)
                st.plotly_chart(fig_health, use_container_width=True)

            tab_inv, tab_ia, tab_manut, tab_hist, tab_llama = st.tabs([
                "📋 Estoque Atual", "📊 Gráficos de Uso", "🛠️ Equipamentos", "📜 Histórico", "🤖 Assistente do Laboratório"
            ])

            with tab_inv:
                if len(itens_baixos) > 0:
                    with st.expander("🛒 COMPRA RÁPIDA", expanded=True):
                        st.write("Selecione um item para ver onde comprar:")
                        item_para_comprar = st.selectbox("O que precisa repor?", itens_baixos['nome'].unique())
                        
                        if item_para_comprar:
                            query = urllib.parse.quote(item_para_comprar)
                            c1, c2, c3 = st.columns(3)
                            c1.link_button("🔍 Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop", use_container_width=True)
                            c2.link_button("🧪 Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}", use_container_width=True)
                            c3.link_button("📦 Amazon", f"https://www.amazon.com.br/s?k={query}", use_container_width=True)

                st.divider()
                st.subheader("📝 Lista de Materiais")
                is_disabled = (role_usuario == "Visualizador")
                
                edited_df = st.data_editor(
                    df, use_container_width=True, hide_index=True, disabled=is_disabled,
                    column_config={
                        "org_name": st.column_config.TextColumn("Empresa", disabled=True),
                        "Status": st.column_config.TextColumn("Status", disabled=True),
                        "quantidade": st.column_config.NumberColumn("Qtd", format="%.2f")
                    },
                    column_order=("Status", "nome", "quantidade", "unidade", "org_name")
                )

                if role_usuario in ["ADM", "Tecnico"]:
                    if st.button("💾 Salvar Alterações"):
                        for _, row in edited_df.iterrows():
                            original_row = df.loc[df['id'] == row['id']].iloc[0]
                            if float(row['quantidade']) != float(original_row['quantidade']):
                                supabase.table("substancias").update({
                                    "nome": row['nome'], "quantidade": row['quantidade'], "unidade": row['unidade']
                                }).eq("id", row['id']).eq("org_name", org_usuario).execute()

                                supabase.table("logs_estoque").insert({
                                    "usuario": username_atual, "substancia": row['nome'],
                                    "quantidade_antiga": original_row['quantidade'],
                                    "quantidade_nova": row['quantidade'], "org_name": org_usuario
                                }).execute()
                        st.success("Salvo!")
                        st.rerun()

            with tab_ia:
                col_ia1, col_ia2 = st.columns(2)
                with col_ia1:
                    st.markdown("### 📈 Tendência de Consumo 💡")
                    st.caption("Ajuda: Mostra a velocidade que os materiais estão sendo gastos. Montanhas altas = muito gasto.")
                    if not df_logs.empty:
                        df_saidas = df_logs[df_logs['quantidade_nova'] < df_logs['quantidade_antiga']].copy()
                        df_saidas['consumo'] = df_saidas['quantidade_antiga'] - df_saidas['quantidade_nova']
                        fig_area = px.area(df_saidas, x='created_at', y='consumo', color='substancia', template="plotly_white")
                        st.plotly_chart(fig_area, use_container_width=True)

                with col_ia2:
                    st.markdown("### 🗓️ Quanto tempo dura? 💡")
                    st.caption("Ajuda: O ponteiro mostra quantos usos o material ainda aguenta antes de acabar.")
                    analise_item = st.selectbox("Escolha o material:", df['nome'].unique())
                    qtd_atual = df.loc[df['nome'] == analise_item, 'quantidade'].values[0]
                    logs_item = df_logs[(df_logs['substancia'] == analise_item) & (df_logs['quantidade_nova'] < df_logs['quantidade_antiga'])]
                    if not logs_item.empty:
                        media = (logs_item['quantidade_antiga'] - logs_item['quantidade_nova']).mean()
                        previsao = qtd_atual / media if media > 0 else 0
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number", value = previsao,
                            gauge = {'axis': {'range': [None, 25]}, 'bar': {'color': "#1f77b4"},
                                    'steps': [{'range': [0, 5], 'color': "#EF553B"}, {'range': [5, 12], 'color': "#FFA15A"}]}
                        ))
                        fig_gauge.update_layout(height=250, margin=dict(t=0, b=0))
                        st.plotly_chart(fig_gauge, use_container_width=True)

            with tab_manut:
                st.subheader("🛠️ Revisão de Equipamentos")
                manut_res = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if manut_res.data:
                    st.dataframe(pd.DataFrame(manut_res.data), use_container_width=True)
                else:
                    st.info("Tudo em dia!")

            with tab_hist:
                st.subheader("📜 Quem mexeu no quê")
                st.dataframe(df_logs, use_container_width=True, hide_index=True)

            with tab_llama:
                st.subheader("🤖 Assistente de Inteligência Artificial")
                st.markdown("*Especialista em Logística Laboratorial (Llama 3.3 70B)*")
                
                contexto_estoque = df[['nome', 'quantidade', 'unidade', 'Status']].to_string()
                pre_prompt = f"""
                Você é um Gerente de Laboratório Profissional. Analise os dados da unidade {org_usuario}.
                Responda como um técnico experiente. Se algo estiver acabando, avise.
                NÃO fale de outras empresas. Foque apenas nestes dados:
                {contexto_estoque}
                """
                pergunta_user = st.chat_input("Tire dúvidas sobre o estoque...")
                if pergunta_user:
                    with st.chat_message("assistant"):
                        chat_completion = client_groq.chat.completions.create(
                            messages=[{"role": "system", "content": pre_prompt}, {"role": "user", "content": pergunta_user}],
                            model="llama-3.3-70b-versatile",
                        )
                        st.write(chat_completion.choices[0].message.content)

    except Exception as e:
        st.error(f"Erro: {e}")

    st.divider()
    st.subheader("🌐 Comprar fora do inventário")
    busca_livre = st.text_input("Nome do reagente ou material:")
    if busca_livre:
        st.link_button(f"🔍 Procurar '{busca_livre}' na Web", f"https://www.google.com/search?q=comprar+{urllib.parse.quote(busca_livre)}")
