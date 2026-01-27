import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from supabase import create_client


url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def show_equipamentos():
   
    
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

  
    with st.expander("➕ Adicionar Novo Equipamento", expanded=False):
        if role_usuario == "Visualizador":
            st.warning("Apenas administradores e técnicos podem cadastrar.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome do Equipamento")
                tipo = st.text_input("Tipo")
            with col2:
                status = st.selectbox("Status", ["Operacional", "Manutenção", "Fora de Uso", "Calibração"])
                u_manut = st.date_input("Última Manutenção").strftime("%d/%m/%Y")
            with col3:
                local = st.text_input("Localização")
                resp = st.text_input("Responsável")
            cat = st.text_input("Categoria")

            if st.button("Salvar Equipamento"):
                if nome:
                    data_insert = {
                        "nome": nome, "tipo": tipo, "status": status,
                        "ultima_manutencao": u_manut, "localizacao": local,
                        "responsavel": resp, "categoria": cat, "org_name": org_usuario
                    }
                    supabase.table("equipamentos").insert(data_insert).execute()
                    
                  
                    supabase.table("logs_estoque").insert({
                        "usuario": username_atual,
                        "substancia": f"CADASTRO EQUIP.: {nome}",
                        "quantidade_antiga": 0.0,
                        "quantidade_nova": 1.0,
                        "org_name": org_usuario
                    }).execute()
                    
                    st.success(f"Equipamento {nome} cadastrado!")
                    st.rerun()


    st.divider()
    with st.expander("🛠️ Registrar Nova Manutenção"):
        resp_eq = supabase.table("equipamentos").select("id, nome").eq("org_name", org_usuario).execute()
        df_eq = pd.DataFrame(resp_eq.data)

        if not df_eq.empty:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                eq_escolhido = st.selectbox("Selecione o Equipamento", df_eq['nome'].tolist())
                eq_id = df_eq[df_eq['nome'] == eq_escolhido]['id'].values[0]
            with col_m2:
                data_m = st.date_input("Data da Manutenção", key="data_m").strftime("%d/%m/%Y")
            
            desc_m = st.text_area("Descrição do Serviço")

            if st.button("Confirmar Manutenção"):
                if role_usuario != "Visualizador":
                    manut_data = {
                        "equipamento_id": int(eq_id),
                        "data_manutencao": data_m,
                        "descricao": desc_m,
                        "org_name": org_usuario
                    }
                    supabase.table("manutencao").insert(manut_data).execute()
                    supabase.table("equipamentos").update({"ultima_manutencao": data_m}).eq("id", int(eq_id)).execute()
                    
                    # --- NOVO: LOG DE MANUTENÇÃO ---
                    supabase.table("logs_estoque").insert({
                        "usuario": username_atual,
                        "substancia": f"MANUTENÇÃO: {eq_escolhido}",
                        "quantidade_antiga": 1.0,
                        "quantidade_nova": 1.0,
                        "org_name": org_usuario
                    }).execute()
                    
                    st.success("Manutenção registrada!")
                    st.rerun()
                else:
                    st.error("Permissão negada.")
        else:
            st.info("Cadastre um equipamento primeiro.")

    # --- 3. VISUALIZAÇÃO DE DADOS E GRÁFICOS ---
    st.divider()
    tab1, tab2, tab3 = st.tabs(["📋 Inventário", "📜 Histórico", "📊 Gráficos"])

    resp_full = supabase.table("equipamentos").select("*").eq("org_name", org_usuario).execute()
    df_view = pd.DataFrame(resp_full.data)
    
    with tab1:
        if not df_view.empty:
            busca = st.text_input("🔍 Pesquisar por nome ou responsável:")
            if busca:
                df_view = df_view[df_view['nome'].str.contains(busca, case=False) | df_view['responsavel'].str.contains(busca, case=False)]
            
            is_disabled = (role_usuario == "Visualizador")
            edited_df = st.data_editor(df_view, use_container_width=True, hide_index=True, disabled=is_disabled)
            
            if not is_disabled and st.button("💾 Salvar Alterações na Tabela"):
                for _, row in edited_df.iterrows():
                    supabase.table("equipamentos").update({
                        "nome": row['nome'], "tipo": row['tipo'], "status": row['status'],
                        "localizacao": row['localizacao'], "responsavel": row['responsavel'],
                        "categoria": row['categoria']
                    }).eq("id", row['id']).execute()
                    
              
                    supabase.table("logs_estoque").insert({
                        "usuario": username_atual,
                        "substancia": f"EDITOU EQUIP.: {row['nome']}",
                        "quantidade_antiga": 1.0,
                        "quantidade_nova": 1.0,
                        "org_name": org_usuario
                    }).execute()
                    
                st.success("Dados atualizados e log registrado!")
                st.rerun()
        else:
            st.write("Nenhum equipamento cadastrado.")

    with tab2:
        resp_hist = supabase.table("manutencao").select("id, data_manutencao, descricao, equipamentos(nome)").eq("org_name", org_usuario).execute()
        if resp_hist.data:
            hist_data = []
            for m in resp_hist.data:
                hist_data.append({
                    "Equipamento": m['equipamentos']['nome'] if m['equipamentos'] else "N/A",
                    "Data": m['data_manutencao'],
                    "Descrição": m['descricao']
                })
            st.dataframe(pd.DataFrame(hist_data), use_container_width=True, hide_index=True)

    with tab3:
        if not df_view.empty:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write("**Equipamentos por Status**")
                status_count = df_view['status'].value_counts()
                fig1, ax1 = plt.subplots(figsize=(4,4))
                ax1.pie(status_count, labels=status_count.index, autopct='%1.1f%%', startangle=90)
                st.pyplot(fig1)
            with col_g2:
                st.write("**Equipamentos por Tipo**")
                tipo_count = df_view['tipo'].value_counts()
                st.bar_chart(tipo_count)


    st.sidebar.divider()
    if st.sidebar.button("📄 Gerar Relatório CSV"):
        if not df_view.empty:
            csv = df_view.to_csv(index=False).encode('utf-8-sig')
            st.sidebar.download_button("Clique para Baixar CSV", csv, "equipamentos.csv", "text/csv")

if __name__ == "__main__":
    show_equipamentos()

