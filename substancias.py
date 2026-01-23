import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import zipfile
from io import BytesIO
import os

st.set_page_config(page_title="Sistema de Substâncias", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_historico(acao, item, detalhes, user_data):
    log_entry = {
        "usuario_nome": user_data.get('username', 'Sistema'),
        "usuario_email": user_data.get('email', 'N/A'),
        "cargo": user_data.get('role', 'N/A'),
        "acao": acao,
        "item_afetado": item,
        "detalhes": detalhes,
        "org_name": user_data.get('org_name', 'Default'),
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico").insert(log_entry).execute()
    except:
        pass

def render_hommel(saude, fogo, reat, esp):
    with open("CSS/substancias.css", "r") as f:
        estilo = f"<style>{f.read()}</style>"
    
    st.markdown(estilo + f"""
    <div class="hommel-container">
        <div class="hommel-box">
            <div class="fogo">{fogo}</div>
            <div class="reat">{reat}</div>
            <div class="saude">{saude}</div>
            <div class="esp">{esp if esp else ''}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_substances():
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

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

            with st.expander("🛡️ Informações de Segurança"):
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
                    registrar_historico("Cadastro", nome, f"Cadastrado com {quantidade} unidades.", user_data)
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🔄 Atualizar Quantidade"):
                    col_sel, col_val, col_btn = st.columns([2, 1, 1])
                    sub_para_editar = col_sel.selectbox("Substância", options=df['nome'].tolist())
                    nova_qtd = col_val.number_input("Nova Qtd", min_value=0.0)
                    
                    if col_btn.button("Atualizar"):
                        qtd_antiga = df[df['nome'] == sub_para_editar]['quantidade'].values[0]
                        supabase.table("substancias").update({"quantidade": nova_qtd}).eq("nome", sub_para_editar).execute()
                        registrar_historico("Movimentação", sub_para_editar, f"De {qtd_antiga} para {nova_qtd}", user_data)
                        st.success("Atualizado!")
                        st.rerun()

            st.subheader("🛡️ Consulta de Segurança")
            sub_fispq = st.selectbox("Selecione para ver ficha:", options=df['nome'].tolist())
            det = df[df['nome'] == sub_fispq].iloc[0]
            c_vis, c_txt = st.columns([1, 3])
            with c_vis:
                render_hommel(det['saude'], det['fogo'], det['reatividade'], det['especial'])
            with c_txt:
                st.warning(f"**Instruções:** {det['instrucoes']}")

            st.divider()
            with st.expander("📦 Exportação para TI"):
                if st.button("Gerar Pacote ZIP"):
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_f:
                        with open("CSS/substancias.css", "r") as f:
                            zip_f.writestr("substancias.css", f.read())
                        with open("HTML/substancias.html", "r") as f:
                            tmpl = f.read()
                        for _, r in df.iterrows():
                            html_i = tmpl
                            for k in r.index:
                                html_i = html_i.replace(f"{{{{{k}}}}}", str(r[k]))
                            zip_f.writestr(f"{r['id']}.html", html_i)
                    st.download_button("📥 Baixar ZIP", zip_buffer.getvalue(), "fichas.zip", "application/zip")

    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
