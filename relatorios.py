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
        st.subheader("🤖 Agente de Automação")
        
        # Busca a configuração com tratamento de erro
        try:
            res_config = supabase.table("config_automacao").select("*").eq("org_name", org).execute()
            config_existente = res_config.data
        except Exception:
            config_existente = []

        default_data = config_existente[0] if config_existente else {}

        with st.form("config_bot_form"):
            email_dest = st.text_input("E-mail de Destino", value=default_data.get('email_destino', ""))
            
    
            dias_lista = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
            
     
            dia_no_banco = default_data.get('dia_semana', "Segunda-feira")
            try:
                idx_dia = dias_lista.index(dia_no_banco)
            except ValueError:
                idx_dia = 0

            dia_sem = st.selectbox("Dia da Semana", dias_lista, index=idx_dia)
            
         
            hora_str = default_data.get('horario', "08:00:00")
            try:
                # Se vier do banco como "08:00:00", converte para objeto time
                hora_val = datetime.strptime(hora_str, "%H:%M:%S").time()
            except:
                hora_val = datetime.now().time()

            horario_envio = st.time_input("Horário do Disparo", value=hora_val)
            
            st.divider()
            st.caption("Configurações SMTP (Para o Bot enviar o e-mail)")
            s_user = st.text_input("Usuário SMTP (E-mail)", value=default_data.get('smtp_user', ""))
            s_pass = st.text_input("Senha SMTP", value=default_data.get('smtp_pass', ""), type="password")
            
            if st.form_submit_button("💾 Salvar Configuração"):
                payload = {
                    "org_name": org,
                    "email_destino": email_dest,
                    "dia_semana": dia_sem,
                    "horario": str(horario_envio),
                    "smtp_user": s_user,
                    "smtp_pass": s_pass
                }
                try:
        # Adicionamos on_conflict para dizer que se o org_name já existir, ele deve atualizar
                    supabase.table("config_automacao").upsert(payload, on_conflict="org_name").execute()
                    st.success("✅ Automação salva com sucesso!")
                except Exception as e:
                    st.error(f"Erro na API do Banco: {e}")


