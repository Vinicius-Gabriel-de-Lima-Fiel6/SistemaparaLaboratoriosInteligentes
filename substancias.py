import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO

# --- CONEXÃO COM O BANCO DE DADOS ---
# Utilizando as chaves configuradas nos Secrets do Streamlit
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")

# --- FUNÇÃO AUXILIAR: DIAMANTE DE HOMMEL (NFPA 704) ---
def render_hommel(saude, fogo, reat, esp):
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;">
        <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555;">
            <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{fogo}</div>
            <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">{reat}</div>
            <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{saude}</div>
            <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-size: 0.7em;">{esp if esp else ''}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_substances():
    # Recuperando dados do usuário e organização
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. SEÇÃO DE CONSULTA (ORIGINAL E NO TOPO) ---
    st.header("🛡️ Consulta de Segurança (FISPQ Digital)")
    
    try:
        # Busca os dados atuais da organização
        res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            # Menu de seleção para consulta
            substancia_alvo = st.selectbox("Selecione um item para ver a ficha:", df['nome'].tolist(), key="consulta_fispq")
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            
            col_v, col_t = st.columns([1, 3])
            with col_v:
                render_hommel(detalhes['saude'], detalhes['fogo'], detalhes['reatividade'], detalhes.get('especial', ''))
            with col_t:
                st.warning(f"**Instruções de Emergência:**\n\n{detalhes.get('instrucoes', 'Não informadas.')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')} | Validade: {detalhes.get('validade', 'N/A')}")
        else:
            st.info("Nenhum item disponível para consulta. Cadastre uma substância abaixo.")

    except Exception as e:
        st.error(f"Erro ao carregar dados de consulta: {e}")

    st.divider()

    # --- 2. CADASTRO DE SUBSTÂNCIAS ---
    st.subheader("➕ Cadastro de Nova Substância")
    
    if role_usuario == "Visualizador":
        st.warning("Você não tem permissão para adicionar novos itens.")
    else:
        with st.form("cadastro_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nome_cad = c1.text_input("Nome da Substância")
            qtd_cad = c2.number_input("Quantidade Atual", min_value=0.0, step=0.1)
            val_cad = c3.text_input("Validade (MM/AAAA)")
            
            with st.expander("Informações de Segurança (NFPA 704)"):
                cs1, cs2, cs3, cs4 = st.columns(4)
                s_val = cs1.slider("Saúde", 0, 4, 0)
                f_val = cs2.slider("Fogo", 0, 4, 0)
                r_val = cs3.slider("Reat.", 0, 4, 0)
                e_val = cs4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                inst_cad = st.text_area("Instruções de Emergência")

            if st.form_submit_button("ADICIONAR AO INVENTÁRIO", use_container_width=True):
                if nome_cad:
                    # Alimenta apenas a tabela substancias (o log será via Trigger SQL no banco)
                    novo_item = {
                        "nome": nome_cad, "quantidade": qtd_cad, "validade": val_cad,
                        "org_name": org_usuario, "saude": s_val, "fogo": f_val, 
                        "reatividade": r_val, "especial": e_val, "instrucoes": inst_cad
                    }
                    supabase.table("substancias").insert(novo_item).execute()
                    st.success(f"Item '{nome_cad}' cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("O campo 'Nome' é obrigatório.")

    # --- 3. SEÇÃO DE QR CODE (ABA ABAIXO) ---
    if not df.empty:
        st.divider()
        st.subheader("🏷️ Gerador de Etiquetas Inteligentes")
        
        col_sel_qr, col_img_qr = st.columns([2, 1])
        
        with col_sel_qr:
            st.write("Selecione um item para gerar o QR Code de acesso mobile:")
            item_p_qr = st.selectbox("Gerar QR para:", df['nome'].tolist(), key="qr_aba_inferior")
            id_p_qr = df[df['nome'] == item_p_qr]['id'].values[0]
            
            # Link para o sistema externo de leitura
            url_leitor = f"https://sistemadeqrcodes.streamlit.app/?id={id_p_qr}"
            st.text_input("Link da Etiqueta:", value=url_leitor, disabled=True)

        with col_img_qr:
            qr = qrcode.make(url_leitor)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf.getvalue(), width=150, caption=f"Etiqueta: {item_p_qr}")
            st.download_button("📥 Baixar QR Code", buf.getvalue(), f"qr_{item_p_qr}.png")

    # --- 4. EXCLUSÃO DE ITENS ---
    if not df.empty and role_usuario in ["ADM", "Tecnico"]:
        st.divider()
        with st.expander("🗑️ Área de Exclusão"):
            item_del = st.selectbox("Selecione o item para remover:", df['nome'].tolist(), key="delete_item")
            if st.button(f"CONFIRMAR EXCLUSÃO DE {item_del}", type="primary", use_container_width=True):
                id_del = df[df['nome'] == item_del]['id'].values[0]
                supabase.table("substancias").delete().eq("id", id_del).execute()
                st.success(f"Item {item_del} removido.")
                st.rerun()

if __name__ == "__main__":
    show_substances()
