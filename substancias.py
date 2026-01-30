import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile
from fpdf import FPDF
import requests

# Configurações iniciais
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
URL_SISTEMA = "https://sistemadeqrcodes.streamlit.app/"

# --- FUNÇÕES DE APOIO E IA ---

def gerar_parecer_ia(dados_processo):
    """Gera parecer técnico usando Llama 3.3-70B via Groq API"""
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
    """Gera o relatório final em formato PDF profissional"""
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

def show_substances():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    st.title("📋 Registro de Processos e Análises")
    
    # --- SEÇÃO DE ANOTAÇÕES INTEGRADA COM PROJETOS E VIDRARIAS ---
    with st.expander("📝 Nova Anotação / Uso de Reagente", expanded=False):
        try:
            # Busca Reagentes, Vidrarias e Projetos Ativos
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
                    # Seleção de Projeto
                    proj_list = df_projetos['nome'].tolist() if not df_projetos.empty else ["Nenhum Projeto Ativo"]
                    projeto_nome = st.selectbox("Vincular ao Projeto", options=proj_list)
                    
                    sub_usada = st.selectbox("Substância Utilizada", options=df_reagentes['nome'].tolist())
                    lote_ref = st.text_input("Lote do Reagente")
                with col_an2:
                    # Seleção de Vidraria via Banco
                    vid_list = [f"{v['tipo']} - {v['numeracao']}" for v in res_vid.data] if res_vid.data else ["Nenhuma Vidraria Cadastrada"]
                    vid_selecionada = st.selectbox("Vidraria Utilizada", options=vid_list)
                    
                    qtd_usada = st.number_input("Quantidade Utilizada", min_value=0.0, step=0.01)
                
                explicacao = st.text_area("Descrição do Procedimento (Como foi feito e resultados)")
                
                if st.button("🚀 Finalizar, Abater Estoque e Salvar", use_container_width=True):
                    if qtd_usada > 0:
                        row_atual = df_reagentes[df_reagentes['nome'] == sub_usada].iloc[0]
                        nova_qtd_estoque = float(row_atual['quantidade']) - float(qtd_usada)
                        
                        if nova_qtd_estoque < 0:
                            st.error("Erro: Quantidade em estoque insuficiente.")
                        else:
                            # 1. Atualiza Estoque na tabela substancias
                            supabase.table("substancias").update({"quantidade": nova_qtd_estoque}).eq("id", row_atual['id']).execute()
                            
                            # 2. Registra Log de Auditoria
                            supabase.table("logs_estoque").insert({
                                "usuario": username_atual, "substancia": sub_usada,
                                "quantidade_antiga": float(row_atual['quantidade']), 
                                "quantidade_nova": nova_qtd_estoque, "org_name": org_usuario
                            }).execute()
                            
                            # 3. Gerar Parecer IA
                            with st.spinner("IA processando parecer técnico..."):
                                parecer = gerar_parecer_ia(f"Projeto: {projeto_nome}. Uso de {qtd_usada} de {sub_usada}. Vidraria: {vid_selecionada}. Procedimento: {explicacao}")
                            
                            # 4. Salvar Persistência na Tabela de Anotacoes (NOVO)
                            id_vidraria = df_vidrarias.iloc[vid_list.index(vid_selecionada)]['id'] if res_vid.data else None
                            
                            supabase.table("anotacoes_processos").insert({
                                "data_procedimento": str(data_proc),
                                "usuario": username_atual,
                                "substancia_id": int(row_atual['id']),
                                "quantidade_usada": float(qtd_usada),
                                "lote_reagente": lote_ref,
                                "vidraria_id": id_vidraria,
                                "procedimento_texto": explicacao,
                                "parecer_ia": parecer,
                                "org_name": org_usuario
                            }).execute()

                            # 5. Exportação em PDF
                            dados_relatorio = {
                                "projeto": projeto_nome, "data": str(data_proc), "usuario": username_atual, 
                                "substancia": sub_usada, "lote": lote_ref, "vidraria": vid_selecionada, 
                                "quantidade_usada": qtd_usada, "procedimento": explicacao
                            }
                            pdf_bytes = exportar_pdf(dados_relatorio, parecer)
                            
                            st.success("Estoque atualizado, anotação salva no banco e relatório gerado!")
                            st.download_button("📥 Baixar Relatório Final (PDF)", data=pdf_bytes, 
                                             file_name=f"analise_{sub_usada}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            else:
                st.info("Nenhum reagente disponível para uso.")
        except Exception as e:
            st.error(f"Erro no módulo de anotações: {e}")

    st.divider()
    
    # --- 1. CADASTRO (MANTIDO CONFORME ORIGINAL) ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item no Inventário")
        if role_usuario == "Visualizador":
            st.warning("Seu perfil é apenas para visualização.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substância")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentração")
                quantidade = st.number_input("Quantidade Atual", min_value=0.0)
            with col3:
                estoque_minimo = st.number_input("Estoque Mínimo (Alerta)", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Número CAS (Opcional)")

            with st.expander("🛡️ Informações de Segurança (FISPQ/MSDS)"):
                c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                s_saude = c_s1.slider("Saúde", 0, 4, 0)
                s_fogo = c_s2.slider("Fogo", 0, 4, 0)
                s_reat = c_s3.slider("Reatividade", 0, 4, 0)
                s_esp = c_s4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Instruções de Emergência / Primeiros Socorros")
                
            if st.button("➕ Adicionar Substância", use_container_width=True):
                if nome and quantidade:
                    data_insert = {
                        "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                        "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                        "validade": validade, "org_name": org_usuario, "cas": cas,
                        "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat,
                        "especial": s_esp, "instrucoes": instrucoes
                    }
                    supabase.table("substancias").insert(data_insert).execute()
                    
                    supabase.table("logs_estoque").insert({
                        "usuario": username_atual, "substancia": nome,
                        "quantidade_antiga": 0.0, "quantidade_nova": float(quantidade), "org_name": org_usuario
                    }).execute()
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    # --- 2. EXIBIÇÃO DO INVENTÁRIO (MANTIDO CONFORME ORIGINAL) ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.subheader(f"📋 Inventário: {org_usuario}")
            cols_ordem = ['id', 'nome', 'cas', 'quantidade', 'estoque_minimo', 'validade']
            st.dataframe(df[cols_ordem], use_container_width=True, hide_index=True)

            with st.container(border=True):
                st.markdown("### 📊 Exportação e QRCodes")
                col_exp1, col_exp2, col_exp3 = st.columns(3)
                
                csv = df.to_csv(index=False).encode('utf-8')
                col_exp1.download_button(label="📥 Baixar CSV", data=csv, file_name=f"inventario.csv", use_container_width=True)
                
                buf_zip = BytesIO()
                with zipfile.ZipFile(buf_zip, 'w') as zf:
                    for _, row in df.iterrows():
                        img_qr = qrcode.make(f"{URL_SISTEMA}?id={row['id']}")
                        img_buf = BytesIO(); img_qr.save(img_buf, format="PNG")
                        zf.writestr(f"qr_{row['nome']}.png", img_buf.getvalue())
                col_exp2.download_button(label="🖼️ Zip QRCodes", data=buf_zip.getvalue(), file_name="qrcodes.zip", use_container_width=True)
                col_exp3.link_button("🌐 Excel Online", "https://excel.new", use_container_width=True)

            # Segurança e Histórico
            st.subheader("🛡️ Consulta de Segurança")
            sub_alvo = st.selectbox("Selecione um item:", options=df['nome'].tolist())
            det = df[df['nome'] == sub_alvo].iloc[0]
            c_v, c_t, c_q = st.columns([1, 2, 1])
            with c_v: render_hommel(det['saude'], det['fogo'], det['reatividade'], det['especial'])
            with c_t: st.warning(f"**Emergência:**\n{det.get('instrucoes', 'N/A')}")
            with c_q:
                qr_img = qrcode.make(f"{URL_SISTEMA}?id={det['id']}")
                b = BytesIO(); qr_img.save(b, format="PNG")
                st.image(b.getvalue(), width=100)

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

if __name__ == "__main__":
    show_substances()
