import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile
from fpdf import FPDF
import requests

# --- CONFIGURAÇÕES INICIAIS ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
URL_SISTEMA = "https://sistemadeqrcodes.streamlit.app/"

# --- FUNÇÕES DE APOIO E IA ---

def gerar_parecer_ia(dados_processo):
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return "Parecer de IA indisponível: Chave de API não configurada."
    
    url_groq = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = f"Como um especialista em química laboratorial, forneça um parecer técnico sobre o seguinte procedimento: {dados_processo}. Seja formal, conciso e aponte possíveis riscos ou observações de qualidade."
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }
    
    try:
        response = requests.post(url_groq, json=payload, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Erro ao gerar parecer: {str(e)}"

def exportar_pdf(dados, parecer_ia):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatório de Procedimento Laboratorial", ln=True, align='C')
    
    pdf.set_font("Arial", size=11)
    pdf.ln(10)
    for key, value in dados.items():
        pdf.multi_cell(0, 10, txt=f"{key.replace('_', ' ').capitalize()}: {value}", border=0)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Parecer Técnico (IA Llama-3.3-70B):", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 7, txt=parecer_ia)
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def render_hommel(saude, fogo, reat, esp):
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;">
        <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555;">
            <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{fogo}</div>
            <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">{reat}</div>
            <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{saude}</div>
            <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold; font-size: 0.7em;">{esp if esp else ''}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- MÓDULO PRINCIPAL ---

def show_substances():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    st.title("📋 Registro de Processos e Análises")

    # --- NOVO: SEÇÃO DE ANOTAÇÕES E PROCEDIMENTOS ---
    with st.expander("📝 Nova Anotação / Uso de Reagente", expanded=False):
        try:
            # Carregar dados relacionais
            res_sub = supabase.table("substancias").select("id, nome, quantidade").eq("org_name", org_usuario).execute()
            res_vid = supabase.table("vidrarias").select("id, tipo, numeracao").eq("org_name", org_usuario).execute()
            res_proj = supabase.table("projetos").select("id, nome").eq("org_name", org_usuario).eq("status", "Ativo").execute()
            
            df_reagentes = pd.DataFrame(res_sub.data)
            df_vidrarias = pd.DataFrame(res_vid.data)
            df_projetos = pd.DataFrame(res_proj.data)
            
            if not df_reagentes.empty:
                col_an1, col_an2 = st.columns(2)
                with col_an1:
                    data_proc = st.date_input("Data do Procedimento", datetime.now())
                    
                    proj_options = ["Nenhum"] + df_projetos['nome'].tolist() if not df_projetos.empty else ["Nenhum"]
                    projeto_sel = st.selectbox("Vincular ao Projeto", options=proj_options)
                    
                    sub_usada = st.selectbox("Substância Utilizada", options=df_reagentes['nome'].tolist())
                    lote_ref = st.text_input("Lote do Reagente")
                with col_an2:
                    vid_options = ["Nenhuma"] + [f"{v['tipo']} - {v['numeracao']}" for v in res_vid.data] if not df_vidrarias.empty else ["Nenhuma"]
                    vid_sel = st.selectbox("Vidraria Utilizada", options=vid_options)
                    
                    qtd_usada = st.number_input("Quantidade Utilizada", min_value=0.0, step=0.01)
                
                explicacao = st.text_area("Descrição do Procedimento (Como foi feito e resultados)")
                
                if st.button("🚀 Finalizar e Sincronizar Tudo", use_container_width=True):
                    if qtd_usada > 0:
                        row_atual = df_reagentes[df_reagentes['nome'] == sub_usada].iloc[0]
                        nova_qtd_estoque = float(row_atual['quantidade']) - float(qtd_usada)
                        
                        if nova_qtd_estoque < 0:
                            st.error("Erro: Quantidade insuficiente em estoque.")
                        else:
                            try:
                                # 1. Atualiza Estoque
                                supabase.table("substancias").update({"quantidade": nova_qtd_estoque}).eq("id", row_atual['id']).execute()
                                
                                # 2. Registra Log de Estoque
                                supabase.table("logs_estoque").insert({
                                    "usuario": username_atual, 
                                    "substancia": sub_usada,
                                    "quantidade_antiga": float(row_atual['quantidade']), 
                                    "quantidade_nova": nova_qtd_estoque, 
                                    "org_name": org_usuario
                                }).execute()
                                
                                # 3. Gerar Parecer IA
                                with st.spinner("IA processando parecer técnico..."):
                                    parecer = gerar_parecer_ia(f"Projeto: {projeto_sel}. Substância: {sub_usada}. Procedimento: {explicacao}")
                                
                                # 4. Salvar Anotação no Banco (Persistência)
                                id_vid = None
                                if vid_sel != "Nenhuma":
                                    num_v = vid_sel.split(" - ")[-1]
                                    id_vid = df_vidrarias[df_vidrarias['numeracao'] == num_v].iloc[0]['id']

                                supabase.table("anotacoes_processos").insert({
                                    "data_procedimento": str(data_proc),
                                    "usuario": username_atual,
                                    "substancia_id": int(row_atual['id']),
                                    "quantidade_usada": float(qtd_usada),
                                    "lote_reagente": lote_ref,
                                    "vidraria_id": id_vid,
                                    "procedimento_texto": explicacao,
                                    "parecer_ia": parecer,
                                    "org_name": org_usuario
                                }).execute()
                                
                                # 5. Gerar PDF
                                dados_pdf = {
                                    "Projeto": projeto_sel, "Data": str(data_proc), "Analista": username_atual,
                                    "Substância": sub_usada, "Lote": lote_ref, "Vidraria": vid_sel,
                                    "Quantidade": qtd_usada, "Descrição": explicacao
                                }
                                pdf_bytes = exportar_pdf(dados_pdf, parecer)
                                
                                st.success("✅ Estoque atualizado, Log gerado e Anotação salva!")
                                st.download_button("📥 Baixar Relatório PDF", data=pdf_bytes, file_name=f"analise_{sub_usada}.pdf")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro na sincronização: {e}")
            else:
                st.info("Nenhum reagente cadastrado para uso.")
        except Exception as e:
            st.error(f"Erro ao carregar dados de anotação: {e}")

    st.divider()
    
    # --- 1. CADASTRO DE NOVOS ITENS ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item no Inventário")
        if role_usuario == "Visualizador":
            st.warning("Acesso apenas para visualização.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substância")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentração")
                quantidade = st.number_input("Quantidade Inicial", min_value=0.0)
            with col3:
                estoque_minimo = st.number_input("Estoque Mínimo", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Número CAS")

            with st.expander("🛡️ Segurança (FISPQ)"):
                cs1, cs2, cs3, cs4 = st.columns(4)
                s_saude = cs1.slider("Saúde", 0, 4, 0)
                s_fogo = cs2.slider("Fogo", 0, 4, 0)
                s_reat = cs3.slider("Reatividade", 0, 4, 0)
                s_esp = cs4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Primeiros Socorros")
                
            if st.button("➕ Adicionar ao Inventário", use_container_width=True):
                if nome and quantidade >= 0:
                    data_insert = {
                        "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                        "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                        "validade": validade, "org_name": org_usuario, "cas": cas,
                        "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat,
                        "especial": s_esp, "instrucoes": instrucoes
                    }
                    supabase.table("substancias").insert(data_insert).execute()
                    
                    supabase.table("logs_estoque").insert({
                        "usuario": username_atual, "substancia": f"CADASTRO: {nome}",
                        "quantidade_antiga": 0.0, "quantidade_nova": float(quantidade), "org_name": org_usuario
                    }).execute()
                    st.success("Item cadastrado com sucesso!")
                    st.rerun()

    st.divider()

    # --- 2. EXIBIÇÃO E GESTÃO DO INVENTÁRIO ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.subheader(f"📋 Inventário: {org_usuario}")
            # Destaque para estoque baixo
            df['Status'] = df.apply(lambda x: "🔴 Baixo" if x['quantidade'] <= x['estoque_minimo'] else "🟢 OK", axis=1)
            cols_show = ['id', 'nome', 'quantidade', 'Status', 'validade', 'cas']
            st.dataframe(df[cols_show], use_container_width=True, hide_index=True)

            # Exportação
            with st.container(border=True):
                st.markdown("### 📊 Exportação")
                ce1, ce2, ce3 = st.columns(3)
                ce1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "inventario.csv", "text/csv", use_container_width=True)
                
                buf_zip = BytesIO()
                with zipfile.ZipFile(buf_zip, 'w') as zf:
                    for _, row in df.iterrows():
                        qr_img = qrcode.make(f"{URL_SISTEMA}?id={row['id']}")
                        b_qr = BytesIO(); qr_img.save(b_qr, format="PNG")
                        zf.writestr(f"qr_{row['nome']}.png", b_qr.getvalue())
                ce2.download_button("🖼️ ZIP QR Codes", buf_zip.getvalue(), "qrcodes.zip", use_container_width=True)
                ce3.link_button("🌐 Excel Online", "https://excel.new", use_container_width=True)

            # Segurança e Histórico Individual
            st.subheader("🛡️ Ficha de Segurança")
            sub_sel = st.selectbox("Visualizar item:", options=df['nome'].tolist())
            det = df[df['nome'] == sub_sel].iloc[0]
            
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1: render_hommel(det['saude'], det['fogo'], det['reatividade'], det['especial'])
            with c2: st.info(f"**Emergência:** {det.get('instrucoes', 'Sem dados.')}")
            with c3:
                qr_ind = qrcode.make(f"{URL_SISTEMA}?id={det['id']}")
                b_ind = BytesIO(); qr_ind.save(b_ind, format="PNG")
                st.image(b_ind.getvalue(), width=120)

            # Histórico de Logs (O que você pediu para manter)
            with st.expander("📜 Histórico de Movimentações"):
                logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(10).execute()
                if logs_res.data:
                    st.table(pd.DataFrame(logs_res.data)[['created_at', 'usuario', 'substancia', 'quantidade_nova']])

    except Exception as e:
        st.error(f"Erro de carregamento: {e}")

if __name__ == "__main__":
    show_substances()
