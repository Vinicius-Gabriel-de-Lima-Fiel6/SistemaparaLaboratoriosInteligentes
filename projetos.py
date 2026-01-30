import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

def render_projetos():
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    org_usuario = st.session_state.get('user_data', {}).get('org_name', 'Default')

    st.header("📂 Gerenciamento de Projetos")
    
    with st.form("novo_projeto"):
        nome = st.text_input("Nome do Projeto")
        resp = st.text_input("Responsável Técnico")
        obj = st.text_area("Objetivo da Análise")
        if st.form_submit_button("Criar Projeto"):
            supabase.table("projetos").insert({
                "nome": nome, "responsavel": resp, "objetivo": obj,
                "data_inicio": str(datetime.now().date()), "org_name": org_usuario
            }).execute()
            st.success("Projeto Ativado!")
            st.rerun()

    res = supabase.table("projetos").select("*").eq("org_name", org_usuario).execute()
    if res.data:
        for p in res.data:
            st.info(f"**Projeto:** {p['nome']} | **Resp:** {p['responsavel']}")
