import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile

# --- CONFIGURAÇÃO DA PÁGINA ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

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
            st.warning("Seu perfil é apenas para visualização. Contate o ADM para alterações.")
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
                instrucoes = st.text_area("Instruções de Emergência / Primeiros Socorros")
                
            if st.button("➕ Adicionar Substância", use_container_width=True):
                if nome and quantidade:
                    with st.spinner("Enviando para o banco de dados..."):
                        data_insert = {
                            "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                            "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                            "validade": validade, "org_name": org_usuario, "cas": cas,
                            "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat,
                            "especial": s_esp, "instrucoes": instrucoes
                        }
                        supabase.table("substancias").insert(data_insert).execute()
                        
                        # --- GRAVANDO LOG DE CADASTRO ---
                        supabase.table("logs_estoque").insert({
                            "usuario": username_atual, "substancia": nome,
                            "quantidade_antiga": 0.0, "quantidade_nova": float(quantidade), "org_name": org_usuario
                        }).execute()
                        
                        st.success(f"'{nome}' cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("Preencha ao menos Nome e Quantidade.")

    st.divider()

    # --- 2. EXIBIÇÃO DO INVENTÁRIO ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.subheader(f"📋 Inventário: {org_usuario}")
            cols_ordem = ['id', 'nome', 'cas', 'quantidade', 'estoque_minimo', 'validade']
            st.dataframe(df[cols_ordem], use_container_width=True, hide_index=True)

            # --- SEÇÃO DE EXPORTAÇÃO ---
            with st.container(border=True):
                st.markdown("### 📊 Exportação e Análise Externa")
                col_exp1, col_exp2, col_exp3, col_exp4 = st.columns([1, 1, 1, 1])
                csv = df.to_csv(index=False).encode('utf-8')
                col_exp1.download_button(label="📥 Baixar Dados (CSV)", data=csv, file_name=f"inventario_{org_usuario}.csv", mime='text/csv', use_container_width=True)
                col_exp2.link_button("🌐 Abrir Excel Online", "https://excel.new", use_container_width=True)
                
                buf_zip = BytesIO()
                with zipfile.ZipFile(buf_zip, 'w') as zf:
                    for _, row in df.iterrows():
                        qr_content = f"Item: {row['nome']}\nCAS: {row.get('cas', 'N/A')}\nEmergencia: {row.get('instrucoes', 'N/A')}"
                        img_qr = qrcode.make(qr_content)
                        img_buf = BytesIO(); img_qr.save(img_buf, format="PNG")
                        zf.writestr(f"qr_{row['nome'].replace(' ', '_')}.png", img_buf.getvalue())
                
                col_exp3.download_button(label="🖼️ Gerar Todos QR Codes", data=buf_zip.getvalue(), file_name=f"qrcodes_{org_usuario}.zip", mime="application/zip", use_container_width=True)
                with col_exp4:
                    with st.popover("💡 Como analisar no Excel?", use_container_width=True):
                        st.write("1. Clique em Baixar. 2. Abra o Excel Online. 3. Vá em Arquivo > Abrir e envie o CSV.")

            # --- ATUALIZAÇÃO RÁPIDA ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🔄 Atualizar Quantidade em Estoque"):
                    col_sel, col_val, col_btn = st.columns([2, 1, 1])
                    sub_para_editar = col_sel.selectbox("Escolha a substância", options=df['nome'].tolist(), key="edit_qty")
                    nova_qtd = col_val.number_input("Nova Quantidade", min_value=0.0)
                    if col_btn.button("Atualizar Estoque", use_container_width=True):
                        qtd_antiga = df[df['nome'] == sub_para_editar]['quantidade'].values[0]
                        supabase.table("substancias").update({"quantidade": nova_qtd}).eq("nome", sub_para_editar).execute()
                        # LOG DE ALTERAÇÃO
                        supabase.table("logs_estoque").insert({
                            "usuario": username_atual, "substancia": sub_para_editar, 
                            "quantidade_antiga": float(qtd_antiga), "quantidade_nova": float(nova_qtd), "org_name": org_usuario
                        }).execute()
                        st.rerun()

            # --- CONSULTA DE SEGURANÇA ---
            st.subheader("🛡️ Consulta de Segurança (FISPQ Digital)")
            substancia_alvo = st.selectbox("Selecione um item:", options=df['nome'].tolist())
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            col_visual, col_texto, col_qr = st.columns([1, 2, 1])
            with col_visual: render_hommel(detalhes['saude'], detalhes['fogo'], detalhes['reatividade'], detalhes['especial'])
            with col_texto:
                st.warning(f"**Instruções de Emergência:**\n\n{detalhes.get('instrucoes', 'Não informadas.')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')}")
            with col_qr:
                qr_content = f"Substancia: {detalhes['nome']}\nCAS: {detalhes.get('cas', 'N/A')}\nEmergencia: {detalhes.get('instrucoes', 'N/A')}"
                qr = qrcode.make(qr_content)
                buf = BytesIO(); qr.save(buf, format="PNG")
                st.image(buf.getvalue(), caption="QR Code", width=120)
                st.download_button("📥 Baixar QR", buf.getvalue(), f"qr_{detalhes['nome']}.png", "image/png")
            
            # --- HISTÓRICO DE MOVIMENTAÇÕES ---
            with st.expander("📜 Histórico Recente de Alterações"):
                logs_res = supabase.table("logs_estoque").select("*").eq("org_name", org_usuario).order("created_at", desc=True).limit(5).execute()
                if logs_res.data:
                    log_df = pd.DataFrame(logs_res.data)
                    log_df['created_at'] = pd.to_datetime(log_df['created_at']).dt.strftime('%d/%m %H:%M')
                    st.table(log_df[['created_at', 'usuario', 'substancia', 'quantidade_antiga', 'quantidade_nova']])

            # --- EXCLUSÃO ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover Substância"):
                    id_del = st.selectbox("ID para remover", options=df['id'].tolist())
                    item_del = df[df['id'] == id_del].iloc[0]
                    if st.button("Confirmar Exclusão", type="primary"):
                        # --- GRAVANDO LOG DE EXCLUSÃO ---
                        supabase.table("logs_estoque").insert({
                            "usuario": username_atual, "substancia": f"(REMOVIDO) {item_del['nome']}",
                            "quantidade_antiga": float(item_del['quantidade']), "quantidade_nova": 0.0, "org_name": org_usuario
                        }).execute()
                        supabase.table("substancias").delete().eq("id", id_del).execute()
                        st.warning(f"Item removido.")
                        st.rerun()
        else:
            st.info(f"Nenhuma substância cadastrada para {org_usuario}.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

if __name__ == "__main__":
    show_substances()
