import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(page_title="Sistema de Substâncias", layout="wide") # Comentei caso já esteja no app.py

# Conexão
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNÇÃO HISTÓRICO (Baseada na sua foto) ---
def salvar_no_historico(acao, substancia, quantidade, detalhes, user_data):
    log_geral = {
        "usuario_email": user_data.get('email', 'usuario@lab.com'),
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia,
        "quantidade": str(quantidade), 
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log_geral).execute()
    except:
        pass

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
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Nome da Substância")
            finalidade = c1.text_input("Finalidade")
            concentracao = c2.text_input("Concentração")
            quantidade = c2.number_input("Quantidade Atual", min_value=0.0)
            estoque_minimo = c3.number_input("Estoque Mínimo", min_value=0.0)
            validade = c3.text_input("Validade (MM/AAAA)")
            cas = c3.text_input("Número CAS")

            with st.expander("🛡️ Segurança"):
                cs = st.columns(4)
                s_s = cs[0].slider("Saúde", 0, 4, 0)
                s_f = cs[1].slider("Fogo", 0, 4, 0)
                s_r = cs[2].slider("Reatividade", 0, 4, 0)
                s_e = cs[3].selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                inst = st.text_area("Instruções")
                
            if st.button("➕ Adicionar Substância", use_container_width=True):
                if nome:
                    data_insert = {
                        "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                        "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                        "validade": validade, "org_name": org_usuario, "cas": cas,
                        "saude": s_s, "fogo": s_f, "reatividade": s_r, # Verifique se no banco está 'reatividade' ou 'reat'
                        "especial": s_e, "instrucoes": inst
                    }
                    try:
                        # TENTA INSERIR
                        supabase.table("substancias").insert(data_insert).execute()
                        salvar_no_historico("CADASTRO", nome, quantidade, "Via sistema", user_data)
                        st.success("Cadastrado!")
                        st.rerun()
                    except Exception as e:
                        # SE DER ERRO, ELE VAI MOSTRAR QUAL COLUNA O BANCO NÃO GOSTOU
                        st.error("🚨 ERRO DE COLUNA NO BANCO DE DADOS:")
                        st.write(str(e))
                        st.info("Verifique se os nomes das colunas na tabela 'substancias' no Supabase são EXATAMENTE iguais aos nomes no código acima.")

    st.divider()

    # --- 2. LISTAGEM ---
    try:
        res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.dataframe(df[['nome', 'quantidade', 'validade']], use_container_width=True)
            
            st.subheader("🛡️ Consulta de Segurança")
            sub_alvo = st.selectbox("Selecione:", df['nome'].tolist())
            det = df[df['nome'] == sub_alvo].iloc[0]
            
            c_v, c_t = st.columns([1, 3])
            with c_v:
                render_hommel(det.get('saude', 0), det.get('fogo', 0), det.get('reatividade', 0), det.get('especial', ''))
            with c_t:
                st.warning(f"**Emergência:** {det.get('instrucoes', 'N/A')}")
        else:
            st.info("Vazio.")
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")

if __name__ == "__main__":
    show_substances()
