import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import zipfile
from io import BytesIO
import os
import qrcode

st.set_page_config(page_title="Sistema de Substâncias", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_historico(acao, item, detalhes, user_data):
    log_entry = {
        "usuario_nome": user_data.get('username', 'Sistema'),
        "usuario_email": user_data.get('email', 'N/A'),
        "cargo": user_data.get('role', 'N/A'),
        "acao": acao,
        "item_afetado": item,
        "detalhes": detalhes,
        "org_name": user_data.get('org_name', 'Default'),
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico").insert(log_entry).execute()
    except:
        pass

def render_hommel(saude, fogo, reat, esp):
    caminho_css = "CSS/substancias.css"
    estilo_fallback = """
    <style>
        .hommel-container { display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
        .hommel-box { position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555; }
        .hommel-box div { position: absolute; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold; }
        .f_vermelho { top: 0; left: 0; background: #ff4b4b; }
        .r_amarelo { top: 0; left: 40px; background: #f1c40f; color: black !important; }
        .s_azul { top: 40px; left: 0; background: #3498db; }
        .e_branco { top: 40px; left: 40px; background: #fff; color: black !important; font-size: 0.7em; }
    </style>
    """
    conteudo_css = estilo_fallback
    if os.path.exists(caminho_css):
        with open(caminho_css, "r") as f:
            conteudo_css = f"<style>{f.read()}</style>"
    
    st.markdown(conteudo_css + f"""
    <div class="hommel-container">
        <div class="hommel-box">
            <div class="f_vermelho">{fogo}</div>
            <div class="r_amarelo">{reat}</div>
            <div class="s_azul">{saude}</div>
            <div class="e_branco">{esp if esp else ''}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_substances():
    st.header("🔬 Gerenciamento de Substâncias")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
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
                estoque_minimo = st.number_input("Estoque Mínimo", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Número CAS")

            with st.expander("🛡️ Informações de Segurança"):
                c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                s_saude = c_s1.slider("Saúde", 0, 4, 0)
                s_fogo = c_s2.slider("Fogo", 0, 4, 0)
                s_reat = c_s3.slider("Reatividade", 0, 4, 0)
                s_esp = c_s4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Instruções de Emergência")
                
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
                    registrar_historico("Cadastro", nome, f"Adicionado ao sistema.", user_data)
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🔄 Atualizar Estoque"):
                    col_sel, col_val, col_btn = st.columns([2, 1, 1])
                    sub_edit = col_sel.selectbox("Escolha o item", options=df['nome'].tolist())
                    nova_qtd = col_val.number_input("Nova Qtd", min_value=0.0)
                    if col_btn.button("Salvar Alteração"):
                        supabase.table("substancias").update({"quantidade": nova_qtd}).eq("nome", sub_edit).execute()
                        registrar_historico("Movimentação", sub_edit, f"Estoque ajustado para {nova_qtd}", user_data)
                        st.rerun()

            st.subheader("🛡️ Ficha de Segurança e QR Code")
            col_f1, col_f2 = st.columns([2, 1])
            
            with col_f1:
                sub_fispq = st.selectbox("Selecionar Substância para Detalhes:", options=df['nome'].tolist())
                det = df[df['nome'] == sub_fispq].iloc[0]
                c_vis, c_txt = st.columns([1, 2])
                with c_vis:
                    render_hommel(det['saude'], det['fogo'], det['reatividade'], det['especial'])
                with c_txt:
                    st.info(f"**Instruções:** {det['instrucoes']}")

            with col_f2:
                base_url = st.text_input("URL Base do Servidor:", "https://meulab.com/fichas/")
                qr_link = f"{base_url}{det['id']}.html"
                
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(qr_link)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                st.image(buf.getvalue(), caption=f"QR Code: {sub_fispq}", width=200)
                st.download_button("📥 Baixar QR Individual", buf.getvalue(), f"qr_{sub_fispq}.png", "image/png")

            st.divider()
            
            with st.expander("⚙️ Ferramentas de Administrador (Gerar Tudo)"):
                col_gen1, col_gen2 = st.columns(2)
                
                if col_gen1.button("📑 Gerar QR Codes em Massa (ZIP)"):
                    zip_qr = BytesIO()
                    with zipfile.ZipFile(zip_qr, "a", zipfile.ZIP_DEFLATED) as z:
                        for _, r in df.iterrows():
                            qr_m = qrcode.make(f"{base_url}{r['id']}.html")
                            b_m = BytesIO()
                            qr_m.save(b_m, format="PNG")
                            z.writestr(f"qrcodes/qr_{r['nome']}.png", b_m.getvalue())
                    st.download_button("📥 Baixar Todos QR Codes", zip_qr.getvalue(), "todos_qrcodes.zip", "application/zip")

                if col_gen2.button("🛠️ Gerar Arquivos HTML/CSS"):
                    zip_sys = BytesIO()
                    with zipfile.ZipFile(zip_sys, "a", zipfile.ZIP_DEFLATED) as z:
                        if os.path.exists("CSS/substancias.css"):
                            with open("CSS/substancias.css", "r") as f:
                                z.writestr("substancias.css", f.read())
                        if os.path.exists("HTML/substancias.html"):
                            with open("HTML/substancias.html", "r") as f:
                                tmpl = f.read()
                            for _, r in df.iterrows():
                                html_i = tmpl
                                for k in r.index:
                                    html_i = html_i.replace(f"{{{{{k}}}}}", str(r[k]))
                                z.writestr(f"{r['id']}.html", html_i)
                    st.download_button("📥 Baixar Arquivos de Servidor", zip_sys.getvalue(), "arquivos_servidor.zip", "application/zip")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")

if __name__ == "__main__":
    show_substances()
