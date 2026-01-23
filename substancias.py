import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile

# --- CONFIGURAÇÃO DA PÁGINA ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

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
    username_atual = user_data.get('username', 'Usuário')

    # --- 1. CADASTRO ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        if role_usuario == "Visualizador":
            st.warning("Apenas visualização.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substância")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentração")
                quantidade = st.number_input("Quantidade Atual", min_value=0.0)
            with col3:
                estoque_minimo = st.number_input("Estoque Mínimo", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("CAS (Opcional)")

            with st.expander("🛡️ Segurança"):
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
                    # LOG DE CADASTRO
                    supabase.table("logs_estoque").insert({
                        "usuario": username_atual, "substancia": nome,
                        "quantidade_antiga": 0.0, "quantidade_nova": float(quantidade), "org_name": org_usuario
                    }).execute()
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    # --- 2. INVENTÁRIO E EXPORTAÇÃO ---
    try:
        res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            st.subheader(f"📋 Inventário: {org_usuario}")
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'estoque_minimo', 'validade']], use_container_width=True, hide_index=True)

            col_exp1, col_exp2 = st.columns(2)
            csv = df.to_csv(index=False).encode('utf-8')
            col_exp1.download_button("📥 Baixar CSV", csv, f"estoque.csv", "text/csv", use_container_width=True)
            
            buf_zip = BytesIO()
            with zipfile.ZipFile(buf_zip, 'w') as zf:
                for _, row in df.iterrows():
                    qr = qrcode.make(f"Item: {row['nome']}\nCAS: {row.get('cas','N/A')}")
                    img_buf = BytesIO(); qr.save(img_buf, format="PNG")
                    zf.writestr(f"qr_{row['nome']}.png", img_buf.getvalue())
            col_exp2.download_button("🖼️ Gerar Todos QRs (ZIP)", buf_zip.getvalue(), "qrcodes.zip", "application/zip", use_container_width=True)

            # --- ATUALIZAÇÃO ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🔄 Atualizar Estoque"):
                    c_sel, c_val, c_btn = st.columns([2, 1, 1])
                    sub_edit = c_sel.selectbox("Substância", options=df['nome'].tolist())
                    nova_qtd = c_val.number_input("Nova Qtd", min_value=0.0)
                    if c_btn.button("Atualizar", use_container_width=True):
                        qtd_ant = df[df['nome'] == sub_edit]['quantidade'].values[0]
                        supabase.table("substancias").update({"quantidade": nova_qtd}).eq("nome", sub_edit).execute()
                        # LOG DE ALTERAÇÃO
                        supabase.table("logs_estoque").insert({
                            "usuario": username_atual, "substancia": sub_edit,
                            "quantidade_antiga": float(qtd_ant), "quantidade_nova": float(nova_qtd), "org_name": org_usuario
                        }).execute()
                        st.rerun()

            # --- SEGURANÇA E QR ---
            st.subheader("🛡️ Segurança")
            sub_fispq = st.selectbox("Selecione para detalhes:", options=df['nome'].tolist())
            det = df[df['nome'] == sub_fispq].iloc[0]
            v1, v2, v3 = st.columns([1, 2, 1])
            with v1: render_hommel(det['saude'], det['fogo'], det['reatividade'], det['especial'])
            with v2: st.warning(det.get('instrucoes', 'Sem instruções.'))
            with v3:
                qr_ind = qrcode.make(f"Substancia: {det['nome']}\nCAS: {det['cas']}")
                b = BytesIO(); qr_ind.save(b, format="PNG")
                st.image(b.getvalue(), width=120)
                st.download_button("📥 Baixar QR", b.getvalue(), "qr.png", "image/png")

            # --- EXCLUSÃO ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover Item"):
                    id_del = st.selectbox("ID para remover", options=df['id'].tolist())
                    item_del = df[df['id'] == id_del].iloc[0]
                    if st.button("Confirmar Exclusão", type="primary"):
                        # LOG DE EXCLUSÃO
                        supabase.table("logs_estoque").insert({
                            "usuario": username_atual, "substancia": f"(REMOVIDO) {item_del['nome']}",
                            "quantidade_antiga": float(item_del['quantidade']), "quantidade_nova": 0.0, "org_name": org_usuario
                        }).execute()
                        supabase.table("substancias").delete().eq("id", id_del).execute()
                        st.rerun()
    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
