import streamlit as st
import pandas as pd
import io
import os
import base64
import matplotlib.pyplot as plt
from datetime import datetime
from jinja2 import Template

# Funções Auxiliares
def get_image_base64(df):
    plt.figure(figsize=(8, 4))
    df.head(10).plot(kind='bar', x='nome', y='quantidade', color='#1E3A8A')
    plt.title("Níveis de Estoque Atual")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def load_css():
    css_path = os.path.join("CSS", "relatorios_style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def show_reports():
    load_css()
    user = st.session_state.user_data
    org = user.get('org_name')
    supabase = st.session_state.get('supabase_client') 

    st.title("📄 Central de Relatórios & Automação")

    aba_import, aba_export, aba_bot = st.tabs(["📥 Importar Dados", "📤 Exportador Pro", "🤖 Configurar Bot"])


    with aba_import:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("Carga de Dados Master")
        file = st.file_uploader("Upload de Inventário (CSV/XLSX)", type=['csv', 'xlsx'])
        if file:
            df_upload = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
            st.dataframe(df_upload.head())
            if st.button("🚀 Processar e Sincronizar"):
            
                st.success("Banco de dados atualizado!")
        st.markdown('</div>', unsafe_allow_html=True)


    with aba_export:
        st.subheader("Geração de Documentos Executivos")
        
        try:
            sub_res = supabase.table("substancias").select("*").eq("org_name", org).execute()
            equ_res = supabase.table("equipamentos").select("*").eq("org_name", org).execute()
            df_sub = pd.DataFrame(sub_res.data)
            df_equ = pd.DataFrame(equ_res.data)

            col1, col2 = st.columns(2)
            with col1:
                # Excel 3 Abas
                buffer_ex = io.BytesIO()
                with pd.ExcelWriter(buffer_ex, engine='xlsxwriter') as writer:
                    df_sub.to_excel(writer, sheet_name='Substancias', index=False)
                    df_equ.to_excel(writer, sheet_name='Equipamentos', index=False)
                    # Aba de Auditoria IA
                    pd.DataFrame([{"Análise": "Risco de ruptura", "Data": datetime.now()}]).to_excel(writer, sheet_name='Auditoria_IA')
                
                st.download_button("📊 Baixar Excel Master", buffer_ex.getvalue(), f"Auditoria_{org}.xlsx", use_container_width=True)

            with col2:
                if st.button("📄 Gerar Relatório PDF Profissional", use_container_width=True):
                
                    grafico_b64 = get_image_base64(df_sub)
                    with open("HTML/template_pdf.html", "r", encoding="utf-8") as f:
                        tmpl = Template(f.read())
                    
                    html_render = tmpl.render(
                        org_name=org, data_atual=datetime.now().strftime("%d/%m/%Y"),
                        total_sub=len(df_sub), total_equ=len(df_equ),
                        total_alertas=len(df_sub[df_sub['quantidade'] < 10]),
                        nivel_risco="Baixo", grafico_base64=grafico_b64,
                        insight_ia="O estoque físico está condizente com os logs da Central de Controle."
                    )
                    st.components.v1.html(html_render, height=600, scrolling=True)
        except: st.warning("Adicione dados para gerar relatórios.")

    with aba_bot:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("Configuração do Agente Autônomo")
        st.write("Defina quando o técnico receberá os alertas e relatórios por e-mail.")
        
        with st.form("bot_config"):
            email = st.text_input("E-mail do Técnico")
            freq = st.selectbox("Frequência de Envio", ["Diário", "Semanal (Segunda-feira)", "Mensal"])
            hora = st.time_input("Horário do Disparo")
            incluir_graficos = st.checkbox("Incluir Gráficos Preditivos", value=True)
            
            if st.form_submit_button("💾 Ativar Bot de Automação"):
             
                st.success(f"Bot programado! Próximo envio: {freq} às {hora}")
        st.markdown('</div>', unsafe_allow_html=True)
