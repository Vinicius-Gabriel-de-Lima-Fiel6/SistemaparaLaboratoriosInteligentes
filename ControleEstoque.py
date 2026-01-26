import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq

# Configurações de Conexão
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])

def show_estoque():
    st.title("📦 Controle de Materiais e Laboratório")
    
    # Recupera dados do usuário (Segurança Multitenant)
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    try:
        # Busca dados filtrados por organização
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(100).execute()
        df_logs = pd.DataFrame(logs_res.data)

        if not df.empty:
            df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
            df['Status'] = df['quantidade'].apply(lambda x: "🔴 Acabou" if x <= 0 else ("🟡 Pouco" if x < 10 else "🟢 OK"))
            
            # --- HEADER: MÉTRICAS E GRÁFICO DE SAÚDE (RECUPERADO) ---
            m1, m2, m3, m4 = st.columns([1, 1, 1, 2])
            itens_baixos = df[df['quantidade'] < 10]
            
            m1.metric("Itens no Lab", len(df))
            m2.metric("Repor Urgente", len(itens_baixos), delta_color="inverse")
            m3.info(f"Unidade: {org_usuario}")
            
            with m4:
                status_counts = df['Status'].value_counts()
                fig_health = px.pie(
                    names=status_counts.index, values=status_counts.values, hole=0.6,
                    color=status_counts.index,
                    color_discrete_map={"🟢 OK": "#00CC96", "🟡 Pouco": "#FFA15A", "🔴 Acabou": "#EF553B"}
                )
                fig_health.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=100)
                st.plotly_chart(fig_health, use_container_width=True)

            # --- ABAS COM NOMES SIMPLIFICADOS ---
            tab_inv, tab_ia, tab_manut, tab_hist, tab_llama = st.tabs([
                "📋 Lista de Materiais", "📊 Consumo no Tempo", "🛠️ Equipamentos", "📜 Histórico", "🤖 Assistente do Lab"
            ])

            with tab_inv:
                # Lógica de Compra Rápida (Recuperada com Sigma e Amazon)
                if len(itens_baixos) > 0:
                    with st.expander("🛒 ONDE COMPRAR (Itens em falta)", expanded=True):
                        item_para_comprar = st.selectbox("Escolha o material para repor:", itens_baixos['nome'].unique())
                        if item_para_comprar:
                            query = urllib.parse.quote(item_para_comprar)
                            c1, c2, c3 = st.columns(3)
                            c1.link_button("🔍 Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop", use_container_width=True)
                            c2.link_button("🧪 Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}", use_container_width=True)
                            c3.link_button("📦 Amazon", f"https://www.amazon.com.br/s?k={query}", use_container_width=True)

                st.divider()
                is_disabled = (role_usuario == "Visualizador")
                
                edited_df = st.data_editor(
                    df, use_container_width=True, hide_index=True, disabled=is_disabled,
                    column_config={
                        "org_name": st.column_config.TextColumn("Lab", disabled=True),
                        "Status": st.column_config.TextColumn("Situação", disabled=True),
                        "quantidade": st.column_config.NumberColumn("Qtd", format="%.2f")
                    },
                    column_order=("Status", "nome", "quantidade", "unidade", "org_name")
                )

                if role_usuario in ["ADM", "Tecnico"]:
                    if st.button("💾 Atualizar Banco de Dados"):
                        for _, row in edited_df.iterrows():
                            original_row = df.loc[df['id'] == row['id']].iloc[0]
                            if float(row['quantidade']) != float(original_row['quantidade']):
                                # Update na tabela principal
                                supabase.table("substancias").update({
                                    "nome": row['nome'], "quantidade": row['quantidade'], "unidade": row['unidade']
                                }).eq("id", row['id']).eq("org_name", org_usuario).execute()

                                # Registro do Log
                                supabase.table("logs_estoque").insert({
                                    "usuario": username_atual, "substancia": row['nome'],
                                    "quantidade_antiga": original_row['quantidade'],
                                    "quantidade_nova": row['quantidade'], "org_name": org_usuario
                                }).execute()
                        st.success("Estoque e Histórico atualizados!")
                        st.rerun()

            with tab_ia:
                col_ia1, col_ia2 = st.columns(2)
                
                with col_ia1:
                    st.markdown("### Uso de Materiais por Data 💡")
                    st.caption("Ajuda: A linha mostra o consumo diário. Picos indicam dias de uso intenso.")
                    if not df_logs.empty:
                        df_saidas = df_logs[df_logs['quantidade_nova'] < df_logs['quantidade_antiga']].copy()
                        df_saidas['consumo'] = df_saidas['quantidade_antiga'] - df_saidas['quantidade_nova']
                        # Gráfico de Linhas (Substituindo a montanha)
                        fig_line = px.line(df_saidas, x='created_at', y='consumo', color='substancia', markers=True, template="plotly_white")
                        st.plotly_chart(fig_line, use_container_width=True)

                with col_ia2:
                    st.markdown("### Previsão de Duração 💡")
                    st.caption("Ajuda: Cálculo baseado na sua média de consumo atual.")
                    analise_item = st.selectbox("Selecione para analisar:", df['nome'].unique())
                    qtd_at = df.loc[df['nome'] == analise_item, 'quantidade'].values[0]
                    
                    logs_item = df_logs[(df_logs['substancia'] == analise_item) & (df_logs['quantidade_nova'] < df_logs['quantidade_antiga'])]
                    if not logs_item.empty:
                        media = (logs_item['quantidade_antiga'] - logs_item['quantidade_nova']).mean()
                        restam = qtd_at / media if media > 0 else 0
                        # Indicador Direto e Limpo
                        st.metric(label=f"Duração para {analise_item}", value=f"{restam:.1f} usos", delta=f"Média de {media:.2f} por retirada")
                    else:
                        st.info("Aguardando mais registros de uso para este item.")

            with tab_manut:
                st.subheader("🛠️ Revisão de Equipamentos")
                manut_res = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if manut_res.data:
                    st.dataframe(pd.DataFrame(manut_res.data), use_container_width=True)
                else:
                    st.info("Nenhuma manutenção agendada no momento.")

            with tab_hist:
                st.subheader("📜 Quem alterou o estoque")
                st.dataframe(df_logs[['created_at', 'usuario', 'substancia', 'quantidade_antiga', 'quantidade_nova']], use_container_width=True, hide_index=True)

            with tab_llama:
                st.subheader("🤖 Assistente Llama 3.3")
                pre_prompt = f"""
                Você é um Técnico de Laboratório experiente. Analise o estoque da empresa {org_usuario}.
                Seja prático e direto.
                Dados atuais: {df[['nome', 'quantidade', 'Status']].to_string()}
                """
                pergunta = st.chat_input("Dúvida sobre o material ou consumo?")
                if pergunta:
                    with st.chat_message("assistant"):
                        chat = client_groq.chat.completions.create(
                            messages=[{"role": "system", "content": pre_prompt}, {"role": "user", "content": pergunta}],
                            model="llama-3.3-70b-versatile",
                        )
                        st.write(chat.choices[0].message.content)

        else:
            st.warning("Inventário vazio para este laboratório.")

    except Exception as e:
        st.error(f"Erro de conexão: {e}")

    # --- PESQUISA EXTERNA (Sua lógica original no rodapé) ---
    st.divider()
    st.subheader("🌐 Pesquisa de Preços Externa")
    busca = st.text_input("Digite o nome de um reagente ou material:")
    if busca:
        st.link_button(f"🔍 Comprar {busca} agora", f"https://www.google.com/search?q=comprar+{urllib.parse.quote(busca)}")
