import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import os
import zipfile

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_historico(acao, item, detalhes, user_data):
    log = {
        "usuario_nome": user_data.get('username', 'Sistema'),
        "acao": acao,
        "item_afetado": item,
        "detalhes": detalhes,
        "org_name": user_data.get('org_name', 'Default'),
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico").insert(log).execute()
    except:
        pass

def show_substances():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    st.title(f"🧪 Estoque - {org_usuario}")

  
    with st.expander("➕ Cadastrar Substância"):
        if role_usuario == "Visualizador":
            st.warning("Acesso restrito.")
        else:
            with st.form("form_sub", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nome = c1.text_input("Nome")
                cas = c1.text_input("CAS")
                qtd = c2.number_input("Quantidade", min_value=0.0)
                val = c2.text_input("Validade")
                
                st.write("**Diamante de Hommel**")
                s1, s2, s3, s4 = st.columns(4)
                f = s1.slider("Fogo", 0, 4, 0)
                s = s2.slider("Saúde", 0, 4, 0)
                r = s3.slider("Reat", 0, 4, 0)
                e = s4.selectbox("Esp", ["", "W", "OX", "SA", "BIO"])
                inst = st.text_area("Instruções")

                if st.form_submit_button("Salvar"):
                    if nome:
                        payload = {
                            "nome": nome, "cas": cas, "quantidade": qtd,
                            "fogo": f, "saude": s, "reatividade": r, "especial": e,
                            "instrucoes": inst, "validade": val, "org_name": org_usuario
                        }
                        supabase.table("substancias").insert(payload).execute()
                        registrar_historico("Cadastro", nome, "Adicionado", user_data)
                        st.rerun()

 
    res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        st.divider()
        st.dataframe(df[['nome', 'quantidade', 'validade']], use_container_width=True)

        st.subheader("🛡️ Ficha e QR Code")
        col_f, col_q = st.columns([2, 1])

        with col_f:
            sel = st.selectbox("Selecione:", df['nome'].tolist())
            det = df[df['nome'] == sel].iloc[0]

            
            css_txt = ""
            if os.path.exists("CSS/substancias.css"):
                with open("CSS/substancias.css", "r") as f_css:
                    css_txt = f_css.read()

            html_hommel = f"""
            <style>{css_txt}</style>
            <div class="hommel-container">
                <div class="hommel-box">
                    <div class="f_vermelho">{det['fogo']}</div>
                    <div class="r_amarelo">{det['reatividade']}</div>
                    <div class="s_azul">{det['saude']}</div>
                    <div class="e_branco">{det['especial'] if det['especial'] else ''}</div>
                </div>
            </div>
            """
            st.markdown(html_hommel, unsafe_allow_html=True)
            st.info(f"**Instruções:** {det['instrucoes']}")

        with col_q:
            url_serv = st.text_input("URL Base:", f"https://{org_usuario.lower()}.lab.com/")
            qr_link = f"{url_serv}{det['id']}.html"
            qr_img = qrcode.make(qr_link)
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=150)
            st.download_button("Baixar QR", buf.getvalue(), f"qr_{sel}.png")

