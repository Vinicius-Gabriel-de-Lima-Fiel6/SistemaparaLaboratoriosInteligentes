import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    user_data = st.session_state.get('user_data', {})
    # Tenta buscar o org_id de várias formas para não aparecer "None"
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name', 'Laboratório')

    st.title("⚙️ Painel de Controle")
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    with aba_equipe:
        # Mantém sua lógica de equipe...
        st.subheader(f"Equipe: {org_name}")
        # (Código de métricas e lista de membros aqui)

    with aba_laboratorio:
        st.subheader("🏢 Perfil da Organização")
        
        # Busca dados da empresa no banco
        dados_org = {}
        if org_id:
            try:
                res = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
                dados_org = res.data if res.data else {}
            except:
                pass

        # INTERFACE: Clicar e Digitar
        with st.form("att_empresa"):
            st.info("Preencha os campos abaixo e clique em Salvar para atualizar seu perfil.")
            
            col1, col2 = st.columns(2)
            # O usuário clica e digita nestes campos:
            novo_plano = col1.selectbox("Plano Atual", ["Trial", "Mensal", "Anual"], 
                                       index=0 if dados_org.get('plano_ativo') == "Trial" else 1)
            
            # Aqui ele digita o método de pagamento
            novo_metodo = col2.text_input("Método de Pagamento", 
                                         value=dados_org.get('metodo_pagto', ''), 
                                         placeholder="Ex: Cartão, Pix...")
            
            # Novo campo para WhatsApp da Empresa (Exemplo de evolução)
            novo_zap = col1.text_input("WhatsApp de Contato", 
                                      value=dados_org.get('whatsapp_org', ''),
                                      placeholder="(00) 00000-0000")

            if st.form_submit_button("💾 Salvar Alterações"):
                if org_id:
                    supabase.table("organizations").update({
                        "plano_ativo": novo_plano,
                        "metodo_pagto": novo_metodo,
                        "whatsapp_org": novo_zap # Certifique-se de ter essa coluna
                    }).eq("id", org_id).execute()
                    st.success("Dados salvos! Os avisos sumirão.")
                    st.rerun()
                else:
                    st.error("Erro: ID da empresa não encontrado na sessão.")

        st.divider()
        st.caption(f"ID do Laboratório: {org_id}")
