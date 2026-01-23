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

    # --- SUA LÓGICA DE VISUALIZAÇÃO ORIGINAL ---
    res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        st.divider()
        st.subheader("Estoque Atual")
        st.dataframe(df[['nome', 'cas', 'quantidade', 'validade']], use_container_width=True)

        # --- ABA DE SEGURANÇA E QR CODE (O QUE VOCÊ PEDIU) ---
        st.divider()
        st.subheader("🛡️ Ficha de Segurança e QR Code")
        
        col_sel, col_qr = st.columns([2, 1])
        
        with col_sel:
            item_nome = st.selectbox("Selecione para ver a Ficha:", df['nome'].tolist())
            det = df[df['nome'] == item_nome].iloc[0]
            
            # Carregar CSS da pasta CSS/
            estilo = ""
            if os.path.exists("CSS/substancias.css"):
                with open("CSS/substancias.css", "r") as f:
                    estilo = f"<style>{f.read()}</style>"
            
            # Renderizar Diamante (Sem vazar código)
            st.markdown(estilo + f"""
            <div class="hommel-container">
                <div class="hommel-box">
                    <div class="f_vermelho">{det['fogo']}</div>
                    <div class="r_amarelo">{det['reatividade']}</div>
                    <div class="s_azul">{det['saude']}</div>
                    <div class="e_branco">{det['especial']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.warning(f"**Procedimentos:** {det['instrucoes']}")

        with col_qr:
            url_servidor = st.text_input("URL do Servidor:", f"https://{org_usuario.lower()}.lab.com/")
            link_qr = f"{url_servidor}{det['id']}.html"
            
            qr = qrcode.make(link_qr)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf.getvalue(), width=200, caption=f"QR Code: {item_nome}")
            st.download_button("📥 Baixar QR Code", buf.getvalue(), f"qr_{item_nome}.png", "image/png")

        # --- FERRAMENTAS DE TI (ZIP) ---
        with st.expander("🛠️ Ferramentas de TI - Gerar Tudo"):
            if st.button("Gerar ZIP com todos os HTMLs e QRs"):
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "a") as z:
                    # Inclui CSS
                    if os.path.exists("CSS/substancias.css"):
                        with open("CSS/substancias.css", "r") as f:
                            z.writestr("substancias.css", f.read())
                    
                    # Inclui HTMLs e QRs
                    with open("HTML/substancias.html", "r") as f:
                        template = f.read()
                        
                    for _, r in df.iterrows():
                        # HTML
                        h = template
                        for k in r.index: h = h.replace(f"{{{{{k}}}}}", str(r[k]))
                        z.writestr(f"fichas/{r['id']}.html", h)
                        # QR
                        img = qrcode.make(f"{url_servidor}{r['id']}.html")
                        img_b = BytesIO()
                        img.save(img_b, format="PNG")
                        z.writestr(f"qrcodes/qr_{r['nome']}.png", img_b.getvalue())
                
                st.download_button("📥 Baixar Pacote Completo", zip_buffer.getvalue(), "projeto_ti.zip")
