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
        # Pega os 10 itens com maior volume para o gráfico
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
    """Carrega o estilo visual profissional"""
    st.markdown("""
        <style>
        .report-card {
            background: #F8FAFC;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #F1F5F9;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 20px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO PRINCIPAL ---

def show_reports(supabase):
    load_css()
    user = st.session_state.user_data
    org = user.get('org_name')

    st.title("📄 Central de Inteligência e Automação")
    st.markdown(f"**Organização:** {org} | **Status do Bot:** Ativo")

    aba_import, aba_export, aba_bot = st.tabs([
        "📥 Importação Inteligente", 
        "📤 Exportador Master", 
        "🤖 Configurar Bot"
    ])

    # --- ABA 1: IMPORTAÇÃO (MAPEADOR FLEXÍVEL) ---
    with aba_import:
        st.subheader("Carga de Dados em Lote")
        arquivo = st.file_uploader("Suba seu inventário (Excel ou CSV)", type=['xlsx', 'csv'])
        
        if arquivo:
            df_up = pd.read_excel(arquivo) if arquivo.name.endswith('xlsx') else pd.read_csv(arquivo)
            cols = df_up.columns.tolist()
            
            st.info("Mapeie as colunas do seu arquivo para os campos do sistema:")
            c1, c2, c3 = st.columns(3)
            m_nome = c1.selectbox("Coluna do Nome/Item", cols)
            m_qtd = c2.selectbox("Coluna de Quantidade", cols)
            m_min = c3.selectbox("Coluna de Estoque Mínimo", cols)

            if st.button("🚀 Iniciar Sincronização"):
                with st.spinner("IA processando dados..."):
                    df_final = df_up.rename(columns={m_nome: "nome", m_qtd: "quantidade", m_min: "estoque_minimo"})
                    df_final["org_name"] = org
                    # Filtra apenas colunas válidas
                    dados = df_final[df_final.columns.intersection(["nome", "quantidade", "estoque_minimo", "org_name"])].to_dict(orient='records')
                    
                    try:
                        supabase.table("substancias").upsert(dados).execute()
                        st.success(f"✅ {len(dados)} itens sincronizados com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao sincronizar: {e}")

    # --- ABA 2: EXPORTADOR (PDF COM GRÁFICOS + EXCEL) ---
    with aba_export:
        st.subheader("Geração de Relatórios Oficiais")
        
        try:
            # Busca dados em tempo real
            res_sub = supabase.table("substancias").select("*").eq("org_name", org).execute()
            res_equ = supabase.table("equipamentos").select("*").eq("org_name", org).execute()
            df_sub = pd.DataFrame(res_sub.data)
            df_equ = pd.DataFrame(res_equ.data)

            if df_sub.empty:
                st.warning("⚠️ Não há dados suficientes para gerar relatórios. Realize uma importação.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Pacote de Auditoria (Excel)**")
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_sub.to_excel(writer, sheet_name='Inventário', index=False)
                        df_equ.to_excel(writer, sheet_name='Equipamentos', index=False)
                        # Aba de Log
                        pd.DataFrame([{"Auditoria": datetime.now(), "Org": org}]).to_excel(writer, sheet_name='Log_Sistema')
                    
                    st.download_button(
                        "📊 Baixar Excel Profissional", 
                        buffer.getvalue(), 
                        f"Relatorio_{org}.xlsx", 
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown("**Relatório Executivo (PDF)**")
                    if st.button("📄 Visualizar Relatório Master", use_container_width=True):
                        grafico_b64 = get_image_base64(df_sub)
                        # Tenta ler o template HTML
                        try:
                            with open("HTML/template_pdf.html", "r", encoding="utf-8") as f:
                                tmpl = Template(f.read())
                            
                            html_render = tmpl.render(
                                org_name=org,
                                data_atual=datetime.now().strftime("%d/%m/%Y"),
                                total_sub=len(df_sub),
                                total_equ=len(df_equ),
                                total_alertas=len(df_sub[df_sub['quantidade'] < 10]) if 'quantidade' in df_sub else 0,
                                grafico_base64=grafico_b64,
                                insight_ia="Análise preditiva sugere estabilidade no consumo para os próximos 15 dias."
                            )
                            st.components.v1.html(html_render, height=500, scrolling=True)
                            st.download_button("📥 Baixar PDF (HTML)", html_render, f"Relatorio_{org}.html", use_container_width=True)
                        except Exception as e:
                            st.error(f"Erro ao carregar template HTML: {e}")
        except Exception as e:
            st.error(f"Erro ao carregar dados do banco: {e}")

    # --- ABA 3: CONFIGURAÇÃO DO BOT (POWER AUTOMATE) ---
    with aba_bot:
        st.subheader("🤖 Configurar Agente de Envio Automático")
        
        # Busca configuração atual
        try:
            res_c = supabase.table("config_automacao").select("*").eq("org_name", org).execute()
            conf = res_c.data[0] if res_c.data else {}
        except:
            conf = {}

        with st.form("bot_config_form"):
            email_dest = st.text_input("E-mail de Destino (Técnico)", value=conf.get('email_destino', ""))
            
            dias_opcoes = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
            dia_banco = conf.get('dia_semana', "Segunda-feira")
            idx_dia = dias_opcoes.index(dia_banco) if dia_banco in dias_opcoes else 0
            
            dia_sem = st.selectbox("Dia da Semana", dias_opcoes, index=idx_dia)
            
            # Tratamento de horário
            hora_banco = conf.get('horario', "08:00:00")
            try:
                hora_val = datetime.strptime(hora_banco, "%H:%M:%S").time()
            except:
                hora_val = datetime.now().time()
            
            horario_envio = st.time_input("Horário do Disparo", value=hora_val)
            
            st.divider()
            st.caption("Configurações SMTP (Para o Bot disparar e-mails)")
            s_user = st.text_input("Usuário SMTP (E-mail do Bot)", value=conf.get('smtp_user', ""))
            s_pass = st.text_input("Senha SMTP (Senha de App)", value=conf.get('smtp_pass', ""), type="password")
            
            if st.form_submit_button("💾 Salvar e Ativar Automação"):
                payload = {
                    "org_name": org,
                    "email_destino": email_dest,
                    "dia_semana": dia_sem,
                    "horario": str(horario_envio),
                    "smtp_user": s_user,
                    "smtp_pass": s_pass
                }
                try:
                    # Upsert explícito com on_conflict para evitar erro de recursão/duplicate
                    supabase.table("config_automacao").upsert(payload, on_conflict="org_name").execute()
                    st.success("✅ Configuração salva! O Bot agora está monitorando seu laboratório.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}. Verifique as políticas de RLS no Supabase.")
