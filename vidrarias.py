import streamlit as st
import pandas as pd
from supabase import create_client
import qrcode
from io import BytesIO

# Configuração Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)
URL_SISTEMA = "https://sistemadeqrcodes.streamlit.app/"

def render_vidrarias():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    st.title("⚗️ Gestão de Vidrarias")

    # --- 1. CADASTRO ---
    with st.container(border=True):
        st.subheader("Cadastrar Nova Vidraria")
        if role_usuario == "Visualizador":
            st.warning("Apenas visualização permitida.")
        else:
            c1, c2, c3 = st.columns(3)
            tipo = c1.selectbox("Tipo de Vidraria", ["Béquer", "Erlenmeyer", "Balão Volumétrico", "Pipeta", "Proveta", "Bureta", "Outros"])
            capacidade = c2.text_input("Capacidade (ex: 250ml)")
            numeracao = c3.text_input("Numeração/Patrimônio")
            
            if st.button("➕ Adicionar Vidraria", use_container_width=True):
                if tipo and numeracao:
                    supabase.table("vidrarias").insert({
                        "tipo": tipo, "capacidade": capacidade, 
                        "numeracao": numeracao, "org_name": org_usuario
                    }).execute()
                    st.success(f"{tipo} cadastrado com sucesso!")
                    st.rerun()

    st.divider()

    # --- 2. LISTAGEM E AÇÕES ---
    try:
        res = supabase.table("vidrarias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.subheader("📋 Inventário de Vidrarias")
            # AJUSTE: Mudamos 'vid' para 'id'
            st.dataframe(df[['id', 'tipo', 'capacidade', 'numeracao']], use_container_width=True, hide_index=True)

            if role_usuario in ["ADM", "Tecnico"]:
                col_edit, col_del = st.columns(2)

                with col_edit:
                    with st.expander("🔄 Alterar Vidraria"):
                        # AJUSTE: Mudamos 'vid' para 'id'
                        id_edit = st.selectbox("Selecione o ID para editar", options=df['id'].tolist(), key="edit_vid")
                        novo_tipo = st.selectbox("Novo Tipo", ["Béquer", "Erlenmeyer", "Balão Volumétrico", "Pipeta", "Proveta", "Bureta", "Outros"], key="n_tipo")
                        nova_cap = st.text_input("Nova Capacidade", key="n_cap")
                        if st.button("Confirmar Alteração", use_container_width=True):
                            # AJUSTE: eq("id", id_edit)
                            supabase.table("vidrarias").update({"tipo": novo_tipo, "capacidade": nova_cap}).eq("id", id_edit).execute()
                            st.success("Alterado!")
                            st.rerun()

                with col_del:
                    with st.expander("🗑️ Excluir Vidraria"):
                        # AJUSTE: Mudamos 'vid' para 'id'
                        id_del = st.selectbox("Selecione o ID para remover", options=df['id'].tolist(), key="del_vid")
                        if st.button("Remover Permanentemente", type="primary", use_container_width=True):
                            supabase.table("vidrarias").delete().eq("id", id_del).execute()
                            st.rerun()
            
            # --- QR CODE INDIVIDUAL ---
            st.subheader("🖼️ Gerar QR Code")
            vid_sel = st.selectbox("Escolha a vidraria para o QR:", options=df['numeracao'].tolist())
            det = df[df['numeracao'] == vid_sel].iloc[0]
            # AJUSTE: O link do QR Code continua mandando 'vid' para o portal saber que é vidraria
            qr = qrcode.make(f"{URL_SISTEMA}?vid={det['id']}") 
            buf = BytesIO(); qr.save(buf, format="PNG")
            st.image(buf.getvalue(), width=150)
            st.download_button("Baixar QR Code", buf.getvalue(), f"qr_vidraria_{det['numeracao']}.png")
