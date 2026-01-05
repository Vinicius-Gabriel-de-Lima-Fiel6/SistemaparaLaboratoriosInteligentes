import streamlit as st
import sqlite3
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime

DB_PATH = "data/lab_data.db"

def init_db():
    """Inicializa as tabelas de equipamentos e manutenção"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabela de Equipamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, tipo TEXT, status TEXT, 
            ultima_manutencao TEXT, localizacao TEXT, 
            responsavel TEXT, categoria TEXT
        )
    """)
    # Tabela de Manutenções
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id INTEGER,
            data_manutencao TEXT,
            descricao TEXT,
            FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
        )
    """)
    conn.commit()
    conn.close()

def show_equipamentos():
    init_db()
    st.title("🔧 Controle de Equipamentos e Manutenção")

    # --- 1. CADASTRO DE EQUIPAMENTOS ---
    with st.expander("➕ Adicionar Novo Equipamento", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome do Equipamento")
            tipo = st.text_input("Tipo")
        with col2:
            status = st.selectbox("Status", ["Operacional", "Manutenção", "Fora de Uso", "Calibração"])
            u_manut = st.date_input("Última Manutenção").strftime("%d/%m/%Y")
        with col3:
            local = st.text_input("Localização")
            resp = st.text_input("Responsável")
        
        cat = st.text_input("Categoria")

        if st.button("Salvar Equipamento"):
            if nome:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO equipamentos (nome, tipo, status, ultima_manutencao, localizacao, responsavel, categoria)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (nome, tipo, status, u_manut, local, resp, cat))
                conn.commit()
                conn.close()
                st.success(f"Equipamento {nome} cadastrado!")
                st.rerun()

    # --- 2. REGISTRO DE MANUTENÇÃO ---
    st.divider()
    with st.expander("🛠️ Registrar Nova Manutenção"):
        conn = sqlite3.connect(DB_PATH)
        df_eq = pd.read_sql_query("SELECT id, nome FROM equipamentos", conn)
        conn.close()

        if not df_eq.empty:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                eq_escolhido = st.selectbox("Selecione o Equipamento", df_eq['nome'].tolist())
                eq_id = df_eq[df_eq['nome'] == eq_escolhido]['id'].values[0]
            with col_m2:
                data_m = st.date_input("Data da Manutenção", key="data_m").strftime("%d/%m/%Y")
            
            desc_m = st.text_area("Descrição do Serviço")

            if st.button("Confirmar Manutenção"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO manutencao (equipamento_id, data_manutencao, descricao) VALUES (?, ?, ?)",
                             (int(eq_id), data_m, desc_m))
                # Atualiza a data de última manutenção no cadastro do equipamento
                cursor.execute("UPDATE equipamentos SET ultima_manutencao = ? WHERE id = ?", (data_m, int(eq_id)))
                conn.commit()
                conn.close()
                st.success("Manutenção registrada!")
                st.rerun()
        else:
            st.info("Cadastre um equipamento primeiro.")

    # --- 3. VISUALIZAÇÃO DE DADOS E GRÁFICOS ---
    st.divider()
    tab1, tab2, tab3 = st.tabs(["📋 Inventário", "📜 Histórico", "📊 Gráficos"])

    conn = sqlite3.connect(DB_PATH)
    
    with tab1:
        df_view = pd.read_sql_query("SELECT * FROM equipamentos", conn)
        if not df_view.empty:
            # Busca rápida integrada
            busca = st.text_input("🔍 Pesquisar por nome ou responsável:")
            if busca:
                df_view = df_view[df_view['nome'].str.contains(busca, case=False) | df_view['responsavel'].str.contains(busca, case=False)]
            
            edited_df = st.data_editor(df_view, use_container_width=True, hide_index=True)
            
            if st.button("💾 Salvar Alterações na Tabela"):
                edited_df.to_sql('equipamentos', conn, if_exists='replace', index=False)
                st.success("Dados atualizados!")
        else:
            st.write("Nenhum equipamento cadastrado.")

    with tab2:
        df_hist = pd.read_sql_query("""
            SELECT m.id, e.nome as Equipamento, m.data_manutencao as Data, m.descricao as Descricao 
            FROM manutencao m 
            JOIN equipamentos e ON m.equipamento_id = e.id
        """, conn)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

    with tab3:
        if not df_view.empty:
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.write("**Equipamentos por Status**")
                status_count = df_view['status'].value_counts()
                fig1, ax1 = plt.subplots()
                ax1.pie(status_count, labels=status_count.index, autopct='%1.1f%%', startangle=90)
                st.pyplot(fig1)

            with col_g2:
                st.write("**Equipamentos por Tipo**")
                tipo_count = df_view['tipo'].value_counts()
                st.bar_chart(tipo_count)
    
    conn.close()

    # --- 4. EXPORTAÇÃO ---
    st.sidebar.divider()
    if st.sidebar.button("📄 Gerar Relatório CSV"):
        df_full = pd.read_sql_query("SELECT * FROM equipamentos", sqlite3.connect(DB_PATH))
        csv = df_full.to_csv(index=False).encode('utf-8-sig')
        st.sidebar.download_button("Clique para Baixar CSV", csv, "equipamentos.csv", "text/csv")