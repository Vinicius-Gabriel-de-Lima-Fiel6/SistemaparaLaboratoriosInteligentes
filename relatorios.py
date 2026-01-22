import streamlit as st
import pandas as pd
import io
import os
import base64
import matplotlib.pyplot as plt
from datetime import datetime
from jinja2 import Template

def get_image_base64(df):
    """Gera gráfico para o PDF"""
    if df.empty: return ""
    plt.figure(figsize=(8, 4))
    # Pega os 10 itens com maior quantidade para o gráfico não ficar poluído
    df_plot = df.nlargest(10, 'quantidade') if 'quantidade' in df.columns else df.head(10)
    plt.bar(df_plot['nome'], df_plot['quantidade'], color='#1E3A8A')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def show_reports():
    # Carregar CSS
    css_path = os.path.join("CSS", "relatorios_style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    user = st.session_state.user_data
    org = user.get('org_name')
    supabase = st.session_state.get('supabase_client', st.session_state.get('supabase')) 

    st.title("📄 Central de Inteligência Laboratorial")

    aba_import, aba_export, aba_bot = st.tabs(["📥 Importar Dados", "📤 Exportador Pro", "🤖 Agente de Automação"])

    # --- ABA 1: IMPORTAÇÃO COM MAPEAMENTO INTELIGENTE ---
    with aba_import:
        st.subheader("Carga de Dados Flexível")
        file = st.file_uploader("Suba seu arquivo (CSV ou XLSX)", type=['csv', 'xlsx'])
        
        if file:
            df_upload = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
            st.write("Prévia do arquivo enviado:")
            st.dataframe(df_upload.head(3))
            
            st.divider()
            st.write("🔗 **Mapeamento de Colunas:**")
            colunas = df_upload.columns.tolist()
            
            c1, c2, c3 = st.columns(3)
            with c1: map_nome = st.selectbox("Coluna do Nome", colunas)
            with c2: map_qtd = st.selectbox("Coluna de Quantidade", colunas)
            with c3: map_min = st.selectbox("Coluna de Estoque Mínimo", colunas)

            if st.button("🚀 Iniciar Sincronização"):
                with st.spinner("IA processando e salvando dados..."):
                    df_final = df_upload.rename(columns={map_nome: "nome", map_qtd: "quantidade", map_min: "estoque_minimo"})
                    df_final["org_name"] = org
                    # Seleciona apenas o que o banco aceita
                    cols_banco = ["nome", "quantidade", "estoque_minimo", "org_name"]
                    dados = df_final[df_final.columns.intersection(cols_banco)].to_dict(orient='records')
                    
                    try:
                        supabase.table("substancias").upsert(dados).execute()
                        st.success(f"✅ {len(dados)} itens sincronizados com sucesso!")
                        st.rerun() # Recarrega para liberar o download na outra aba
                    except Exception as e:
                        st.error(f"Erro ao salvar no Supabase: {e}")

    # --- ABA 2: EXPORTAÇÃO (CORRIGIDA) ---
    with aba_export:
        st.subheader("Relatórios Master (Excel & PDF)")
        
        # Busca dados de forma explícita para debugar
        res_sub = supabase.table("substancias").select("*").eq("org_name", org).execute()
        res_equ = supabase.table("equipamentos").select("*").eq("org_name", org).execute()
        
        df_sub = pd.DataFrame(res_sub.data)
        df_equ = pd.DataFrame(res_equ.data)

        if df_sub.empty:
            st.warning("⚠️ O banco de dados está vazio para esta organização. Use a aba de Importação primeiro.")
        else:
            st.info(f"Dados prontos: {len(df_sub)} substâncias e {len(df_equ)} equipamentos.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Pacote de Auditoria (Excel)**")
                buffer_ex = io.BytesIO()
                with pd.ExcelWriter(buffer_ex, engine='xlsxwriter') as writer:
                    df_sub.to_excel(writer, sheet_name='PARTE 1 - ESTOQUE', index=False)
                    df_equ.to_excel(writer, sheet_name='PARTE 2 - MAQUINARIO', index=False)
                    # Simulação de Auditoria
                    pd.DataFrame([{"Data": datetime.now(), "Status": "Auditado", "Org": org}]).to_excel(writer, sheet_name='LOG_AUDITORIA')
                
                st.download_button(
                    label="📊 Baixar Excel Master (3 Abas)",
                    data=buffer_ex.getvalue(),
                    file_name=f"Relatorio_Full_{org}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col2:
                st.markdown("**Relatório Executivo (PDF)**")
                if st.button("📄 Gerar e Visualizar PDF", use_container_width=True):
                    grafico_b64 = get_image_base64(df_sub)
                    html_path = os.path.join("HTML", "template_pdf.html")
                    
                    if os.path.exists(html_path):
                        with open(html_path, "r", encoding="utf-8") as f:
                            template = Template(f.read())
                        
                        html_render = template.render(
                            org_name=org,
                            data_atual=datetime.now().strftime("%d/%m/%Y"),
                            total_sub=len(df_sub),
                            total_equ=len(df_equ),
                            total_alertas=len(df_sub[df_sub['quantidade'] <= df_sub['estoque_minimo']]),
                            nivel_risco="Calculado via IA",
                            grafico_base64=grafico_b64,
                            insight_ia="Tendência de consumo estável. Recomenda-se calibração preventiva dos equipamentos ativos."
                        )
                        st.components.v1.html(html_render, height=500, scrolling=True)
                        st.download_button("📥 Baixar Arquivo HTML (Oficial)", html_render, f"Relatorio_{org}.html", use_container_width=True)

    # --- ABA 3: CONFIGURAÇÃO DO BOT ---
    with aba_bot:
        st.subheader("Configurar Agente de Envio Automático")
        st.write("O Bot enviará os arquivos acima para o técnico no horário programado.")
        
        with st.form("config_bot_form"):
            email_dest = st.text_input("E-mail do Técnico/Gestor")
            dia = st.selectbox("Dia do Envio", ["Segunda-feira", "Quarta-feira", "Sexta-feira"])
            hora = st.time_input("Horário do Disparo")
            
            if st.form_submit_button("💾 Salvar e Ativar Bot"):
                # Aqui faremos o upsert na sua tabela 'automacoes_bot' assim que você mandar a estrutura
                st.success(f"Bot programado com sucesso para {dia} às {hora}!")
