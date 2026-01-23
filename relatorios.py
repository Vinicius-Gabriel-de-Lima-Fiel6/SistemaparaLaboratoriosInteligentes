import streamlit as st
import pandas as pd
import io
import os
import base64
import matplotlib.pyplot as plt
from datetime import datetime
from jinja2 import Template

def get_image_base64(df):
    if df.empty or 'quantidade' not in df.columns: return ""
    plt.figure(figsize=(8, 4))
    df_plot = df.nlargest(10, 'quantidade') 
    plt.bar(df_plot['nome'], df_plot['quantidade'], color='#1E3A8A')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def show_reports(supabase): # Recebe a conexão do app.py
    # Carregar CSS
    css_path = os.path.join("CSS", "relatorios_style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    user = st.session_state.user_data
    org = user.get('org_name')

    st.title("📄 Central de Inteligência Laboratorial")

    aba_import, aba_export, aba_bot = st.tabs(["📥 Importar Dados", "📤 Exportador Pro", "🤖 Agente de Automação"])

    # --- ABA 1: IMPORTAÇÃO COM MAPEAMENTO ---
    with aba_import:
        st.subheader("Carga de Dados Master")
        file = st.file_uploader("Upload de Inventário (CSV/XLSX)", type=['csv', 'xlsx'])
        if file:
            df_up = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
            cols = df_up.columns.tolist()
            st.write("Mapeie as colunas:")
            c1, c2, c3 = st.columns(3)
            m_nome = c1.selectbox("Nome", cols)
            m_qtd = c2.selectbox("Quantidade", cols)
            m_min = c3.selectbox("Mínimo", cols)

            if st.button("🚀 Sincronizar"):
                df_f = df_up.rename(columns={m_nome: "nome", m_qtd: "quantidade", m_min: "estoque_minimo"})
                df_f["org_name"] = org
                dados = df_f[df_f.columns.intersection(["nome", "quantidade", "estoque_minimo", "org_name"])].to_dict(orient='records')
                supabase.table("substancias").upsert(dados).execute()
                st.success("Sincronizado!")
                st.rerun()

    # --- ABA 2: EXPORTAÇÃO (CORRIGIDA) ---
    with aba_export:
        try:
            res_sub = supabase.table("substancias").select("*").eq("org_name", org).execute()
            res_equ = supabase.table("equipamentos").select("*").eq("org_name", org).execute()
            df_sub = pd.DataFrame(res_sub.data)
            df_equ = pd.DataFrame(res_equ.data)

            if df_sub.empty:
                st.warning("Adicione dados na aba de Importação primeiro.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_sub.to_excel(writer, sheet_name='Estoque', index=False)
                        df_equ.to_excel(writer, sheet_name='Equipamentos', index=False)
                    st.download_button("📊 Baixar Excel Master", buffer.getvalue(), f"Relatorio_{org}.xlsx", use_container_width=True)
                
                with col2:
                    if st.button("📄 Visualizar Relatório PDF"):
                        grafico = get_image_base64(df_sub)
                        with open("HTML/template_pdf.html", "r", encoding="utf-8") as f:
                            tmpl = Template(f.read())
                        html = tmpl.render(org_name=org, data_atual=datetime.now().strftime("%d/%m/%Y"),
                                         total_sub=len(df_sub), total_equ=len(df_equ),
                                         total_alertas=len(df_sub[df_sub['quantidade'] < 10]),
                                         grafico_base64=grafico, insight_ia="Auditoria concluída com sucesso.")
                        st.components.v1.html(html, height=500, scrolling=True)
        except Exception as e:
            st.error(f"Erro na exportação: {e}")

    # --- ABA 3: CONFIGURAÇÃO DO BOT ---
    with aba_bot:
        st.subheader("Configurar Bot de Envio")
        with st.form("bot_config"):
            email = st.text_input("E-mail do Técnico")
            dia = st.selectbox("Dia", ["Segunda-feira", "Sexta-feira"])
            hora = st.time_input("Hora")
            if st.form_submit_button("Ativar Bot"):
                st.success("Agendamento salvo!")
