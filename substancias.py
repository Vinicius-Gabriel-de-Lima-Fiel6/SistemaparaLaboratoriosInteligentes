import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import os
import zipfile

# Conexão com o Banco de Dados
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def registrar_historico(acao, item, qtd, detalhes, user_data):
    """Grava na tabela historico_atividades com as colunas corretas"""
    log = {
        "usuario_email": user_data.get('email') or user_data.get('username') or "sistema@empresa.com",
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": item,
        "quantidade": str(qtd),
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log).execute()
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {e}")

def show_substances():
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

    # --- 1. SEU CADASTRO ORIGINAL (LINHA POR LINHA) ---
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

            with st.expander("🛡️ Informações de Segurança (FISPQ/MSDS)"):
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
                    
                    # REGISTRO NO HISTÓRICO CONFORME SOLICITADO
                    registrar_historico("CADASTRO", nome, quantidade, "Novo item cadastrado", user_data)
                    
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    # --- 2. SEU INVENTÁRIO ORIGINAL ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            # --- ACRESCIMO: SISTEMA DE QRCODE NO FINAL ---
            st.subheader("🛡️ Geração de Etiquetas QR (Portal Online)")
            
            # URL do SEGUNDO site que você vai criar para consulta
            url_portal = st.text_input("Link do Portal de Consulta:", "https://portal-consulta.streamlit.app")
            
            sel_item = st.selectbox("Selecione o item para o QR Code:", df['nome'].tolist())
            detalhes = df[df['nome'] == sel_item].iloc[0]
            
            col_diamante, col_qr = st.columns([2, 1])
            
            with col_diamante:
                # Diamante de Hommel em HTML Inline para visualização rápida
                html_h = f"""
                <div style="display: flex; background: #1e1e1e; padding: 10px; border-radius: 10px; border: 1px solid #333;">
                    <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #444; margin: auto;">
                        <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{detalhes.get('fogo', 0)}</div>
                        <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">{detalhes.get('reatividade', 0)}</div>
                        <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{detalhes.get('saude', 0)}</div>
                        <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold; font-size: 0.7em;">{detalhes.get('especial', '')}</div>
                    </div>
                </div>
                """
                st.markdown(html_h, unsafe_allow_html=True)
                st.info(f"**Instruções de Emergência:** {detalhes.get('instrucoes', 'Não cadastradas')}")

            with col_qr:
                # O Link Dinâmico para o Portal Online (com ID e Empresa)
                link_qrcode = f"{url_portal}?id={detalhes['id']}&org={org_usuario.replace(' ', '%20')}"
                img = qrcode.make(link_qrcode)
                buf = BytesIO()
                img.save(buf, format="PNG")
                
                st.image(buf.getvalue(), width=150)
                st.download_button("📥 Baixar QR", buf.getvalue(), f"QR_{sel_item}.png", use_container_width=True)
                
                if st.button("Registrar Consulta"):
                    registrar_historico("GERAR QR", sel_item, detalhes['quantidade'], f"Link: {link_qrcode}", user_data)
                    st.toast("Ação registrada no Supabase!")

            st.divider()
            
            # Geração em Massa
            if st.button("📦 Gerar ZIP de Todos os Itens da Empresa"):
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as z:
                    for _, row in df.iterrows():
                        link_lote = f"{url_portal}?id={row['id']}&org={org_usuario.replace(' ', '%20')}"
                        q = qrcode.make(link_lote)
                        img_buffer = BytesIO()
                        q.save(img_buffer, format="PNG")
                        z.writestr(f"qrcodes/qr_{row['nome']}.png", img_buffer.getvalue())
                
                st.download_button("📥 Baixar ZIP Completo", zip_buffer.getvalue(), "etiquetas_empresa.zip", use_container_width=True)
                registrar_historico("EXPORTAR LOTE", "Sistema", 0, "Gerou todos os QRs da empresa", user_data)

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

if __name__ == "__main__":
    show_substances()
