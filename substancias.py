import streamlit as st
import sqlite3
import os
import pandas as pd

# Mantemos o caminho exato do seu banco original
DB_PATH = "data/lab_data.db"

def init_db():
    """Cria o banco de dados e a tabela se não existirem (Lógica original)"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS substancias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            finalidade TEXT,
            concentracao TEXT,
            quantidade REAL,
            validade TEXT
        )
    """)
    conn.commit()
    conn.close()

def show_substances():
    """Esta é a função que o app.py vai chamar para exibir esta aba"""
    init_db()
    
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")

    # --- CAMPOS DE ENTRADA (Substitui QLineEdit) ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            nome = st.text_input("Nome da Substância")
            finalidade = st.text_input("Finalidade")
        with col2:
            concentracao = st.text_input("Concentração")
            quantidade = st.number_input("Quantidade", min_value=0.0)
        with col3:
            validade = st.text_input("Validade (MM/AAAA)")
            
        if st.button("➕ Adicionar Substância", use_container_width=True):
            if nome and quantidade:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO substancias (nome, finalidade, concentracao, quantidade, validade)
                    VALUES (?, ?, ?, ?, ?)
                """, (nome, finalidade, concentracao, quantidade, validade))
                conn.commit()
                conn.close()
                st.success(f"'{nome}' cadastrado!")
                st.rerun()
            else:
                st.error("Preencha ao menos Nome e Quantidade.")

    st.divider()

    # --- TABELA DE DADOS (Substitui QTableWidget) ---
    st.subheader("📋 Inventário Atual")
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM substancias", conn)
    conn.close()

    if not df.empty:
        # Exibição reativa
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Ações de remoção
        with st.expander("🗑️ Excluir Itens"):
            id_del = st.number_input("Digite o ID para remover", min_value=int(df['id'].min()), step=1)
            if st.button("Confirmar Exclusão", type="primary"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM substancias WHERE id = ?", (id_del,))
                conn.commit()
                conn.close()
                st.warning(f"Item {id_del} removido.")
                st.rerun()
    else:
        st.info("Nenhuma substância encontrada no banco de dados.")