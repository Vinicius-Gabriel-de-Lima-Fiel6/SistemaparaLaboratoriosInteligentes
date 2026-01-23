import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
import zipfile
from io import BytesIO
import os

# Configuração de Conexão
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_log(acao, substancia, qtd, detalhes):
    """Alimenta a tabela historico_atividades com detalhes completos"""
    user_data = st.session_state.get('user_data', {})
    log_entry = {
        "usuario_email": user_data.get('email', 'desconhecido@lab.com'),
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia,
        "quantidade": str(qtd),
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    supabase.table("historico_atividades").insert(log_entry).execute()

def carregar_recurso(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def show_substances():
    st.title("🔬 Controle de Estoque e Segurança")
    user_data = st.session_state.get('user_data', {})
    org = user_data.get('org_name', 'Default')

    # --- ABA DE CADASTRO ---
    with st.expander("📝 Cadastrar Nova Substância"):
        with st.form("form_cadastro"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome")
            cas = col1.text_input("CAS")
            qtd = col2.number_input("Quantidade Inicial", min_value=0.0)
            
            st.markdown("### 🛡️ Segurança (NFPA 704)")
            c_s1, c_s2, c_s3, c_s4 = st.columns(4)
            s_saude = c_s1.slider("Saúde", 0, 4, 0)
            s_fogo = c_s2.slider("Fogo", 0, 4, 0)
            s_reat = c_s3.slider("Reatividade", 0, 4, 0)
            s_esp = c_s4.selectbox("Especial", ["", "W", "OX", "SA"])
            instrucoes = st.text_area("Instruções de Emergência")

            if st.form_submit_button("Cadastrar"):
                dados = {
                    "nome": nome, "quantidade": qtd, "cas": cas, "org_name": org,
                    "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat, 
                    "especial": s_esp, "instrucoes": instrucoes
                }
                supabase.table("substancias").insert(dados).execute()
                registrar_log("CADASTRO", nome, qtd, f"Item {nome} inserido no sistema.")
                st.success("Cadastrado com sucesso!")
                st.rerun()

    # --- INVENTÁRIO E QR CODES ---
    res = supabase.table("substancias").select("*").eq("org_name", org).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        st.subheader("📊 Inventário")
        st.dataframe(df[['nome', 'cas', 'quantidade']], use_container_width=True)

        st.divider()
        st.subheader("🖨️ Gerador de QR Codes")
        
        url_base = st.text_input("Link da Ficha Digital:", "https://meulab.com/ficha/")
        
        col_btn1, col_btn2 = st.columns(2)
        
        # Opção 1: Individual
        with col_btn1:
            item_sel = st.selectbox("Escolha para QR individual:", df['nome'].tolist())
            if st.button("Gerar Individual"):
                row = df[df['nome'] == item_sel].iloc[0]
                qr_img = qrcode.make(f"{url_base}{row['id']}")
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                st.image(buf.getvalue(), width=150)
                registrar_log("QR_INDIVIDUAL", item_sel, 0, "Gerou QR code único.")

        # Opção 2: Em Lote (ZIP)
        with col_btn2:
            st.write("Baixar todos os itens cadastrados:")
            if st.button("🚀 Gerar Todos (ZIP)"):
                zip_buf = BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as z:
                    for _, r in df.iterrows():
                        # Gerar QR
                        qr = qrcode.make(f"{url_base}{r['id']}")
                        img_buf = BytesIO()
                        qr.save(img_buf, format="PNG")
                        z.writestr(f"qrcodes/QR_{r['nome']}.png", img_buf.getvalue())
                
                st.download_button("📥 Baixar Arquivo .ZIP", zip_buf.getvalue(), "todos_qrcodes.zip")
                registrar_log("QR_LOTE", "VARIADOS", len(df), f"Exportou {len(df)} QR codes em massa.")

    # --- VISUALIZAÇÃO COM HTML/CSS ---
    st.divider()
    if not df.empty:
        st.subheader("👁️ Visualização de Segurança")
        sel_vis = st.selectbox("Ver detalhes de:", df['nome'].tolist(), key="vis_sel")
        detalhes = df[df['nome'] == sel_vis].iloc[0]

        css = carregar_recurso("CSS/substancias.css")
        html_tpl = carregar_recurso("HTML/card_template.html")
        
        # Substituição de Variáveis no HTML
        for key in detalhes.index:
            html_tpl = html_tpl.replace(f"{{{{{key}}}}}", str(detalhes[key]))
        
        st.markdown(f"<style>{css}</style>{html_tpl}", unsafe_allow_html=True)

if __name__ == "__main__":
    show_substances()
