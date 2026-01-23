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
    """Alimenta a tabela 'historico_atividades' conforme solicitado"""
    email_usuario = user_data.get('email') or user_data.get('username') or "sistema@empresa.com"
    log = {
        "usuario_email": email_usuario,
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
        st.error(f"Erro no Log Supabase: {e}")

def show_substances():
    st.header("🔬 Gestão de Substâncias da Empresa")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- LÓGICA DE DETECÇÃO DO QR CODE ---
    # Se alguém escanear o QR Code, o sistema detecta o ID na URL e mostra a ficha
    query_params = st.query_params
    if "id" in query_params:
        item_id = query_params["id"]
        res_qr = supabase.table("substancias").select("*").eq("id", item_id).execute()
        if res_qr.data:
            item = res_qr.data[0]
            st.success(f"📌 Ficha Digital: {item['nome']}")
            st.info(f"**Instruções de Emergência:** {item.get('instrucoes', 'Não cadastradas')}")
            # Botão para voltar ao sistema normal
            if st.button("Voltar ao Inventário Completo"):
                st.query_params.clear()
                st.rerun()
            return # Para a execução aqui para mostrar só a ficha

    # --- 1. CADASTRO ORIGINAL ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        if role_usuario != "Visualizador":
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substância")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentração")
                quantidade = st.number_input("Quantidade Atual", min_value=0.0)
            with col3:
                estoque_minimo = st.number_input("Estoque Mínimo", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Número CAS")

            with st.expander("🛡️ Segurança (NFPA 704)"):
                c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                s_saude = c_s1.slider("Saúde", 0, 4, 0)
                s_fogo = c_s2.slider("Fogo", 0, 4, 0)
                s_reat = c_s3.slider("Reatividade", 0, 4, 0)
                s_esp = c_s4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Instruções de Emergência")
                
            if st.button("➕ Adicionar Substância", use_container_width=True):
                if nome:
                    data_insert = {
                        "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                        "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                        "validade": validade, "org_name": org_usuario, "cas": cas,
                        "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat,
                        "especial": s_esp, "instrucoes": instrucoes
                    }
                    supabase.table("substancias").insert(data_insert).execute()
                    registrar_historico("CADASTRO", nome, quantidade, "Novo item na pasta da empresa", user_data)
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    # --- 2. INVENTÁRIO E SISTEMA AUTOMÁTICO DE QR CODE ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df[['id', 'nome', 'quantidade', 'validade']], use_container_width=True)

            st.subheader("🖼️ Gerador de Etiquetas QR (Pasta Empresa)")
            
            # Pega a URL do seu app automaticamente ou pede para inserir
            url_app = st.text_input("URL do Sistema (para o QR Code funcionar):", "https://seu-app.streamlit.app")
            
            aba_qr1, aba_qr2 = st.tabs(["Individual", "Lote (Download ZIP)"])

            with aba_qr1:
                item_sel = st.selectbox("Escolha o produto para gerar QR:", df['nome'].tolist())
                dados_item = df[df['nome'] == item_sel].iloc[0]
                
                # O LINK AGORA LEVA DIRETO PARA O ID DO PRODUTO
                link_final = f"{url_app}?id={dados_item['id']}"
                
                img_qr = qrcode.make(link_final)
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                
                st.image(buf.getvalue(), width=200, caption=f"QR Code: {item_sel}")
                st.download_button(f"📥 Baixar QR {item_sel}", buf.getvalue(), f"QR_{item_sel}.png")
                
            with aba_qr2:
                st.write(f"Gerar etiquetas para os {len(df)} itens da empresa.")
                if st.button("🚀 Gerar Todos em ZIP"):
                    zip_buf = BytesIO()
                    with zipfile.ZipFile(zip_buf, "w") as z:
                        for _, r in df.iterrows():
                            link_lote = f"{url_app}?id={r['id']}"
                            img_l = qrcode.make(link_lote)
                            b_l = BytesIO()
                            img_l.save(b_l, format="PNG")
                            z.writestr(f"etiquetas/QR_{r['nome']}.png", b_l.getvalue())
                    
                    st.download_button("📥 Baixar Arquivo ZIP", zip_buf.getvalue(), "etiquetas_empresa.zip")
                    registrar_historico("EXPORTACAO", "Vários", 0, "Gerou lote de QR Codes", user_data)

    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
