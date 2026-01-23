import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import os
import zipfile

# Conexão com o Banco de Dados
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
    # --- CARREGAMENTO DO ESTILO EXTERNO ---
    if os.path.exists("CSS/style_subst.css"):
        with open("CSS/style_subst.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    # --- 1. CADASTRO ---
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
                estoque_minimo = st.number_input("Estoque Mínimo (Alerta)", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Número CAS (Opcional)")

            with st.expander("🛡️ Informações de Segurança (FISPQ/MSDS)"):
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
                    registrar_historico("Cadastro", nome, "Inserção via sistema", user_data)
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    # --- 2. INVENTÁRIO ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            st.subheader("🛡️ Consulta de Segurança e QR Code")
            substancia_alvo = st.selectbox("Selecione um item:", options=df['nome'].tolist())
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            
            col_vis, col_txt, col_qr = st.columns([1.5, 2.5, 1.5])
            
            with col_vis:
                css_content = ""
                if os.path.exists("CSS/substancias.css"):
                    with open("CSS/substancias.css", "r") as f:
                        css_content = f.read()
                
                # MANTIDO: Sua estrutura original de replace
                html_template = """
                <style>__CSS__</style>
                <div style="display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;">
                    <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555;">
                        <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">__FOGO__</div>
                        <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">__REAT__</div>
                        <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">__SAUDE__</div>
                        <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold; font-size: 0.7em;">__ESP__</div>
                    </div>
                </div>
                """
                render = html_template.replace("__CSS__", css_content)
                render = render.replace("__FOGO__", str(detalhes.get('fogo', 0)))
                render = render.replace("__REAT__", str(detalhes.get('reatividade', 0)))
                render = render.replace("__SAUDE__", str(detalhes.get('saude', 0)))
                render = render.replace("__ESP__", str(detalhes.get('especial', '')))
                st.markdown(render, unsafe_allow_html=True)

            with col_txt:
                st.warning(f"**Emergência:**\n\n{detalhes.get('instrucoes', 'N/A')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')}")

            with col_qr:
                # O Link agora aponta para o portal online que receberá o ID
                url_portal = st.text_input("Link do Portal Online:", "https://portal-online.streamlit.app")
                qr_link = f"{url_portal}?id={detalhes['id']}&org={org_usuario.replace(' ', '%20')}"
                
                img_qr = qrcode.make(qr_link)
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                st.image(buf.getvalue(), width=130, caption="QR Ficha Digital")
                st.download_button("📥 Baixar QR", buf.getvalue(), f"qr_{substancia_alvo}.png", use_container_width=True)

            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("⚙️ Ferramentas de Administrador (Massa)"):
                    if st.button("📦 Gerar Tudo (ZIP de HTML e QR Codes)"):
                        zip_buf = BytesIO()
                        with zipfile.ZipFile(zip_buf, "a") as z:
                            if os.path.exists("HTML/substancias.html"):
                                with open("HTML/substancias.html", "r") as f:
                                    tmpl = f.read()
                                for _, r in df.iterrows():
                                    h = tmpl
                                    for col in r.index: h = h.replace(f"{{{{{col}}}}}", str(r[col]))
                                    z.writestr(f"fichas/{r['id']}.html", h)
                                    
                                    q = qrcode.make(f"{url_portal}?id={r['id']}&org={org_usuario.replace(' ', '%20')}")
                                    b = BytesIO()
                                    q.save(b, format="PNG")
                                    z.writestr(f"qrcodes/qr_{r['nome']}.png", b.getvalue())
                        st.download_button("📥 Baixar Projeto Completo", zip_buf.getvalue(), "estoque_digital.zip")

    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
