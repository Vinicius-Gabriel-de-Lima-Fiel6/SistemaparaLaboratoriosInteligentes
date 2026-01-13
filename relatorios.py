import streamlit as st
import pandas as pd
from supabase import create_client
import io

# --- CONEXÃO COM O BANCO (Mantendo o padrão do seu app.py) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_reports():
    # 1. Recuperar dados do usuário logado para filtro
    user = st.session_state.user_data
    org_atual = user.get('org_name')

    st.title("📊 Central de Inteligência e Relatórios")
    st.markdown(f"**Organização:** {org_atual} | **Analista:** {user['username']}")

    # --- ABA DE NAVEGAÇÃO INTERNA ---
    aba_import, aba_export, aba_analise = st.tabs(["📥 Importar Dados", "📤 Exportar Relatórios", "📈 Visão Analítica"])

    # --- SEÇÃO 1: IMPORTAR DADOS (Respeitando sua estrutura original) ---
    with aba_import:
        st.header("📥 Importação em Massa")
        st.info("Certifique-se que o arquivo possui: nome, finalidade, concentracao, quantidade, validade")
        
        uploaded_file = st.file_uploader("Escolha CSV ou Excel", type=['csv', 'xlsx'], key="rep_import")

        if uploaded_file:
            try:
                df_import = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                
                # INJEÇÃO AUTOMÁTICA DA EMPRESA (Segurança)
                df_import['org_name'] = org_atual
                
                st.subheader("Pré-visualização (Primeiras 5 linhas)")
                st.dataframe(df_import.head(), use_container_width=True)

                if st.button("🚀 Confirmar Carga para Nuvem"):
                    with st.spinner("Gravando no banco de dados..."):
                        data_to_save = df_import.to_dict(orient='records')
                        supabase.table("substancias").insert(data_to_save).execute()
                        st.success(f"✅ {len(df_import)} itens integrados ao estoque da {org_atual}!")
                        st.balloons()
            except Exception as e:
                st.error(f"Erro na importação: {e}")

    # --- SEÇÃO 2: GERAR RELATÓRIOS (Potencializado com Filtros) ---
    with aba_export:
        st.header("📤 Exportação de Dados")
        
        try:
            # Busca apenas dados da empresa logada
            res = supabase.table("substancias").select("*").eq("org_name", org_atual).execute()
            df_export = pd.DataFrame(res.data)

            if not df_export.empty:
                # FILTROS DINÂMICOS
                st.subheader("Filtros de Exportação")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    filtro_nome = st.multiselect("Filtrar por Substância:", options=df_export['nome'].unique())
                with col_f2:
                    status_validade = st.checkbox("Mostrar apenas itens vencidos")

                # Aplicando Filtros
                df_filtrado = df_export.copy()
                if filtro_nome:
                    df_filtrado = df_filtrado[df_filtrado['nome'].isin(filtro_nome)]
                if status_validade:
                    df_filtrado['validade'] = pd.to_datetime(df_filtrado['validade'])
                    df_filtrado = df_filtrado[df_filtrado['validade'] < pd.Timestamp.now()]

                st.dataframe(df_filtrado, use_container_width=True)

                # BOTÕES DE DOWNLOAD
                st.divider()
                c1, c2, c3 = st.columns(3)
                
                # CSV
                csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
                c1.download_button("📥 Baixar CSV/Excel", csv, "relatorio_lab.csv", "text/csv", use_container_width=True)
                
                # JSON (Para integração de sistemas)
                json_data = df_filtrado.to_json(orient='records')
                c2.download_button("📥 Baixar JSON", json_data, "dados_lab.json", "application/json", use_container_width=True)

                # INFO PDF
                c3.info("PDF: Utilize 'Imprimir' do navegador para PDF formatado.")

            else:
                st.warning("Nenhum dado encontrado para sua organização.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

    # --- SEÇÃO 3: VISÃO ANALÍTICA (O Diferencial) ---
    with aba_analise:
        st.header("📈 Resumo Estatístico")
        if not df_export.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Valor Total em Estoque (Qtd)", f"{df_export['quantidade'].sum():.0f}")
            m2.metric("Variedade de Itens", len(df_export))
            
            # Cálculo de itens próximos ao vencimento
            df_export['validade'] = pd.to_datetime(df_export['validade'])
            em_alerta = len(df_export[df_export['validade'] < pd.Timestamp.now() + pd.Timedelta(days=30)])
            m3.metric("Alertas de Validade", em_alerta, delta="30 dias", delta_color="inverse")

            st.subheader("Distribuição por Finalidade")
            st.bar_chart(df_export['finalidade'].value_counts())
        else:
            st.info("Sem dados para gerar estatísticas.")

# Para execução direta se necessário
if __name__ == "__main__":
    show_reports()
