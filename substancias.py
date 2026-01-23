import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
import zipfile
from io import BytesIO
import os

# Conexão Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_historico(acao, substancia, qtd, detalhes):
    """Alimenta a tabela 'historico_atividades' conforme o esquema oficial."""
    user_data = st.session_state.get('user_data', {})
    log = {
        "usuario_email": user_data.get('email', 'sistema@lab.com'),
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia,
        "quantidade": str(qtd),
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log).execute()
    except Exception as e:
        st.error(f"Erro de Log: {e}")

def show_substances():
    st.header("🔬 Gestão de Inventário e Segurança")
    user_data = st.session_state.get('user_data', {})
    org = user_data.get('org_name', 'Default')

    # --- CONSULTA DE DADOS ---
    res = supabase.table("substancias").select("*").eq("org_name", org).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # --- SISTEMA DE QR CODE (LOTE E INDIVIDUAL) ---
        st.subheader("🖼️ Geração de QR Codes")
        url_base = st.text_input("URL das Fichas:", "https://seulab.com/item/")
        
        col_qr1, col_qr2 = st.columns(2)
        with col_qr1:
            if st.button("📦 Gerar Todos (ZIP)"):
                zip_buf = BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as z:
                    for _, r in df.iterrows():
                        img = qrcode.make(f"{url_base}{r['id']}")
                        b = BytesIO()
                        img.save(b, format="PNG")
                        z.writestr(f"qr_{r['nome']}.png", b.getvalue())
                st.download_button("📥 Baixar ZIP", zip_buf.getvalue(), "qrcodes.zip")
                registrar_historico("DOWNLOAD_LOTE", "Multiplos", 0, "Gerou ZIP com todos os QR Codes")

        # --- VISUALIZAÇÃO DE SEGURANÇA (HTML RENDERIZADO) ---
        st.divider()
        st.subheader("👁️ Visualização de Segurança")
        substancia_alvo = st.selectbox("Ver detalhes de:", df['nome'].tolist())
        detalhes = df[df['nome'] == substancia_alvo].iloc[0].to_dict()

        # Carregar arquivos externos
        with open("CSS/substancias.css", "r") as f:
            css_content = f.read()
        with open("HTML/card_template.html", "r") as f:
            html_template = f.read()

        # Substituir variáveis no HTML
        for key, value in detalhes.items():
            html_template = html_template.replace(f"{{{{{key}}}}}", str(value if value else "N/A"))

        # RENDERIZAÇÃO FINAL (O segredo para não aparecer como texto)
        render_final = f"<style>{css_content}</style>{html_template}"
        st.markdown(render_final, unsafe_allow_html=True)
        
        # Log de Visualização
        registrar_historico("VISUALIZACAO", substancia_alvo, 0, f"Consultou ficha de segurança de {substancia_alvo}")

if __name__ == "__main__":
    show_substances()
