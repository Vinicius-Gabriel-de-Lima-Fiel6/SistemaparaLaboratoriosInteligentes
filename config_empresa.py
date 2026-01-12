import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    # 1. Recuperação Segura de Dados
    user_data = st.session_state.get('user_data', {})
    email_logado = user_data.get('email')
    
    # Se o org_id estiver vazio, tentamos buscar direto da tabela users
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')

    if not org_id and email_logado:
        try:
            check_user = supabase.table("users").select("org_id, org_name").eq("email", email_logado).single().execute()
            if check_user.data:
                org_id = check_user.data['org_id']
                org_name = check_user.data['org_name']
        except:
            pass

    st.title("⚙️ Painel Administrativo")
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    with aba_equipe:
        st.subheader(f"Membros da Organização: {org_name}")
        
        # Dashboard de Métricas (MANTIDO)
        try:
            # Buscamos por org_id que é mais seguro que nome
            res = supabase.table("users").select("*").eq("org_id", org_id).execute()
            df = pd.DataFrame(res.data)

            if not df.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("Total", len(df))
                c2.metric("Técnicos", len(df[df['role'] == 'Tecnico']))
                c3.metric("ADMs", len(df[df['role'] == 'ADM']))
                
                st.write("### 📋 Lista de Membros")
                for _, func in df.iterrows():
                    with st.container(border=True):
                        col_info, col_del = st.columns([4, 1])
                        col_info.write(f"**{func['username']}** ({func['role']})")
                        col_info.caption(f"Email: {func['email']}")
                        
                        if func['email'] != email_logado:
                            if col_del.button("Remover", key=f"del_{func['id']}", type="secondary"):
                                if db.excluir_usuario_por_id(func['id'])[0]:
                                    st.rerun()
                        else:
                            col_del.write("✨ Você")
            else:
                st.info("Nenhum membro encontrado para esta organização.")
        except Exception as e:
            st.error(f"Erro ao carregar equipe: {e}")

    with aba_laboratorio:
        st.subheader("🏢 Configurações da Empresa")
        
        # Busca dados da empresa no banco
        dados_org = {}
        if org_id:
            try:
                res_org = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
                dados_org = res_org.data if res_org.data else {}
            except:
                pass

        with st.form("form_empresa"):
            st.write(f"ID: `{org_id}`")
            novo_plano = st.selectbox("Plano", ["Trial", "Mensal", "Anual"], 
                                     index=0 if dados_org.get('plano_ativo') != "Mensal" else 1)
            novo_metodo = st.text_input("Método de Pagamento", value=dados_org.get('metodo_pagto', ''))
            
            if st.form_submit_button("Salvar Alterações"):
                if org_id:
                    try:
                        supabase.table("organizations").update({
                            "plano_ativo": novo_plano,
                            "metodo_pagto": novo_metodo
                        }).eq("id", org_id).execute()
                        st.success("Dados salvos!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
                else:
                    st.error("Erro: O sistema não identificou o ID da sua empresa. Faça logout e login novamente.")
