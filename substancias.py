import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile

# Conexão com o Banco de Dados
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_historico(acao, item, qtd, detalhes, user_data):
    """Grava na tabela historico_atividades conforme as colunas do seu banco"""
    log = {
        "usuario_email": user_data.get('email') or user_data.get('username') or "sistema@empresa.com",
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": item,
        "quantidade": str(qtd),
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log).execute()
    except:
        pass

def show_substances():
    # --- CARREGA O CSS DA PASTA CSS ---
    try:
        with open("CSS/style_subst.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    # Título com ícone conforme sua imagem
    st.markdown("<h1>🔬 Cadastro e Gerenciamento de Substâncias</h1>", unsafe_allow_html=True)
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. SEU CADASTRO ORIGINAL (IGUAL À CAPTURA DE TELA) ---
    with st.container(border=True):
        st.markdown("<h2 class='sub-header'>Cadastrar Novo Item</h2>", unsafe_allow_html=True)
        
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
                    registrar_historico("CADASTRO", nome, quantidade, "Sucesso", user_data)
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    # --- 2. INVENTÁRIO E QR CODE ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            st.markdown("<h3 style='color: white;'>🖼️ Gerador de Etiquetas QR</h3>", unsafe_allow_html=True)
            url_portal = st.text_input("Link do Portal Online:", "https://seu-portal.streamlit.app")
            
            sel_item = st.selectbox("Selecione o item:", df['nome'].tolist())
            det = df[df['nome'] == sel_item].iloc[0]

            link_final = f"{url_portal}?id={det['id']}&org={org_usuario.replace(' ', '%20')}"
            
            qr_img = qrcode.make(link_final)
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(buf.getvalue(), width=150)
            with c2:
                st.download_button("📥 Baixar QR Individual", buf.getvalue(), f"QR_{sel_item}.png")
                if st.button("📦 Gerar ZIP da Empresa"):
                    zip_buf = BytesIO()
                    with zipfile.ZipFile(zip_buf, "w") as z:
                        for _, r in df.iterrows():
                            lnk = f"{url_portal}?id={r['id']}&org={org_usuario.replace(' ', '%20')}"
                            q = qrcode.make(lnk)
                            b = BytesIO()
                            q.save(b, format="PNG")
                            z.writestr(f"QR_{r['nome']}.png", b.getvalue())
                    st.download_button("📥 Baixar ZIP", zip_buf.getvalue(), "etiquetas.zip")
    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
