import streamlit as st
import pandas as pd
from supabase import create_client

# Configuração Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def render_vidrarias():
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    st.title("⚗️ Gestão de Vidrarias")
    st.markdown("---")

    # --- 1. CADASTRO ---
    with st.container(border=True):
        st.subheader("Cadastrar Nova Vidraria")
        if role_usuario == "Visualizador":
            st.warning("Apenas usuários Administradores ou Técnicos podem cadastrar itens.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                tipo = st.selectbox("Tipo de Vidraria", ["Béquer", "Erlenmeyer", "Balão Volumétrico", "Pipeta", "Proveta", "Bureta", "Tubo de Ensaio", "Outros"])
            with c2:
                capacidade = st.text_input("Capacidade (ex: 250ml)", placeholder="250ml")
            with c3:
                numeracao = st.text_input("Numeração / Patrimônio", placeholder="Ex: VID-001")
            
            if st.button("➕ Adicionar ao Inventário", use_container_width=True):
                if tipo and numeracao:
                    try:
                        # Verificação básica de duplicidade de numeração
                        check = supabase.table("vidrarias").select("vid").eq("numeracao", numeracao).eq("org_name", org_usuario).execute()
                        if check.data:
                            st.error(f"A numeração '{numeracao}' já existe nesta organização.")
                        else:
                            supabase.table("vidrarias").insert({
                                "tipo": tipo, 
                                "capacidade": capacidade, 
                                "numeracao": numeracao, 
                                "org_name": org_usuario
                            }).execute()
                            st.success(f"{tipo} ({numeracao}) cadastrado com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    st.error("Por favor, preencha o Tipo e a Numeração.")

    st.write("")

    # --- 2. LISTAGEM E GESTÃO ---
    try:
        res = supabase.table("vidrarias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.subheader("📋 Inventário Atual")
            
            # UX: Reorganizando as colunas para a Numeração vir primeiro
            st.dataframe(
                df[['numeracao', 'tipo', 'capacidade']], 
                use_container_width=True, 
                hide_index=True
            )

            if role_usuario in ["ADM", "Tecnico"]:
                st.write("")
                col_edit, col_del = st.columns(2)

                with col_edit:
                    with st.expander("🔄 Alterar Dados"):
                        # UX: Seleciona pela Numeração em vez do ID oculto
                        num_edit = st.selectbox("Selecione a Numeração para editar", options=df['numeracao'].tolist(), key="sel_edit")
                        
                        # Localiza os dados atuais no DF
                        dados_atuais = df[df['numeracao'] == num_edit].iloc[0]
                        
                        novo_tipo = st.selectbox("Novo Tipo", ["Béquer", "Erlenmeyer", "Balão Volumétrico", "Pipeta", "Proveta", "Bureta", "Outros"], index=0)
                        nova_cap = st.text_input("Nova Capacidade", value=dados_atuais['capacidade'])
                        
                        if st.button("Salvar Alterações", use_container_width=True):
                            supabase.table("vidrarias").update({
                                "tipo": novo_tipo, 
                                "capacidade": nova_cap
                            }).eq("numeracao", num_edit).eq("org_name", org_usuario).execute()
                            st.success("Item atualizado!")
                            st.rerun()

                with col_del:
                    with st.expander("🗑️ Excluir Item"):
                        # UX: Seleciona pela Numeração para remover
                        num_del = st.selectbox("Selecione a Numeração para remover", options=df['numeracao'].tolist(), key="sel_del")
                        st.warning(f"Tem certeza que deseja remover o item '{num_del}'?")
                        if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                            supabase.table("vidrarias").delete().eq("numeracao", num_del).eq("org_name", org_usuario).execute()
                            st.rerun()
        else:
            st.info("Nenhuma vidraria encontrada para esta organização.")
            
    except Exception as e:
        st.error(f"Erro ao carregar o inventário: {e}")

if __name__ == "__main__":
    render_vidrarias()
