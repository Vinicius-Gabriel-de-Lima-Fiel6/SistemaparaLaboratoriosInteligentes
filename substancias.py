import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
import zipfile
from io import BytesIO
import os

# Conexão com Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_log(acao, substancia, qtd, detalhes):
    """
    Registra toda e qualquer alteração na tabela historico_atividades.
    Mantém o rastro de QUEM fez, O QUE fez e QUAL substância foi afetada.
    """
    user_data = st.session_state.get('user_data', {})
    log_data = {
        "usuario_email": user_data.get('email', 'usuario_desconhecido@lab.com'),
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia,
        "quantidade": str(qtd),
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log_data).execute() # Tabela conforme sua imagem
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {e}")

def carregar_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()

def show_substances():
    st.header("🔬 Sistema de Gestão e Segurança")
    user_data = st.session_state.get('user_data', {})
    org = user_data.get('org_name', 'Default')

    # 1. BUSCA DE DADOS
    res = supabase.table("substancias").select("*").eq("org_name", org).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # --- SEÇÃO DE QR CODES ---
        st.subheader("🖼️ Gerador de QR Codes")
        url_base = st.text_input("URL das Fichas:", f"https://{org.lower()}.lab.com/item/")
        
        c1, c2 = st.columns(2)
        with c1:
            item_qr = st.selectbox("QR Individual:", df['nome'].tolist())
            if st.button("Gerar QR Selecionado"):
                row = df[df['nome'] == item_qr].iloc[0]
                qr = qrcode.make(f"{url_base}{row['id']}")
                buf = BytesIO()
                qr.save(buf, format="PNG")
                st.image(buf.getvalue(), width=150)
                registrar_log("QR_GERADO", item_qr, row['quantidade'], "Gerou QR Code individual.")

        with c2:
            st.write("Lote completo:")
            if st.button("📦 Baixar Todos (ZIP)"):
                zip_buf = BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as z:
                    for _, r in df.iterrows():
                        qr = qrcode.make(f"{url_base}{r['id']}")
                        b = BytesIO()
                        qr.save(b, format="PNG")
                        z.writestr(f"qrcodes/qr_{r['nome']}.png", b.getvalue())
                
                st.download_button("📥 Baixar ZIP", zip_buf.getvalue(), "todos_qrcodes.zip")
                registrar_log("EXPORTACAO_ZIP", "Múltiplos", 0, f"Exportou {len(df)} itens em lote.")

        # --- SEÇÃO DE VISUALIZAÇÃO (HTML/CSS) ---
        st.divider()
        st.subheader("👁️ Visualização de Segurança")
        selecionado = st.selectbox("Escolha a substância:", df['nome'].tolist(), key="vis")
        
        # Preparação do HTML
        dados_item = df[df['nome'] == selecionado].iloc[0].to_dict()
        css = carregar_arquivo("CSS/substancias.css")
        html_template = carregar_arquivo("HTML/card_template.html")

        # Substituição de tags no HTML
        for campo, valor in dados_item.items():
            html_template = html_template.replace(f"{{{{{campo}}}}}", str(valor if valor else "None"))

        # RENDERIZAÇÃO CORRETA
        st.markdown(f"<style>{css}</style>{html_template}", unsafe_allow_html=True)
        
        # Log de Consulta
        registrar_log("CONSULTA_SEGURANÇA", selecionado, dados_item['quantidade'], "Visualizou ficha técnica.")

    else:
        st.warning("Nenhuma substância encontrada para esta organização.")

if __name__ == "__main__":
    show_substances()
