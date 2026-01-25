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
    username_atual = user_data.get('username', 'Usuário Desconhecido')

    try:
        # --- BUSCA DADOS NO SUPABASE FILTRANDO PELA EMPRESA ---
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # --- LÓGICA DE STATUS DINÂMICO ---
            # Definimos uma função para aplicar o status visual
            def calcular_status(row):
                minimo = row.get('estoque_minimo', 10) # Usa 10 como padrão se não houver na tabela
                if row['quantidade'] <= 0:
                    return "🔴 ESGOTADO"
                elif row['quantidade'] <= minimo:
                    return "🟡 CRÍTICO"
                else:
                    return "🟢 NORMAL"

            df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
            df['Status'] = df.apply(calcular_status, axis=1)

            # --- SEÇÃO DE ALERTAS E MÉTRICAS ---
            col1, col2, col3 = st.columns(3)
            itens_baixos = df[df['quantidade'] < 10]
            
            col1.metric("Total no Inventário", len(df))
            col2.metric("Itens Críticos", len(itens_baixos), delta_color="inverse")
            col3.metric("Org Ativa", org_usuario)

            # --- SEÇÃO DE COMPRAS DIRETAS ---
            if len(itens_baixos) > 0:
                with st.expander("🛒 COMPRA RÁPIDA (Itens com estoque baixo)", expanded=False):
                    st.write("Selecione um item para buscar fornecedores online:")
                    item_para_comprar = st.selectbox("Substância para repor:", itens_baixos['nome'].unique())
                    
                    if item_para_comprar:
                        query = urllib.parse.quote(item_para_comprar)
                        c1, c2, c3 = st.columns(3)
                        c1.link_button("🔍 Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop", use_container_width=True)
                        c2.link_button("🧪 Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}", use_container_width=True)
                        c3.link_button("📦 Amazon", f"https://www.amazon.com.br/s?k={query}", use_container_width=True)

            st.divider()

            # --- TABELA DE EDIÇÃO COM VISUAL DINÂMICO ---
            st.subheader(f"📝 Inventário: {org_usuario}")
            
            is_disabled = (role_usuario == "Visualizador")
            
            # Configuração visual das colunas
            edited_df = st.data_editor(
                df, 
                use_container_width=True, 
                hide_index=True, 
                disabled=is_disabled,
                column_config={
                    "org_name": st.column_config.TextColumn("Empresa", disabled=True),
                    "Status": st.column_config.TextColumn("Status Atual", help="Calculado com base na quantidade"),
                    "quantidade": st.column_config.NumberColumn("Qtd Atual", format="%.2f"),
                    "estoque_minimo": st.column_config.NumberColumn("Mínimo", help="Nível de alerta"),
                    # Adiciona um gráfico de barras visual para a quantidade
                    "quantidade_visual": st.column_config.ProgressColumn(
                        "Nível",
                        help="Representação visual do estoque",
                        min_value=0,
                        max_value=float(df['quantidade'].max() if df['quantidade'].max() > 0 else 100),
                    )
                },
                column_order=("Status", "nome", "quantidade", "unidade", "estoque_minimo", "org_name")
            )

            # Botão de salvar (Lógica de Logs e Alterações)
            if role_usuario in ["ADM", "Tecnico"]:
                if st.button("💾 Salvar Alterações e Registrar Logs"):
                    with st.spinner("Sincronizando..."):
                        houve_mudanca = False
                        
                        for index, row in edited_df.iterrows():
                            # Comparação com o DF original para identificar mudanças
                            valor_original = df.loc[df['id'] == row['id']].iloc[0]
                            qtd_antiga = float(valor_original['quantidade'])
                            qtd_nova = float(row['quantidade'])

                            if qtd_nova != qtd_antiga:
                                houve_mudanca = True
                                
                                # 1. Atualiza substancias
                                supabase.table("substancias").update({
                                    "nome": row['nome'],
                                    "quantidade": qtd_nova,
                                    "unidade": row['unidade'] if 'unidade' in row else "un"
                                }).eq("id", row['id']).execute()
                                
                                # 2. Registra Log na logs_estoque
                                supabase.table("logs_estoque").insert({
                                    "usuario": username_atual,
                                    "substancia": row['nome'],
                                    "quantidade_antiga": qtd_antiga,
                                    "quantidade_nova": qtd_nova,
                                    "org_name": org_usuario
                                }).execute()
                        
                        if houve_mudanca:
                            st.success("Estoque e Logs atualizados!")
                            st.rerun()
                        else:
                            st.info("Nenhuma alteração detectada.")

        else:
            st.warning(f"O inventário da empresa {org_usuario} está vazio.")
            if role_usuario != "Visualizador":
                if st.button("➕ Criar Primeiro Item"):
                    supabase.table("substancias").insert({"nome": "Novo Item", "quantidade": 0, "org_name": org_usuario}).execute()
                    st.rerun()

    except Exception as e:
        st.error(f"Erro no sistema: {e}")

    # --- BUSCA GERAL ---
    st.divider()
    st.subheader("🌐 Pesquisa Externa")
    busca_livre = st.text_input("Procurar qualquer reagente para compra:")
    if busca_livre:
        q_livre = urllib.parse.quote(busca_livre)
        st.link_button(f"Comprar {busca_livre} agora", f"https://www.google.com/search?q=comprar+{q_livre}")
