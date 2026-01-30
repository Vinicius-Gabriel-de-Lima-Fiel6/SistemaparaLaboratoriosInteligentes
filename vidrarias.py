import streamlit as st
import pandas as pd
from supabase import create_client

def render_vidrarias():
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    org_usuario = st.session_state.get('user_data', {}).get('org_name', 'Default')

    st.header("🧪 Inventário de Vidrarias")
    
    with st.expander("➕ Cadastrar Nova Vidraria"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Béquer", "Erlenmeyer", "Proveta", "Balão Volumétrico", "Outro"])
        num = c2.text_input("Numeração/Patrimônio")
        cap = c1.text_input("Capacidade (ex: 500ml)")
        est = c2.selectbox("Estado", ["Novo", "Bom", "Desgastado"])
        
        if st.button("Salvar Vidraria"):
            supabase.table("vidrarias").insert({
                "tipo": tipo, "numeracao": num, "capacidade": cap, 
                "estado": est, "org_name": org_usuario
            }).execute()
            st.success("Vidraria registrada!")
            st.rerun()

    res = supabase.table("vidrarias").select("*").eq("org_name", org_usuario).execute()
    if res.data:
        st.dataframe(pd.DataFrame(res.data)[['numeracao', 'tipo', 'capacidade', 'estado', 'status']], use_container_width=True)
