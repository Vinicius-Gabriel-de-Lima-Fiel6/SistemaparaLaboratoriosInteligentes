import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

# Caminho do banco de dados (mesmo do seu arquivo de substâncias)
DB_PATH = "data/lab_data.db"

def show_reports():
    st.title("📊 Central de Dados: Importação e Relatórios")
    
    # --- SEÇÃO 1: IMPORTAR DADOS (GRAVAR NO BANCO) ---
    st.header("📥 Importar Planilha para o Banco")
    st.info("O arquivo deve ter as colunas: nome, finalidade, concentracao, quantidade, validade")
    
    uploaded_file = st.file_uploader("Escolha o arquivo CSV ou Excel", type=['csv', 'xlsx'])

    if uploaded_file is not None:
        try:
            # Lendo o arquivo
            if uploaded_file.name.endswith('.csv'):
                df_importado = pd.read_csv(uploaded_file)
            else:
                df_importado = pd.read_excel(uploaded_file)

            st.subheader("Pré-visualização dos dados importados:")
            st.dataframe(df_importado.head(), use_container_width=True)

            if st.button("🚀 Confirmar Importação para o Banco de Dados"):
                conn = sqlite3.connect(DB_PATH)
                # 'append' adiciona os novos dados sem apagar os que já existem no banco
                df_importado.to_sql('substancias', conn, if_exists='append', index=False)
                conn.close()
                
                st.success(f"✅ Sucesso! {len(df_importado)} itens salvos permanentemente no banco de dados.")
                st.balloons()
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

    st.divider()

    # --- SEÇÃO 2: GERAR RELATÓRIOS (LER DO BANCO) ---
    st.header("📤 Gerar Relatórios (Exportar)")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df_export = pd.read_sql_query("SELECT * FROM substancias", conn)
        conn.close()

        if not df_export.empty:
            st.write(f"Total de itens no banco: {len(df_export)}")
            st.dataframe(df_export, use_container_width=True)

            col1, col2 = st.columns(2)
            
            with col1:
                # Exportar o banco atual para Excel (CSV)
                csv = df_export.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 Baixar Banco Atual (Excel/CSV)", 
                    csv, 
                    "relatorio_laboratorio.csv", 
                    "text/csv", 
                    use_container_width=True
                )

            with col2:
                st.info("Para gerar PDF formatado, certifique-se de ter o 'reportlab' instalado.")
        else:
            st.warning("O banco de dados está vazio. Importe dados acima para gerar relatórios.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados para relatório: {e}")