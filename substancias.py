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

# --- FUNÇÃO: REGISTRAR NA TABELA DA FOTO (historico_atividades) ---
def registrar_log_atividades(acao, substancia, quantidade, detalhes, user_data):
    log = {
        "usuario_email": user_data.get('email', 'usuario@lab.com'),
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia,
        "quantidade": str(quantidade), 
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log).execute()
    except:
        pass

# --- FUNÇÃO AUXILIAR: RENDERIZAR DIAMANTE DE HOMMEL ---
def render_hommel(saude, fogo, reat, esp):
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;">
        <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555;">
            <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{fogo}</div>
            <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">{reat}</div>
            <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{saude}</div>
            <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold; font-size: 0.7em;">{esp if esp else ''}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_substances():
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. CADASTRO DE SUBSTÂNCIAS ---
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
                if nome:
                    # AJUSTADO PARA OS NOMES DA SUA FOTO
                    data_insert = {
                        "nome": nome, 
                        "finalidade": finalidade, 
                        "concentracao": concentracao,
                        "quantidade": quantidade, 
                        "estoque_minimo": estoque_minimo,
                        "validade": validade, 
                        "org_name": org_usuario, 
                        "cas": cas,
                        "saude": s_saude, 
                        "fogo": s_fogo, 
                        "reatividade": s_reat, # nome exato da foto
                        "especial": s_esp, 
                        "instrucoes": instrucoes
                    }
                    try:
                        supabase.table("substancias").insert(data_insert).execute()
                        registrar_log_atividades("Cadastro", nome, quantidade, "Inserção via sistema", user_data)
                        st.success(f"'{nome}' cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    st.divider()

    # --- 2. EXIBIÇÃO DO INVENTÁRIO ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.subheader(f"📋 Inventário: {org_usuario}")
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            # --- CONSULTA DE SEGURANÇA (NO TOPO) ---
            st.subheader("🛡️ Consulta de Segurança (FISPQ Digital)")
            substancia_alvo = st.selectbox("Selecione um item:", options=df['nome'].tolist())
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            
            col_visual, col_texto = st.columns([1, 3])
            with col_visual:
                render_hommel(detalhes.get('saude', 0), detalhes.get('fogo', 0), detalhes.get('reatividade', 0), detalhes.get('especial', ''))
            with col_texto:
                st.warning(f"**Instruções:**\n\n{detalhes.get('instrucoes', 'N/A')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')}")

            st.divider()

            # --- ABA ABAIXO: QR CODE ---
            st.subheader("🏷️ Gerador de Etiquetas (QR Code)")
            url_final = f"https://sistemadeqrcodes.streamlit.app/?id={detalhes['id']}"
            
            col_q1, col_q2 = st.columns([2, 1])
            with col_q1:
                st.write(f"QR Code para: **{substancia_alvo}**")
                if st.button("📦 Gerar ZIP de QRs"):
                    zip_buf = BytesIO()
                    with zipfile.ZipFile(zip_buf, "a") as z:
                        for _, r in df.iterrows():
                            link_z = f"https://sistemadeqrcodes.streamlit.app/?id={r['id']}"
                            q_z = qrcode.make(link_z)
                            b_z = BytesIO()
                            q_z.save(b_z, format="PNG")
                            z.writestr(f"qr_{r['nome']}.png", b_z.getvalue())
                    st.download_button("📥 Baixar ZIP", zip_buf.getvalue(), "etiquetas.zip")

            with col_q2:
                img_qr = qrcode.make(url_final)
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                st.image(buf.getvalue(), width=150)

    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
