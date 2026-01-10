import streamlit as st
import pandas as pd
from supabase import create_client

# Conexão com o Banco de Dados na Nuvem
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNÇÃO AUXILIAR PARA O DIAMANTE (ACRÉSCIMO) ---
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
    
    # Recupera os dados da empresa logada
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. CADASTRO DE SUBSTÂNCIAS ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        
        # Bloqueia cadastro para quem é apenas Visualizador
        if role_usuario == "Visualizador":
            st.warning("Seu perfil é apenas para visualização. Contate o ADM para alterações.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substância")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentração")
                quantidade = st.number_input("Quantidade", min_value=0.0)
            with col3:
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Número CAS (Opcional)") # ACRESCENTADO

            # --- SEÇÃO FISPQ (ACRESCENTADO) ---
            with st.expander("🛡️ Informações de Segurança (FISPQ/MSDS)"):
                c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                s_saude = c_s1.slider("Saúde", 0, 4, 0)
                s_fogo = c_s2.slider("Fogo", 0, 4, 0)
                s_reat = c_s3.slider("Reatividade", 0, 4, 0)
                s_esp = c_s4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Instruções de Emergência / Primeiros Socorros")
                
            if st.button("➕ Adicionar Substância", use_container_width=True):
                if nome and quantidade:
                    with st.spinner("Enviando para o banco de dados..."):
                        data_insert = {
                            "nome": nome,
                            "finalidade": finalidade,
                            "concentracao": concentracao,
                            "quantidade": quantidade,
                            "validade": validade,
                            "org_name": org_usuario,
                            "cas": cas,              # ACRESCENTADO
                            "saude": s_saude,        # ACRESCENTADO
                            "fogo": s_fogo,          # ACRESCENTADO
                            "reatividade": s_reat,   # ACRESCENTADO
                            "especial": s_esp,       # ACRESCENTADO
                            "instrucoes": instrucoes # ACRESCENTADO
                        }
                        supabase.table("substancias").insert(data_insert).execute()
                        st.success(f"'{nome}' cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("Preencha ao menos Nome e Quantidade.")

    st.divider()

    # --- 2. EXIBIÇÃO DO INVENTÁRIO (Sincronizado com o Estoque) ---
    st.subheader(f"📋 Inventário: {org_usuario}")
    
    try:
        # Busca apenas as substâncias da empresa logada
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            # Reorganizando as colunas (ACRESCENTADO 'cas' na visualização)
            cols_ordem = ['id', 'nome', 'cas', 'quantidade', 'concentracao', 'validade', 'finalidade']
            df_display = df[cols_ordem]
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # --- NOVO: CONSULTA DE SEGURANÇA RÁPIDA (ACRESCENTADO) ---
            st.subheader("🛡️ Consulta de Segurança (FISPQ Digital)")
            substancia_alvo = st.selectbox("Selecione um item para ver a ficha de segurança:", options=df['nome'].tolist())
            
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            
            col_visual, col_texto = st.columns([1, 3])
            with col_visual:
                render_hommel(detalhes.get('saude', 0), detalhes.get('fogo', 0), detalhes.get('reatividade', 0), detalhes.get('especial', ''))
            with col_texto:
                st.warning(f"**Instruções de Emergência:**\n\n{detalhes.get('instrucoes', 'Não informadas.')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')}")
            
            # --- 3. EXCLUSÃO DE ITENS ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover Substância"):
                    st.write("Selecione o item para exclusão permanente:")
                    id_del = st.selectbox("ID para remover", options=df['id'].tolist())
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        supabase.table("substancias").delete().eq("id", id_del).execute()
                        st.warning(f"Item ID {id_del} foi removido do banco de dados.")
                        st.rerun()
        else:
            st.info(f"Nenhuma substância cadastrada para a empresa {org_usuario}.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
