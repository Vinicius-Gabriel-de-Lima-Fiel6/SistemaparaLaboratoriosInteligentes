import streamlit as st
import pandas as pd
from supabase import create_client
import io

# --- CONEXÃO COM O BANCO ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_reports():
    user = st.session_state.user_data
    org_atual = user.get('org_name')

    st.title("📊 Central de Inteligência e Relatórios")
    st.markdown(f"**Organização:** {org_atual} | **Analista:** {user['username']}")

    aba_import, aba_export, aba_analise = st.tabs(["📥 Importar Dados", "📤 Exportar Relatórios", "📈 Visão Analítica"])

    # --- SEÇÃO 1: IMPORTAR DADOS ---
    with aba_import:
        st.header("📥 Importação em Massa")
        uploaded_file = st.file_uploader("Escolha CSV ou Excel", type=['csv', 'xlsx'], key="rep_import")

        if uploaded_file:
            try:
                df_import = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                df_import['org_name'] = org_atual
                
                st.subheader("Pré-visualização")
                st.dataframe(df_import.head(), use_container_width=True)

                if st.button("🚀 Confirmar Carga para Nuvem"):
                    with st.spinner("Gravando no banco..."):
                        data_to_save = df_import.to_dict(orient='records')
                        supabase.table("substancias").insert(data_to_save).execute()
                        st.success(f"✅ Itens integrados com sucesso!")
                        st.balloons()
            except Exception as e:
                st.error(f"Erro na importação: {e}")

    try:
        res = supabase.table("substancias").select("*").eq("org_name", org_atual).execute()
        df_export = pd.DataFrame(res.data)

        if not df_export.empty:
        
          
            df_export['validade'] = df_export['validade'].astype(str)
     
            df_export['validade_dt'] = pd.to_datetime(df_export['validade'], errors='coerce', utc=True).dt.tz_localize(None)
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
        df_export = pd.DataFrame()

    # --- SEÇÃO 2: GERAR RELATÓRIOS ---
    with aba_export:
        st.header("📤 Exportação de Dados")
        if not df_export.empty:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_nome = st.multiselect("Filtrar por Substância:", options=df_export['nome'].unique(),placeholder="Escolha a opção")
            with col_f2:
                status_validade = st.checkbox("Mostrar apenas itens vencidos")

            df_filtrado = df_export.copy()
            if filtro_nome:
                df_filtrado = df_filtrado[df_filtrado['nome'].isin(filtro_nome)]
            if status_validade:
                # Usa a coluna limpa validade_dt para comparar
                df_filtrado = df_filtrado[df_filtrado['validade_dt'] < pd.Timestamp.now()]

            # Mostra a tabela limpando a coluna técnica de erro
            st.dataframe(df_filtrado.drop(columns=['validade_dt'], errors='ignore'), use_container_width=True)

            csv = df_filtrado.drop(columns=['validade_dt'], errors='ignore').to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar CSV/Excel", csv, "relatorio_lab.csv", "text/csv", use_container_width=True)
        else:
            st.warning("Nenhum dado encontrado.")

    # --- SEÇÃO 3: VISÃO ANALÍTICA ---
    with aba_analise:
        st.header("📈 Resumo Estatístico")
        if not df_export.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Quantidade Total", f"{df_export['quantidade'].sum():.0f}")
            m2.metric("Variedade de Itens", len(df_export))
            
            
            hoje = pd.Timestamp.now()
            vencimento_proximo = hoje + pd.Timedelta(days=30)
            
            # Conta apenas datas válidas (não nulas)
            em_alerta = len(df_export[(df_export['validade_dt'].notnull()) & (df_export['validade_dt'] < vencimento_proximo)])
            
            m3.metric("Alertas de Validade", em_alerta, delta="Próximos 30 dias", delta_color="inverse")

            st.subheader("Distribuição por Finalidade")
            st.bar_chart(df_export['finalidade'].value_counts())
        else:
            st.info("Sem dados para análise.")

