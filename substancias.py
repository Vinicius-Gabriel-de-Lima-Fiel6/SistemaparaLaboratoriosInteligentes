import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Substâncias", layout="wide")

# Conexão com o Banco de Dados na Nuvem
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNÇÃO: ALIMENTAR A TABELA DE HISTÓRICO (DA FOTO) ---
def salvar_no_historico(acao, substancia, quantidade, detalhes, user_data):
    """
    Garante que toda ação seja registrada na tabela 'historico_atividades'
    conforme as colunas da sua imagem.
    """
    log_geral = {
        "usuario_email": user_data.get('email', 'usuario@lab.com'),
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia,
        "quantidade": str(quantidade), # Salva como texto conforme sua foto
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log_geral).execute()
    except Exception as e:
        st.error(f"Erro ao salvar histórico central: {e}")

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
    username_atual = user_data.get('username', 'Usuário')

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
                if nome and quantidade:
                    with st.spinner("Salvando..."):
                        data_insert = {
                            "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                            "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                            "validade": validade, "org_name": org_usuario, "cas": cas,
                            "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat,
                            "especial": s_esp, "instrucoes": instrucoes
                        }
                        supabase.table("substancias").insert(data_insert).execute()
                        
                        # ALIMENTA O HISTÓRICO DA FOTO
                        salvar_no_historico("CADASTRO", nome, quantidade, f"Cadastrado por {username_atual}", user_data)
                        
                        st.success(f"'{nome}' cadastrado!")
                        st.rerun()

    st.divider()

    # --- 2. EXIBIÇÃO E HISTÓRICO ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.subheader(f"📋 Inventário: {org_usuario}")
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'estoque_minimo', 'validade']], use_container_width=True, hide_index=True)

            # --- ATUALIZAÇÃO COM LOG DUPLO ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🔄 Atualizar Quantidade em Estoque"):
                    col_sel, col_val, col_btn = st.columns([2, 1, 1])
                    sub_para_editar = col_sel.selectbox("Escolha a substância", options=df['nome'].tolist(), key="edit_qty")
                    nova_qtd = col_val.number_input("Nova Quantidade", min_value=0.0)
                    
                    if col_btn.button("Atualizar Estoque", use_container_width=True):
                        qtd_antiga = df[df['nome'] == sub_para_editar]['quantidade'].values[0]
                        supabase.table("substancias").update({"quantidade": nova_qtd}).eq("nome", sub_para_editar).execute()
                        
                        # Log na sua tabela de historico_atividades
                        salvar_no_historico("ATUALIZAÇÃO", sub_para_editar, nova_qtd, f"Alterado de {qtd_antiga} para {nova_qtd}", user_data)
                        
                        st.success(f"Estoque de {sub_para_editar} atualizado!")
                        st.rerun()

            # --- CONSULTA DE SEGURANÇA ---
            st.subheader("🛡️ Consulta de Segurança (FISPQ Digital)")
            substancia_alvo = st.selectbox("Selecione um item:", options=df['nome'].tolist())
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            
            col_visual, col_texto = st.columns([1, 3])
            with col_visual:
                render_hommel(detalhes.get('saude', 0), detalhes.get('fogo', 0), detalhes.get('reatividade', 0), detalhes.get('especial', ''))
            with col_texto:
                st.warning(f"**Instruções:** {detalhes.get('instrucoes', 'Não informadas.')}")

            # --- EXCLUSÃO COM LOG ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover Substância"):
                    id_del = st.selectbox("ID para remover", options=df['id'].tolist())
                    nome_del = df[df['id'] == id_del]['nome'].values[0]
                    if st.button("Confirmar Exclusão", type="primary"):
                        supabase.table("substancias").delete().eq("id", id_del).execute()
                        salvar_no_historico("EXCLUSÃO", nome_del, 0, "Item removido do sistema", user_data)
                        st.rerun()
        else:
            st.info("Nenhuma substância cadastrada.")
            
    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
