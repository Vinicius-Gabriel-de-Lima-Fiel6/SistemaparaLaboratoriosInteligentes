import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse # Para converter nomes em links de internet

DB_PATH = "data/lab_data.db"

def show_estoque():
    st.title("📦 Controle de Estoque e Compras")

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM substancias", conn)
        
        if not df.empty:
            # --- SEÇÃO DE ALERTAS E MÉTRICAS ---
            col1, col2 = st.columns(2)
            itens_baixos = df[df['quantidade'] < 10]
            col1.metric("Total no Inventário", len(df))
            col2.metric("Itens para Reposição", len(itens_baixos), delta_color="inverse")

            # --- NOVIDADE: SEÇÃO DE COMPRAS DIRETAS ---
            if len(itens_baixos) > 0:
                with st.expander("🛒 COMPRA RÁPIDA (Itens com estoque baixo)", expanded=True):
                    st.write("Selecione um item para buscar fornecedores online:")
                    
                    # Lista apenas os nomes dos itens que precisam de compra
                    item_para_comprar = st.selectbox("Substância para repor:", itens_baixos['nome'].unique())
                    
                    if item_para_comprar:
                        # Criamos a URL de busca (Google Shopping e Sigma-Aldrich)
                        query = urllib.parse.quote(item_para_comprar)
                        
                        c1, c2, c3 = st.columns(3)
                        # Links diretos que abrem em nova aba
                        c1.link_button("🔍 Buscar no Google Shopping", f"https://www.google.com/search?q={query}&tbm=shop")
                        c2.link_button("🧪 Buscar na Sigma-Aldrich", f"https://www.sigmaaldrich.com/BR/pt/search/{query}")
                        c3.link_button("📦 Buscar na Amazon", f"https://www.amazon.com.br/s?k={query}")

            st.divider()

            # --- TABELA DE EDIÇÃO ---
            st.subheader("📝 Edição do Inventário")
            edited_df = st.data_editor(df, use_container_width=True, hide_index=True)

            if st.button("💾 Salvar Alterações"):
                edited_df.to_sql('substancias', conn, if_exists='replace', index=False)
                st.success("Estoque atualizado!")
                st.rerun()

        else:
            st.warning("O banco de dados está vazio.")

    except Exception as e:
        st.error(f"Erro: {e}")
    finally:
        if conn: conn.close()

    # --- BUSCA GERAL NA INTERNET ---
    st.divider()
    st.subheader("🌐 Pesquisa Externa")
    busca_livre = st.text_input("Procurar qualquer reagente para compra:")
    if busca_livre:
        q_livre = urllib.parse.quote(busca_livre)
        st.link_button(f"Comprar {busca_livre} agora", f"https://www.google.com/search?q=comprar+{q_livre}")