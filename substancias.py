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

def limpar_texto_pdf(txt):
    """Remove caracteres especiais que quebram o PDF (latin-1)"""
    if not txt: return ""
    # Substitui caracteres tipográficos da IA por caracteres padrão
    substituicoes = {
        '\u2212': '-', '\u2013': '-', '\u2014': '-', 
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\xb0': ' graus'
    }
    for char, rep in substituicoes.items():
        txt = txt.replace(char, rep)
    return txt

def gerar_parecer_ia(dados_processo):
    """Gera parecer técnico usando Llama 3.3-70B via Groq API"""
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return "Parecer de IA indisponivel: Chave de API nao configurada."
    
    url_groq = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = f"Como um especialista em quimica laboratorial, forneca um parecer tecnico sobre: {dados_processo}. Seja formal e conciso."
    
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
    """Gera o relatório final em formato PDF com tratamento de caracteres"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio de Procedimento Laboratorial", ln=True, align='C')
    
    pdf.set_font("Arial", size=11)
    pdf.ln(10)
    
    for key, value in dados.items():
        txt_limpo = limpar_texto_pdf(f"{key.capitalize()}: {value}")
        pdf.multi_cell(0, 10, txt=txt_limpo.encode('latin-1', 'replace').decode('latin-1'), border=0)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Parecer Tecnico (IA Llama-3.3-70B):", ln=True)
    pdf.set_font("Arial", size=10)
    
    parecer_limpo = limpar_texto_pdf(parecer_ia)
    pdf.multi_cell(0, 7, txt=parecer_limpo.encode('latin-1', 'replace').decode('latin-1'))
    
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
    username_atual = user_data.get('username', 'Usuario')

    # --- SEÇÃO DE ANOTAÇÕES E PROCEDIMENTOS ---
    st.title("📋 Registro de Processos e Análises")
    with st.expander("📝 Nova Anotação / Uso de Reagente", expanded=False):
        try:
            res_sub = supabase.table("substancias").select("nome, quantidade, id").eq("org_name", org_usuario).execute()
            res_vid = supabase.table("vidrarias").select("vid, tipo, numeracao").eq("org_name", org_usuario).execute()
            res_proj = supabase.table("projetos").select("id, nome").eq("org_name", org_usuario).eq("status", "Ativo").execute()
            
            df_reagentes = pd.DataFrame(res_sub.data)
            df_vidrarias = pd.DataFrame(res_vid.data)
            df_projetos = pd.DataFrame(res_proj.data)
            
            if not df_reagentes.empty:
                col_an1, col_an2 = st.columns(2)
                with col_an1:
                    data_proc = st.date_input("Data do Procedimento", datetime.now())
                    proj_list = df_projetos['nome'].tolist() if not df_projetos.empty else ["Nenhum"]
                    projeto_nome = st.selectbox("Vincular ao Projeto", options=proj_list)
                    sub_usada = st.selectbox("Substancia Utilizada", options=df_reagentes['nome'].tolist())
                    lote_ref = st.text_input("Lote do Reagente")
                with col_an2:
                    vid_list = [f"{v['tipo']} - {v['numeracao']}" for v in res_vid.data] if not df_vidrarias.empty else ["Nenhuma"]
                    vid_selecionada = st.selectbox("Vidraria Utilizada", options=vid_list)
                    qtd_usada = st.number_input("Quantidade Utilizada", min_value=0.0, step=0.01)
                    
                explicacao = st.text_area("Descricao do Procedimento (Metodologia e Resultados)")
                
                if st.button("🚀 Finalizar e Salvar no Banco", use_container_width=True):
                    if qtd_usada > 0:
                        row_atual = df_reagentes[df_reagentes['nome'] == sub_usada].iloc[0]
                        nova_qtd = float(row_atual['quantidade']) - float(qtd_usada)
                        
                        if nova_qtd < 0:
                            st.error("Estoque insuficiente!")
                        else:
                            # 1. Atualiza Estoque
                            supabase.table("substancias").update({"quantidade": nova_qtd}).eq("id", row_atual['id']).execute()
                            
                            # 2. Registra Log de Auditoria
                            supabase.table("logs_estoque").insert({
                                "usuario": username_atual, "substancia": sub_usada,
                                "quantidade_antiga": float(row_atual['quantidade']), 
                                "quantidade_nova": nova_qtd, "org_name": org_usuario
                            }).execute()
                            
                            # 3. Parecer IA
                            with st.spinner("Llama analisando dados..."):
                                parecer = gerar_parecer_ia(f"Uso de {qtd_usada} de {sub_usada}. Projeto: {projeto_nome}. Procedimento: {explicacao}")
                            
                            # 4. Busca o valor de 'vid' da vidraria selecionada
                            id_v_save = None
                            if vid_selecionada != "Nenhuma":
                                num_v = vid_selecionada.split(" - ")[-1]
                                id_v_save = df_vidrarias[df_vidrarias['numeracao'] == num_v].iloc[0]['vid']

                            # 5. Salvar na Tabela de Anotacoes (Usando 'id' como o nome da coluna na tabela anotacoes_processos)
                            supabase.table("anotacoes_processos").insert({
                                "data_procedimento": str(data_proc), 
                                "usuario": username_atual,
                                "substancia_id": int(row_atual['id']), 
                                "quantidade_usada": float(qtd_usada),
                                "lote_reagente": lote_ref, 
                                "id": id_v_save,  # Conforme você informou: o nome da coluna na tabela de anotações é 'id'
                                "procedimento_texto": explicacao, 
                                "parecer_ia": parecer, 
                                "org_name": org_usuario
                            }).execute()

                            # 6. Salva PDF para o botão de download
                            st.session_state['pdf_report'] = exportar_pdf({
                                "projeto": projeto_nome, "data": str(data_proc), "usuario": username_atual,
                                "substancia": sub_usada, "lote": lote_ref, "vidraria": vid_selecionada,
                                "quantidade": qtd_usada, "procedimento": explicacao
                            }, parecer)
                            st.session_state['last_sub'] = sub_usada
                            st.success("Dados salvos e estoque abatido!")
                            st.rerun()

                if 'pdf_report' in st.session_state:
                    st.download_button("📥 Baixar Relatorio PDF", data=st.session_state['pdf_report'], 
                                     file_name=f"analise_{st.session_state['last_sub']}.pdf", mime="application/pdf", use_container_width=True)
            else:
                st.info("Sem reagentes cadastrados.")
        except Exception as e:
            st.error(f"Erro no modulo de anotacoes: {e}")

    st.divider()
    
    # --- 1. CADASTRO ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        if role_usuario == "Visualizador":
            st.warning("Apenas visualizacao permitida.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substancia")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentracao")
                quantidade = st.number_input("Quantidade Atual", min_value=0.0)
            with col3:
                estoque_minimo = st.number_input("Estoque Minimo", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Numero CAS")

            with st.expander("🛡️ Seguranca (FISPQ)"):
                c1, c2, c3, c4 = st.columns(4)
                s_saude = c1.slider("Saude", 0, 4, 0)
                s_fogo = c2.slider("Fogo", 0, 4, 0)
                s_reat = c3.slider("Reatividade", 0, 4, 0)
                s_esp = c4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Instrucoes de Emergencia")
                
            if st.button("➕ Adicionar Substancia", use_container_width=True):
                if nome and quantidade:
                    supabase.table("substancias").insert({
                        "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                        "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                        "validade": validade, "org_name": org_usuario, "cas": cas,
                        "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat,
                        "especial": s_esp, "instrucoes": instrucoes
                    }).execute()
                    supabase.table("logs_estoque").insert({
                        "usuario": username_atual, "substancia": nome,
                        "quantidade_antiga": 0.0, "quantidade_nova": float(quantidade), "org_name": org_usuario
                    }).execute()
                    st.success("Cadastrado!")
                    st.rerun()

    st.divider()

    # --- 2. INVENTÁRIO ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.subheader(f"📋 Inventario: {org_usuario}")
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'estoque_minimo', 'validade']], use_container_width=True, hide_index=True)

            with st.container(border=True):
                st.markdown("### 📊 Exportacao")
                c_e1, c_e2, c_e3, c_e4 = st.columns([1, 1, 1, 1])
                c_e1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "inventario.csv", use_container_width=True)
                c_e2.link_button("🌐 Excel", "https://excel.new", use_container_width=True)
                
                buf_z = BytesIO()
                with zipfile.ZipFile(buf_z, 'w') as zf:
                    for _, row in df.iterrows():
                        qr_i = qrcode.make(f"{URL_SISTEMA}?id={row['id']}")
                        b_i = BytesIO(); qr_i.save(b_i, format="PNG")
                        zf.writestr(f"qr_{row['nome']}.png", b_i.getvalue())
                c_e3.download_button("🖼️ ZIP QR", buf_z.getvalue(), "qrcodes.zip", use_container_width=True)
                with c_e4:
                    with st.popover("💡 Ajuda", use_container_width=True): st.write("Use o CSV no Excel Online.")

            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🔄 Atualizar Estoque"):
                    col_s, col_v, col_b = st.columns([2, 1, 1])
                    sub_ed = col_s.selectbox("Substancia", options=df['nome'].tolist(), key="ed_stock")
                    n_qtd = col_v.number_input("Nova Qtd", min_value=0.0)
                    if col_b.button("Atualizar", use_container_width=True):
                        old_q = df[df['nome'] == sub_ed]['quantidade'].values[0]
                        supabase.table("substancias").update({"quantidade": n_qtd}).eq("nome", sub_ed).execute()
                        supabase.table("logs_estoque").insert({
                            "usuario": username_atual, "substancia": sub_ed, 
                            "quantidade_antiga": float(old_q), "quantidade_nova": float(n_qtd), "org_name": org_usuario
                        }).execute()
                        st.rerun()

            st.subheader("🛡️ Seguranca")
            sub_alvo = st.selectbox("Item:", options=df['nome'].tolist())
            det = df[df['nome'] == sub_alvo].iloc[0]
            cv, ct, cq = st.columns([1, 2, 1])
            with cv: render_hommel(det['saude'], det['fogo'], det['reatividade'], det['especial'])
            with ct: st.warning(f"**Emergencia:** {det.get('instrucoes', 'N/A')}")
            with cq:
                qr_ind = qrcode.make(f"{URL_SISTEMA}?id={det['id']}")
                b_ind = BytesIO(); qr_ind.save(b_ind, format="PNG")
                st.image(b_ind.getvalue(), width=100)
                st.download_button("📥 QR", b_ind.getvalue(), "qr.png")

            with st.expander("📜 Logs Recentes"):
                l_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(5).execute()
                if l_res.data: st.table(pd.DataFrame(l_res.data)[['created_at', 'usuario', 'substancia', 'quantidade_nova']])

            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover"):
                    id_rem = st.selectbox("ID p/ remover", options=df['id'].tolist())
                    if st.button("Confirmar Exclusao", type="primary"):
                        supabase.table("substancias").delete().eq("id", id_rem).execute()
                        st.rerun()
        else:
            st.info("Inventario vazio.")
    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
