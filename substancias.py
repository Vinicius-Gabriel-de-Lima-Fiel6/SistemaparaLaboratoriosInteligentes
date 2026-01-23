import streamlit as st
import pandas as pd
from supabase import create_client
import qrcode
from io import BytesIO
import os

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_substances():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')

    st.title(f"🧪 Estoque - {org_usuario}")

    res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        st.dataframe(df[['nome', 'quantidade', 'validade']], use_container_width=True)
        st.divider()

        col_f, col_q = st.columns([2, 1])

        with col_f:
            sel = st.selectbox("Substância:", df['nome'].tolist())
            det = df[df['nome'] == sel].iloc[0]

            # 1. PEGA O CSS SEM INTERPRETAR
            css_content = ""
            if os.path.exists("CSS/substancias.css"):
                with open("CSS/substancias.css", "r") as f:
                    css_content = f.read()

            # 2. MONTA O HTML COMO STRING PURA (SEM F-STRING PARA NÃO VAZAR)
            template_html = """
            <style>__CSS__</style>
            <div class="hommel-container">
                <div class="hommel-box">
                    <div class="f_vermelho">__F__</div>
                    <div class="r_amarelo">__R__</div>
                    <div class="s_azul">__S__</div>
                    <div class="e_branco">__E__</div>
                </div>
            </div>
            """
            
            # 3. SUBSTITUIÇÃO MANUAL (MAIS SEGURO QUE F-STRING)
            render = template_html.replace("__CSS__", css_content)
            render = render.replace("__F__", str(det['fogo']))
            render = render.replace("__R__", str(det['reatividade']))
            render = render.replace("__S__", str(det['saude']))
            render = render.replace("__E__", str(det['especial'] if det['especial'] else ""))

            # 4. RENDERIZAÇÃO FINAL
            st.markdown(render, unsafe_allow_html=True)
            
            st.info(f"**Instruções:** {det['instrucoes']}")

        with col_q:
            url_serv = st.text_input("URL:", f"https://{org_usuario.lower().replace(' ','')}.lab.com/")
            qr_img = qrcode.make(f"{url_serv}{det['id']}.html")
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=150)
            st.download_button("Baixar QR", buf.getvalue(), f"qr_{sel}.png")

if __name__ == "__main__":
    show_substances()
