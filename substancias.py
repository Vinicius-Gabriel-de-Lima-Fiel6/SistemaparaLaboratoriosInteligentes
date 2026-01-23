import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile

# --- CONEXÃO ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

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
        # Força a inserção e captura a resposta para garantir que não passou em branco
        res = supabase.table("historico_atividades").insert(log).execute()
        if res.data:
            return True
    except Exception as e:
        st.error(f"FALHA NO HISTÓRICO: {str(e)}")
    return False

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
    st.header("🔬 Controle de Laboratório")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. CADASTRO ---
    with st.container(border=True):
        st.subheader("➕ Adicionar Nova Substância")
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome")
        qtd = c2.number_input("Quantidade", min_value=0.0, step=0.1)
        val = c3.text_input("Validade (MM/AAAA)")
        
        with st.expander("🛡️ Segurança e FISPQ"):
            c_s1, c_s2, c_s3, c_s4 = st.columns(4)
            s_s = c_s1.slider("Saúde", 0, 4, 0)
            s_f = c_s2.slider("Fogo", 0, 4, 0)
            s_r = c_s3.slider("Reatividade", 0, 4, 0)
            s_e = c_s4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
            inst = st.text_area("Instruções")

        if st.button("💾 SALVAR ITEM E LOG", use_container_width=True, type="primary"):
            if nome:
                with st.spinner("Gravando..."):
                    # Inserção Inventário
                    supabase.table("substancias").insert({
                        "nome": nome, "quantidade": qtd, "validade": val, 
                        "org_name": org_usuario, "saude": s_s, "fogo": s_f, 
                        "reatividade": s_r, "especial": s_e, "instrucoes": inst
                    }).execute()
                    
                    # Inserção Histórico
                    log_ok = registrar_log_atividades("CADASTRO", nome, qtd, "Item adicionado", user_data)
                    
                    if log_ok:
                        st.success(f"✅ Sucesso: {nome} cadastrado e histórico atualizado!")
                    else:
                        st.warning("⚠️ Item salvo, mas falha ao registrar histórico (Verifique RLS).")
                    st.rerun()
            else:
                st.error("❌ O nome da substância é obrigatório!")

    # --- 2. CONSULTA E QR ---
    try:
        res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.divider()
            st.subheader("📋 Inventário Atual")
            st.dataframe(df[['id', 'nome', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            st.subheader("🔍 Detalhes de Segurança")
            # Menu suspenso para consulta
            item_ver = st.selectbox("Selecione para consultar:", df['nome'].tolist(), key="ver_detalhes")
            det = df[df['nome'] == item_ver].iloc[0]
            
            col_v, col_t = st.columns([1, 3])
            with col_v:
                render_hommel(det['saude'], det['fogo'], det['reatividade'], det.get('especial', ''))
            with col_t:
                st.info(f"**Instruções:** {det.get('instrucoes', 'N/A')}")

            # --- 3. ETIQUETAS ---
            st.divider()
            st.subheader("🏷️ Gerar QR Code")
            url_qr = f"https://sistemadeqrcodes.streamlit.app/?id={det['id']}"
            qr_img = qrcode.make(url_qr)
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=150)
            st.download_button("📥 Baixar QR", buf.getvalue(), f"qr_{item_ver}.png")

            # --- 4. EXCLUSÃO (CORRIGIDO) ---
            if role_usuario in ["ADM", "Tecnico"]:
                st.divider()
                with st.expander("🚨 ÁREA DE EXCLUSÃO"):
                    st.write("Selecione o item para deletar permanentemente:")
                    # Menu suspenso específico para deletar
                    item_deletar = st.selectbox("Item para REMOVER:", df['nome'].tolist(), key="del_box")
                    id_deletar = df[df['nome'] == item_deletar]['id'].values[0]
                    
                    if st.button(f"🗑️ EXCLUIR {item_deletar}", type="primary", use_container_width=True):
                        supabase.table("substancias").delete().eq("id", id_deletar).execute()
                        registrar_log_atividades("EXCLUSÃO", item_deletar, "0", "Removido via painel", user_data)
                        st.success("Item removido!")
                        st.rerun()
        else:
            st.info("Nenhum item encontrado.")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

if __name__ == "__main__":
    show_substances()
