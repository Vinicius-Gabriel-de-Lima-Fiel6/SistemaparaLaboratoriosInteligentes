import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import zipfile
from io import BytesIO
import os
import qrcode

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
    estilo = """
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
    if os.path.exists("CSS/substancias.css"):
        try:
            with open("CSS/substancias.css", "r") as f:
                estilo = f"<style>{f.read()}</style>"
        except:
            pass
    
    st.markdown(estilo + f"""
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
    if 'user_data' not in st.session_state:
        st.error("Erro de autenticação. Realize o login novamente.")
        return

    user_data = st.session_state.user_data
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    st.header(f"🧪 Gestão de Substâncias - {org_usuario}")

    with st.container(border=True):
        st.subheader("Cadastrar Item")
        if role_usuario == "Visualizador":
            st.warning("Apenas leitura.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                nome = st.text_input("Substância")
                finalidade = st.text_input("Uso")
            with c2:
                concentracao = st.text_input("Conc.")
                quantidade = st.number_input("Qtd", min_value=0.0)
            with c3:
                estoque_min = st.number_input("Mínimo", min_value=0.0)
                validade = st.text_input("Validade")
            
            cas = st.text_input("CAS Number")

            with st.expander("Informações NFPA 704"):
                s1, s2, s3, s4 = st.columns(4)
                v_saude = s1.slider("Saúde", 0, 4, 0)
                v_fogo = s2.slider("Fogo", 0, 4, 0)
                v_reat = s3.slider("Reatividade", 0, 4, 0)
                v_esp = s4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Procedimentos de Emergência")
                
            if st.button("Gravar no Banco", use_container_width=True):
                if nome:
                    data = {
                        "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                        "quantidade": quantidade, "estoque_minimo": estoque_min,
                        "validade": validade, "org_name": org_usuario, "cas": cas,
                        "saude": v_saude, "fogo": v_fogo, "reatividade": v_reat,
                        "especial": v_esp, "instrucoes": instrucoes
                    }
                    supabase.table("substancias").insert(data).execute()
                    registrar_historico("Cadastro", nome, "Inserção manual", user_data)
                    st.rerun()

    try:
        res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.divider()
            st.dataframe(df[['nome', 'quantidade', 'validade', 'cas']], use_container_width=True)

            st.subheader("🛡️ Segurança e Identificação")
            sel_item = st.selectbox("Escolha o item para gerar QR/Ficha", df['nome'].tolist())
            item = df[df['nome'] == sel_item].iloc[0]

            col_ficha, col_qrcode = st.columns([2, 1])
            with col_ficha:
                render_hommel(item['saude'], item['fogo'], item['reatividade'], item['especial'])
                st.info(f"**Emergência:** {item['instrucoes']}")
            
            with col_qrcode:
                url_base = st.text_input("URL do Servidor", f"https://{org_usuario.lower().replace(' ','')}.lab.com/fichas/")
                link_final = f"{url_base}{item['id']}.html"
                
                qr = qrcode.make(link_final)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                st.image(buffer.getvalue(), width=180, caption=f"ID: {item['id']}")
                st.download_button("Baixar PNG", buffer.getvalue(), f"qr_{sel_item}.png")

            st.divider()
            with st.expander("🛠️ Console de TI - Ações em Massa"):
                c_ti1, c_ti2 = st.columns(2)
                
                if c_ti1.button("Gerar ZIP de QRCodes"):
                    z_qr = BytesIO()
                    with zipfile.ZipFile(z_qr, "a") as z:
                        for _, r in df.iterrows():
                            img = qrcode.make(f"{url_base}{r['id']}.html")
                            img_b = BytesIO()
                            img.save(img_b, format="PNG")
                            z.writestr(f"qrcodes/qr_{r['nome']}.png", img_b.getvalue())
                    st.download_button("Download ZIP QRs", z_qr.getvalue(), "estoque_qr.zip")

                if c_ti2.button("Gerar Estáticos (HTML/CSS)"):
                    z_html = BytesIO()
                    with zipfile.ZipFile(z_html, "a") as z:
                        if os.path.exists("CSS/substancias.css"):
                            with open("CSS/substancias.css", "r") as f:
                                z.writestr("substancias.css", f.read())
                        if os.path.exists("HTML/substancias.html"):
                            with open("HTML/substancias.html", "r") as f:
                                template = f.read()
                            for _, r in df.iterrows():
                                h = template
                                for k in r.index:
                                    h = h.replace(f"{{{{{k}}}}}", str(r[k]))
                                z.writestr(f"{r['id']}.html", h)
                    st.download_button("Download ZIP Site", z_html.getvalue(), "site_estatico.zip")

    except Exception as e:
        st.error(f"Erro na conexão com Supabase: {e}")

if __name__ == "__main__":
    show_substances()
