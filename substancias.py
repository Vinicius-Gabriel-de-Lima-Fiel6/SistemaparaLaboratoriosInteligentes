import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import os
import zipfile

# CONFIGURAÇÃO DO CLIENTE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_historico(acao, item, detalhes, user_data):
    log = {
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
        supabase.table("historico").insert(log).execute()
    except:
        pass

def show_substances():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    st.title(f"🧪 Controle de Substâncias - {org_usuario}")

    # --- SUA LÓGICA DE CADASTRO ORIGINAL ---
    with st.expander("➕ Cadastrar Nova Substância", expanded=False):
        if role_usuario == "Visualizador":
            st.warning("Você não tem permissão para cadastrar.")
        else:
            with st.form("form_cadastro", clear_on_submit=True):
                col1, col2 = st.columns(2)
                nome = col1.text_input("Nome da Substância")
                cas = col1.text_input("Número CAS")
                concentracao = col2.text_input("Concentração")
                quantidade = col2.number_input("Quantidade Atual", min_value=0.0)
                
                st.write("**Segurança (NFPA 704)**")
                s1, s2, s3, s4 = st.columns(4)
                fogo = s1.slider("Fogo", 0, 4, 0)
                saude = s2.slider("Saúde", 0, 4, 0)
                reatividade = s3.slider("Reatividade", 0, 4, 0)
                especial = s4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                
                instrucoes = st.text_area("Instruções de Emergência")
                validade = st.text_input("Validade (MM/AAAA)")

                if st.form_submit_button("Salvar Substância"):
                    if nome:
                        dados = {
                            "nome": nome, "cas": cas, "concentracao": concentracao,
                            "quantidade": quantidade, "fogo": fogo, "saude": saude,
                            "reatividade": reatividade, "especial": especial,
                            "instrucoes": instrucoes, "validade": validade,
                            "org_name": org_usuario
                        }
                        supabase.table("substancias").insert(dados).execute()
                        registrar_historico("Cadastro", nome, "Novo item adicionado", user_data)
                        st.success("Cadastrado com sucesso!")
                        st.rerun()

    # --- VISUALIZAÇÃO DO ESTOQUE ---
    res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        st.divider()
        st.subheader("Estoque Atual")
        st.dataframe(df[['nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

        # --- SEÇÃO DE SEGURANÇA E QR CODE (CORRIGIDA) ---
        st.divider()
        st.subheader("🛡️ Ficha de Segurança e QR Code")
        
        col_sel, col_qr = st.columns([2, 1])
        
        with col_sel:
            item_nome = st.selectbox("Selecione para ver a Ficha:", df['nome'].tolist())
            det = df[df['nome'] == item_nome].iloc[0]
            
            # Carregar CSS externo (Pasta CSS)
            estilo_css = ""
            if os.path.exists("CSS/substancias.css"):
                with open("CSS/substancias.css", "r") as f:
                    estilo_css = f"<style>{f.read()}</style>"
            
            # Renderização forçada como HTML (Isso remove os códigos da tela)
            html_hommel = f"""
            <div class="hommel-container">
                <div class="hommel-box">
                    <div class="f_vermelho">{det['fogo']}</div>
                    <div class="r_amarelo">{det['reatividade']}</div>
                    <div class="s_azul">{det['saude']}</div>
                    <div class="e_branco">{det['especial'] if det['especial'] else ''}</div>
                </div>
            </div>
            """
            st.markdown(estilo_css + html_hommel, unsafe_allow_html=True)
            
            st.warning(f"**Procedimentos de Emergência:**\n\n{det['instrucoes']}")

        with col_qr:
            # Lógica de TI: URL dinâmica por Organização
            url_servidor = st.text_input("Link do Servidor (TI):", f"https://{org_usuario.lower().replace(' ','')}.lab.com/")
            link_final = f"{url_servidor}{det['id']}.html"
            
            qr = qrcode.make(link_final)
            img_buf = BytesIO()
            qr.save(img_buf, format="PNG")
            
            st.image(img_buf.getvalue(), width=200, caption=f"QR Code: {item_nome}")
            st.download_button("📥 Baixar Imagem QR", img_buf.getvalue(), f"qr_{item_nome}.png", "image/png")

        # --- FERRAMENTAS EXCLUSIVAS DE TI ---
        st.divider()
        with st.expander("🛠️ Console de Administração (TI)"):
            c1, c2 = st.columns(2)
            
            if c1.button("📦 Gerar ZIP de QR Codes"):
                buf_zip = BytesIO()
                with zipfile.ZipFile(buf_zip, "a") as z:
                    for _, r in df.iterrows():
                        img_qr = qrcode.make(f"{url_servidor}{r['id']}.html")
                        b = BytesIO()
                        img_qr.save(b, format="PNG")
                        z.writestr(f"qrcodes/qr_{r['nome']}.png", b.getvalue())
                st.download_button("Baixar Todos QRs", buf_zip.getvalue(), "qrcodes.zip")

            if c2.button("🌐 Exportar HTMLs para Servidor"):
                buf_html = BytesIO()
                with zipfile.ZipFile(buf_html, "a") as z:
                    if os.path.exists("CSS/substancias.css"):
                        with open("CSS/substancias.css", "r") as f:
                            z.writestr("substancias.css", f.read())
                    if os.path.exists("HTML/substancias.html"):
                        with open("HTML/substancias.html", "r") as f:
                            tmpl = f.read()
                        for _, r in df.iterrows():
                            # Substitui os marcadores {{campo}} pelos dados do banco
                            pag = tmpl
                            for col in r.index:
                                pag = pag.replace(f"{{{{{col}}}}}", str(r[col]))
                            z.writestr(f"fichas/{r['id']}.html", pag)
                st.download_button("Baixar Site Estático", buf_html.getvalue(), "site_fichas.zip")

if __name__ == "__main__":
    show_substances()
