import streamlit as st
import pandas as pd
import io
import os
import base64
import matplotlib.pyplot as plt
from datetime import datetime
from jinja2 import Template

# --- FUNÇÕES DE APOIO ---

def get_image_base64(df):
    """Gera gráfico para o PDF e converte em Base64"""
    if df.empty or 'quantidade' not in df.columns:
        return ""
    try:
        plt.figure(figsize=(8, 4))
        df_plot = df.nlargest(10, 'quantidade') 
        plt.bar(df_plot['nome'], df_plot['quantidade'], color='#1E3A8A')
        plt.title("Níveis de Estoque (Top 10)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except:
        return ""

def load_css():
    """Estilização Profissional"""
    st.markdown("""
        <style>
        .main-card {
            background: #FFFFFF;
            padding: 25px;
            border-radius: 15px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO PRINCIPAL ---

def show_reports(supabase):
    load_css()
    user = st.session_state.user_data
    org = user.get('org_name')

    st.title("📄 Central de Automação e Auditoria")
    
    aba_import, aba_export, aba_bot = st.tabs([
        "📥 Importador Inteligente", 
        "📤 Exportador Master", 
        "🤖 Configurar Bot (Scheduler)"
    ])

    # --- ABA 1: IMPORTAÇÃO ---
    with aba_import:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("Importação de Dados em Lote")
        arquivo = st.file_uploader("Upload de Inventário (Excel/CSV)", type=['xlsx', 'csv'])
        
        if arquivo:
            df_up = pd.read_excel(arquivo) if arquivo.name.endswith('xlsx') else pd.read_csv(arquivo)
            cols = df_up.columns.tolist()
            
            st.write("🔗 **Mapeamento de Colunas:**")
            c1, c2, c3 = st.columns(3)
            m_nome = c1.selectbox("Nome do Item", cols)
            m_qtd = c2.selectbox("Quantidade", cols)
            m_min = c3.selectbox("Estoque Mínimo", cols)

            if st.button("🚀 Sincronizar com Banco de Dados"):
                df_f = df_up.rename(columns={m_nome: "nome", m_qtd: "quantidade", m_min: "estoque_minimo"})
                df_f["org_name"] = org
                dados = df_f[df_f.columns.intersection(["nome", "quantidade", "estoque_minimo", "org_name"])].to_dict(orient='records')
                
                try:
                    supabase.table("substancias").upsert(dados).execute()
                    st.success(f"✅ {len(dados)} itens atualizados!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA 2: EXPORTAÇÃO ---
    with aba_export:
        try:
            res_sub = supabase.table("substancias").select("*").eq("org_name", org).execute()
            res_equ = supabase.table("equipamentos").select("*").eq("org_name", org).execute()
            df_sub = pd.DataFrame(res_sub.data)
            df_equ = pd.DataFrame(res_equ.data)

            if df_sub.empty:
                st.warning("⚠️ Adicione dados para liberar a exportação.")
            else:
                st.markdown('<div class="main-card">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Relatório de Dados (Excel)**")
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_sub.to_excel(writer, sheet_name='Estoque', index=False)
                        df_equ.to_excel(writer, sheet_name='Maquinário', index=False)
                    st.download_button("📊 Baixar Excel Master", buffer.getvalue(), f"Auditoria_{org}.xlsx", use_container_width=True)
                
                with col2:
                    st.write("**Relatório Executivo (PDF)**")
                    if st.button("📄 Gerar Visualização PDF"):
                        grafico = get_image_base64(df_sub)
                        with open("HTML/template_pdf.html", "r", encoding="utf-8") as f:
                            tmpl = Template(f.read())
                        html = tmpl.render(org_name=org, data_atual=datetime.now().strftime("%d/%m/%Y"),
                                         total_sub=len(df_sub), total_equ=len(df_equ),
                                         total_alertas=len(df_sub[df_sub['quantidade'] < 10]),
                                         grafico_base64=grafico, insight_ia="Auditoria processada.")
                        st.components.v1.html(html, height=500, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

    # --- ABA 3: CONFIGURAÇÃO DO BOT (TABELA bot_scheduler) ---
    with aba_bot:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("🤖 Configurar Bot Agendador")
        st.write("Defina o envio automático de relatórios para o técnico responsável.")
        
        # Tenta buscar config existente na nova tabela
        try:
            res_bot = supabase.table("bot_scheduler").select("*").eq("org_name", org).execute()
            b_conf = res_bot.data[0] if res_bot.data else {}
        except:
            b_conf = {}

        with st.form("form_bot_scheduler"):
            email_tecnico = st.text_input("E-mail do Técnico Destinatário", value=b_conf.get('email_destino', ""))
            
            dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
            dia_idx = dias.index(b_conf.get('dia_semana', "Segunda-feira")) if b_conf.get('dia_semana') in dias else 0
            
            c1, c2 = st.columns(2)
            dia_envio = c1.selectbox("Dia do Envio", dias, index=dia_idx)
            
            hora_banco = b_conf.get('horario', "08:00:00")
            hora_val = datetime.strptime(hora_banco, "%H:%M:%S").time() if isinstance(hora_banco, str) else datetime.now().time()
            horario = c2.time_input("Horário do Disparo", value=hora_val)
            
            st.divider()
            st.write("🔑 **Configuração de Disparo (SMTP)**")
            smtp_user = st.text_input("E-mail de Envio (Bot)", value=b_conf.get('smtp_user', ""))
            smtp_pass = st.text_input("Senha de App (SMTP)", value=b_conf.get('smtp_pass', ""), type="password")
            
            if st.form_submit_button("💾 SALVAR E ATIVAR BOT"):
                payload = {
                    "org_name": org,
                    "email_destino": email_tecnico,
                    "dia_semana": dia_envio,
                    "horario": str(horario),
                    "smtp_user": smtp_user,
                    "smtp_pass": smtp_pass,
                    "ativo": True
                }
                try:
                    # UPSERT na nova tabela (Independente de RLS de usuários)
                    supabase.table("bot_scheduler").upsert(payload, on_conflict="org_name").execute()
                    st.success("✅ Automação salva com sucesso na tabela bot_scheduler!")
                except Exception as e:
                    st.error(f"Erro ao salvar automação: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
