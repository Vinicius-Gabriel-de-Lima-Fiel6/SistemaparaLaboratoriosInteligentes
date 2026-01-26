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
    st.title("📦 Controle de Materiais")
    
    # Segurança Multitenant (Rigorosa)
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    try:
        # Busca filtrada por empresa
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(100).execute()
        df_logs = pd.DataFrame(logs_res.data)

        if not df.empty:
            df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
            df['Status'] = df['quantidade'].apply(lambda x: "🔴 Acabou" if x <= 0 else ("🟡 Pouco" if x < 10 else "🟢 OK"))
            
            # --- MÉTRICAS DE TOPO ---
            m1, m2, m3, m4 = st.columns([1, 1, 1, 2])
            itens_baixos = df[df['quantidade'] < 10]
            
            m1.metric("Itens Totais", len(df))
            m2.metric("Reposição", len(itens_baixos))
            m3.info(f"Unidade: {org_usuario}")
            
            with m4:
                # Gráfico de Saúde (Mantido mas discreto)
                status_counts = df['Status'].value_counts()
                fig_health = px.pie(
                    names=status_counts.index, values=status_counts.values, hole=0.7,
                    color=status_counts.index,
                    color_discrete_map={"🟢 OK": "#2E7D32", "🟡 Pouco": "#F9A825", "🔴 Acabou": "#C62828"}
                )
                fig_health.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=100)
                st.plotly_chart(fig_health, use_container_width=True)

            # --- ABAS COM NOMES PARA TÉCNICOS ---
            tab_inv, tab_ia, tab_manut, tab_hist, tab_llama = st.tabs([
                "📋 Lista de Materiais", "📈 Consumo no Tempo", "🛠️ Equipamentos", "📜 Histórico", "🤖 Assistente IA"
            ])

            with tab_inv:
                # Botões de Compra (Lógica original 100% mantida)
                if len(itens_baixos) > 0:
                    with st.expander("🛒 LINKS PARA COMPRA", expanded=True):
                        item_para_comprar = st.selectbox("Material para repor:", itens_baixos['nome'].unique())
                        if item_para_comprar:
                            query = urllib.parse.quote(item_para_comprar)
                            c1, c2, c3 = st.columns(3)
                            c1.link_button("Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop", use_container_width=True)
                            c2.link_button("Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}", use_container_width=True)
                            c3.link_button("Amazon", f"https://www.amazon.com.br/s?k={query}", use_container_width=True)

                st.divider()
                is_disabled = (role_usuario == "Visualizador")
                
                edited_df = st.data_editor(
                    df, use_container_width=True, hide_index=True, disabled=is_disabled,
                    column_config={
                        "org_name": st.column_config.TextColumn("Lab", disabled=True),
                        "Status": st.column_config.TextColumn("Situação", disabled=True),
                        "quantidade": st.column_config.NumberColumn("Qtd Atual", format="%.2f")
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
                        st.success("Alterações salvas!")
                        st.rerun()

            with tab_ia:
                # --- GRÁFICO DE LINHA SIMPLES (ALTERADO) ---
                st.markdown("### Histórico de Uso Diário 💡")
                st.caption("Linha simples mostrando o quanto foi gasto de cada material ao longo dos dias.")
                if not df_logs.empty:
                    df_saidas = df_logs[df_logs['quantidade_nova'] < df_logs['quantidade_antiga']].copy()
                    df_saidas['consumo'] = df_saidas['quantidade_antiga'] - df_saidas['quantidade_nova']
                    
                    # Gráfico de linha sem preenchimento colorido (estilo sóbrio)
                    fig_line = px.line(df_saidas, x='created_at', y='consumo', color='substancia', 
                                       markers=True, line_shape="linear", template="plotly_white")
                    fig_line.update_traces(line=dict(width=2))
                    st.plotly_chart(fig_line, use_container_width=True)

                    st.divider()
                    
                    # --- INDICADOR DIRETO SEM CORES (ALTERADO) ---
                    st.markdown("### Estimativa de Término 💡")
                    anal_item = st.selectbox("Previsão para o item:", df['nome'].unique())
                    qtd_at = df.loc[df['nome'] == anal_item, 'quantidade'].values[0]
                    logs_item = df_saidas[df_saidas['substancia'] == anal_item]
                    
                    if not logs_item.empty:
                        media = logs_item['consumo'].mean()
                        restam = qtd_at / media if media > 0 else 0
                        # Uso do st.metric para ser 100% direto e sem "velocímetro"
                        st.metric(label=f"Usos restantes para {anal_item}", value=f"{restam:.1f} ciclos", 
                                  delta=f"Média: {media:.2f}/uso", delta_color="off")
                    else:
                        st.info("Ainda não há dados de saída para predição.")

            with tab_manut:
                st.subheader("🛠️ Revisão de Equipamentos")
                manut_res = supabase.table("manutencao").select("*").eq("org_name", org_usuario).execute()
                if manut_res.data:
                    st.dataframe(pd.DataFrame(manut_res.data), use_container_width=True)
                else:
                    st.info("Sem manutenções agendadas.")

            with tab_hist:
                st.subheader("📜 Registro de Atividades")
                st.dataframe(df_logs[['created_at', 'usuario', 'substancia', 'quantidade_antiga', 'quantidade_nova']], 
                             use_container_width=True, hide_index=True)

            with tab_llama:
                st.subheader("🤖 Consultor Técnico IA")
                # Modelo Llama-3.3-70B-Versatile
                pre_prompt = f"Você é um técnico sênior de laboratório. Analise o estoque da empresa {org_usuario} e responda de forma curta e prática. Dados atuais: {df[['nome', 'quantidade', 'Status']].to_string()}"
                pergunta = st.chat_input("Dúvida sobre consumo ou reposição?")
                if pergunta:
                    with st.chat_message("assistant"):
                        chat = client_groq.chat.completions.create(
                            messages=[{"role": "system", "content": pre_prompt}, {"role": "user", "content": pergunta}],
                            model="llama-3.3-70b-versatile",
                        )
                        st.write(chat.choices[0].message.content)

    except Exception as e:
        st.error(f"Erro no sistema: {e}")

    # --- PESQUISA EXTERNA (RODAPÉ) ---
    st.divider()
    st.subheader("🌐 Pesquisa Global")
    busca = st.text_input("Buscar fornecedor externo:")
    if busca:
        st.link_button(f"🔍 Comprar {busca}", f"https://www.google.com/search?q=comprar+{urllib.parse.quote(busca)}")
