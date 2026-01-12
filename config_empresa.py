import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db

# Inicializa conexão original (MANTIDA)
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    # Estilo CSS (MANTIDO)
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
        .st-emotion-cache-1cvow48 { border-radius: 12px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("⚙️ Painel de Controle")
    
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')

    # --- NOVO: LÓGICA DE DETECÇÃO DE DADOS FALTANTES (MELHORIA) ---
    campos_vulneraveis = {
        "plano_ativo": "Plano Contratado",
        "metodo_pagto": "Método de Pagamento",
        "status_assinatura": "Status da Conta"
    }
    
    faltando = []
    dados_org = {}
    
    try:
        org_res = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
        if org_res.data:
            dados_org = org_res.data
            for campo, label in campos_vulneraveis.items():
                if not dados_org.get(campo) or dados_org.get(campo) == "Não informado":
                    faltando.append(label)
    except:
        pass

    # Exibe Alerta Amigável se houver pendências
    if faltando:
        st.warning(f"### 📢 Olá, {user_data['username']}! Identificamos dados pendentes.")
        st.write(f"Para garantir a evolução do seu sistema Beta, preencha os seguintes campos da **{org_name}** na aba de 'Dados da Empresa':")
        st.markdown(f"**Pendente:** {', '.join(faltando)}")

    st.divider()

    # --- ABAS ORIGINAIS (MANTIDAS) ---
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    # --- ABA: GESTÃO DE EQUIPE (MANTIDA 100% FUNCIONAL) ---
    with aba_equipe:
        try:
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)

            if not df.empty:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Membros", len(df))
                c2.metric("Técnicos", len(df[df['role'] == 'Tecnico']))
                c3.metric("ADMs", len(df[df['role'] == 'ADM']))
                c4.metric("Visualizadores", len(df[df['role'] == 'Visualizador']))
                
                st.write("📊 **Distribuição de Cargos**")
                st.bar_chart(df['role'].value_counts(), height=180)

            st.divider()

            with st.expander("➕ **Adicionar Novo Membro à Equipe**"):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    nome_func = c1.text_input("Nome Completo")
                    email_func = c2.text_input("E-mail de Login")
                    senha_func = c1.text_input("Senha Provisória", type="password")
                    cargo_func = c2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                    
                    if st.form_submit_button("🚀 Liberar Acesso", use_container_width=True):
                        if nome_func and email_func and senha_func:
                            sucesso, msg = db.cadastrar_usuario(nome_func, email_func, senha_func, org_name, cargo_func)
                            if sucesso:
                                st.success(f"Acesso liberado!")
                                st.rerun()
                            else:
                                st.error(msg)

            st.write("### 📋 Equipe Atual")
            if not df.empty:
                for _, func in df.iterrows():
                    with st.container(border=True):
                        col_txt, col_btn = st.columns([4, 1])
                        with col_txt:
                            role_color = "blue" if func['role'] == "Tecnico" else "red" if func['role'] == "ADM" else "gray"
                            st.markdown(f"**{func['username']}** :{role_color}[({func['role']})]")
                            st.caption(f"📧 {func['email']}")
                        
                        if func['email'] != user_data['email']:
                            if col_btn.button("Remover", key=f"del_{func['id']}", type="secondary", use_container_width=True):
                                if db.excluir_usuario_por_id(func['id'])[0]:
                                    st.rerun()
                        else:
                            col_btn.write("✨ (Você)")
        except Exception as e:
            st.error(f"Erro ao carregar equipe: {e}")

    # --- ABA: DADOS DA EMPRESA (MELHORADA PARA ATUALIZAÇÃO) ---
    with aba_laboratorio:
        st.subheader("🏢 Perfil da Organização")
        
        # FORMULÁRIO DE ATUALIZAÇÃO (Para o ADM completar os dados)
        with st.form("form_update_empresa"):
            col_id, col_edit = st.columns(2)
            
            with col_id:
                st.write(f"**Laboratório:** {org_name}")
                st.write("**ID Único:**")
                st.code(org_id, language="text")
                st.caption("Dados fixos de registro.")

            with col_edit:
                # Carrega o que já existe ou sugere preenchimento
                val_plano = dados_org.get('plano_ativo', 'Trial')
                novo_plano = st.selectbox("Plano Atual", ["Trial", "Mensal", "Anual", "Enterprise"], 
                                         index=["Trial", "Mensal", "Anual", "Enterprise"].index(val_plano) if val_plano in ["Trial", "Mensal", "Anual", "Enterprise"] else 0)
                
                novo_metodo = st.text_input("Método de Pagto", value=dados_org.get('metodo_pagto', ''))
                
            if st.form_submit_button("💾 Salvar Alterações e Validar Conta", use_container_width=True):
                try:
                    supabase.table("organizations").update({
                        "plano_ativo": novo_plano,
                        "metodo_pagto": novo_metodo,
                        "status_assinatura": "ativo"
                    }).eq("id", org_id).execute()
                    st.success("Dados atualizados com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        st.divider()
        st.info("💡 **Dica Beta:** Sempre que o sistema ganhar novas funções, campos extras aparecerão aqui para preenchimento.")
