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
    """
    Alimenta a tabela 'historico_atividades' conforme a imagem.
    """
    # Garante que o email não seja nulo para não dar erro no banco
    email_usuario = user_data.get('email') or user_data.get('username') or "usuario@sistema.com"
    
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
        # Tenta inserir na tabela correta
        supabase.table("historico_atividades").insert(log).execute()
    except Exception as e:
        # Se der erro (ex: nome da tabela errado), avisa no console do Streamlit
        st.sidebar.error(f"Erro de Log: {e}")

def show_substances():
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. SEU CADASTRO ORIGINAL ---
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
                    # REGISTRO NO HISTÓRICO
                    registrar_historico("Cadastro", nome, quantidade, "Inserção via sistema", user_data)
                    st.success(f"'{nome}' cadastrado!")
                    st.rerun()

    st.divider()

    # --- 2. SEU INVENTÁRIO ORIGINAL ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            # --- MELHORIA: QR CODE INDIVIDUAL OU LOTE ---
            st.subheader("🛡️ Consulta e QR Codes Automáticos")
            
            # Escolha do modo
            modo = st.radio("Deseja gerar QR Code de:", ["Apenas este item", "Todos os itens (ZIP)"], horizontal=True)
            
            # Aqui você deve colocar o link real do seu Streamlit!
            url_atual = st.text_input("Link do seu sistema (URL):", "https://seu-app.streamlit.app")

            if modo == "Apenas este item":
                substancia_alvo = st.selectbox("Selecione o item:", options=df['nome'].tolist())
                detalhes = df[df['nome'] == substancia_alvo].iloc[0]
                
                col_vis, col_txt, col_qr = st.columns([1.5, 2.5, 1.5])
                with col_vis:
                    html_diamante = f"""
                    <div style="display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;">
                        <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555;">
                            <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{detalhes.get('fogo', 0)}</div>
                            <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">{detalhes.get('reatividade', 0)}</div>
                            <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">{detalhes.get('saude', 0)}</div>
                            <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold; font-size: 0.7em;">{detalhes.get('especial', '')}</div>
                        </div>
                    </div>
                    """
                    st.markdown(html_diamante, unsafe_allow_html=True)

                with col_txt:
                    st.warning(f"**Emergência:**\n\n{detalhes.get('instrucoes', 'N/A')}")

                with col_qr:
                    qr_link = f"{url_atual}?id={detalhes['id']}"
                    img_qr = qrcode.make(qr_link)
                    buf = BytesIO()
                    img_qr.save(buf, format="PNG")
                    st.image(buf.getvalue(), width=130)
                    st.download_button("📥 Baixar QR", buf.getvalue(), f"qr_{substancia_alvo}.png")
                    registrar_historico("QR Individual", substancia_alvo, detalhes['quantidade'], "Gerou QR Code", user_data)
            
            else:
                # GERAÇÃO EM LOTE
                if st.button("📦 Baixar Todos os QR Codes (ZIP)"):
                    zip_buf = BytesIO()
                    with zipfile.ZipFile(zip_buf, "w") as z:
                        for _, r in df.iterrows():
                            link = f"{url_atual}?id={r['id']}"
                            img = qrcode.make(link)
                            b = BytesIO()
                            img.save(b, format="PNG")
                            z.writestr(f"qr_{r['nome']}.png", b.getvalue())
                    
                    st.download_button("📥 Clique para Baixar ZIP", zip_buf.getvalue(), "etiquetas.zip")
                    registrar_historico("QR Lote", "Todos", 0, "Gerou todos os QRs da empresa", user_data)

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

if __name__ == "__main__":
    show_substances()
