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
key = st.secrets["SUPABASE_KEY"]import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Substâncias", layout="wide")

# Conexão com o Banco de Dados na Nuvem
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNÇÃO: REGISTRAR NA TABELA DA FOTO (historico_atividades) ---
def registrar_log_atividades(acao, substancia, quantidade, detalhes, user_data):
    log = {
        "usuario_email": user_data.get('email', 'usuario@lab.com'),
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia,
        "quantidade": str(quantidade),
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        supabase.table("historico_atividades").insert(log).execute()
    except:
        pass

# --- FUNÇÃO AUXILIAR: RENDERIZAR DIAMANTE DE HOMMEL (NFPA 704) ---
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
                    with st.spinner("Enviando..."):
                        data_insert = {
                            "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                            "quantidade": quantidade, "estoque_minimo": estoque_minimo,
                            "validade": validade, "org_name": org_usuario, "cas": cas,
                            "saude": s_saude, "fogo": s_fogo, "reatividade": s_reat,
                            "especial": s_esp, "instrucoes": instrucoes
                        }
                        supabase.table("substancias").insert(data_insert).execute()
                        registrar_log_atividades("Cadastro", nome, quantidade, "Inserção via sistema", user_data)
                        st.success(f"'{nome}' cadastrado!")
                        st.rerun()

    st.divider()

    # --- 2. EXIBIÇÃO DO INVENTÁRIO ---
    try:
        response = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.subheader(f"📋 Inventário: {org_usuario}")
            st.dataframe(df[['id', 'nome', 'cas', 'quantidade', 'validade']], use_container_width=True, hide_index=True)

            # --- ABA DE CONSULTA DE SEGURANÇA (MANTIDA ORIGINAL) ---
            st.subheader("🛡️ Consulta de Segurança (FISPQ Digital)")
            substancia_alvo = st.selectbox("Selecione um item para ver a ficha de segurança:", options=df['nome'].tolist())
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            
            col_visual, col_texto = st.columns([1, 3])
            with col_visual:
                render_hommel(detalhes.get('saude', 0), detalhes.get('fogo', 0), detalhes.get('reatividade', 0), detalhes.get('especial', ''))
            with col_texto:
                st.warning(f"**Instruções de Emergência:**\n\n{detalhes.get('instrucoes', 'Não informadas.')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')}")

            st.divider()

            # --- NOVA SEÇÃO: GERADOR DE QR CODES (CONECTADO AO NOVO SISTEMA) ---
            st.subheader("🏷️ Gerador de Etiquetas Inteligentes (QR Code)")
            with st.container(border=True):
                col_qr_sel, col_qr_img = st.columns([2, 1])
                
                with col_qr_sel:
                    st.write("Gere o QR Code para acesso rápido via mobile:")
                    item_qr = st.selectbox("Escolha o item para o QR Code", options=df['nome'].tolist(), key="qr_select")
                    id_selecionado = df[df['nome'] == item_qr]['id'].values[0]
                    
                    # Link para o novo sistema
                    url_final = f"https://sistemadeqrcodes.streamlit.app/?id={id_selecionado}"
                    
                    if st.button("📦 Gerar ZIP com Todos os QRs", use_container_width=True):
                        zip_buf = BytesIO()
                        with zipfile.ZipFile(zip_buf, "a") as z:
                            for _, r in df.iterrows():
                                link_zip = f"https://sistemadeqrcodes.streamlit.app/?id={r['id']}"
                                q_zip = qrcode.make(link_zip)
                                b_zip = BytesIO()
                                q_zip.save(b_zip, format="PNG")
                                z.writestr(f"qrcodes/qr_{r['nome']}.png", b_zip.getvalue())
                        
                        st.download_button("📥 Baixar ZIP Completo", zip_buf.getvalue(), "etiquetas_laboratorio.zip", use_container_width=True)
                        registrar_log_atividades("Exportação ZIP", "Todos", "0", "Download de todos os QRs", user_data)

                with col_qr_img:
                    img_qr = qrcode.make(url_final)
                    buf = BytesIO()
                    img_qr.save(buf, format="PNG")
                    st.image(buf.getvalue(), width=150, caption=f"QR Code: {item_qr}")
                    st.download_button("📥 Baixar Imagem QR", buf.getvalue(), f"qr_{item_qr}.png", use_container_width=True)

            # --- PAINEL ADM E REMOÇÃO (MANTIDOS) ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Remover Substância"):
                    id_del = st.selectbox("ID para remover", options=df['id'].tolist())
                    if st.button("Confirmar Exclusão", type="primary"):
                        supabase.table("substancias").delete().eq("id", id_del).execute()
                        registrar_log_atividades("Exclusão", "ID: "+str(id_del), "0", "Remoção permanente", user_data)
                        st.rerun()

    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()
supabase = create_client(url, key)

# --- AJUSTE: Conectando à tabela historico_atividades conforme a foto ---
def registrar_historico(acao, substancia_nome, quantidade, detalhes, user_data):
    log = {
        "usuario_email": user_data.get('email', 'sistema@lab.com'), # Ajustado para bater com a coluna da foto
        "org_name": user_data.get('org_name', 'Default'),
        "acao": acao,
        "substancia_nome": substancia_nome,
        "quantidade": str(quantidade), # A foto indica tipo 'text' para quantidade
        "detalhes": detalhes,
        "created_at": datetime.now().isoformat()
    }
    try:
        # Nome da tabela alterado para historico_atividades conforme imagem
        supabase.table("historico_atividades").insert(log).execute()
    except Exception as e:
        print(f"Erro ao logar: {e}")
        pass

def show_substances():
    st.header("🔬 Cadastro e Gerenciamento de Substâncias")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')
    username_atual = user_data.get('username', 'Usuário')

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
                    
                    # Chamada de log atualizada para a nova estrutura
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

            # --- MELHORIA TI: CONSULTA E QR CODE (Conectado ao novo domínio) ---
            st.subheader("🛡️ Consulta de Segurança e QR Code")
            substancia_alvo = st.selectbox("Selecione um item:", options=df['nome'].tolist())
            detalhes = df[df['nome'] == substancia_alvo].iloc[0]
            
            col_vis, col_txt, col_qr = st.columns([1.5, 2.5, 1.5])
            
            with col_vis:
                css_content = ""
                if os.path.exists("CSS/substancias.css"):
                    with open("CSS/substancias.css", "r") as f:
                        css_content = f.read()
                
                html_template = """
                <style>__CSS__</style>
                <div style="display: flex; justify-content: center; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;">
                    <div style="position: relative; width: 80px; height: 80px; transform: rotate(45deg); border: 1px solid #555;">
                        <div style="position: absolute; top: 0; left: 0; width: 40px; height: 40px; background: #ff4b4b; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">__FOGO__</div>
                        <div style="position: absolute; top: 0; left: 40px; width: 40px; height: 40px; background: #f1c40f; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold;">__REAT__</div>
                        <div style="position: absolute; top: 40px; left: 0; width: 40px; height: 40px; background: #3498db; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: white; font-weight: bold;">__SAUDE__</div>
                        <div style="position: absolute; top: 40px; left: 40px; width: 40px; height: 40px; background: #fff; display: flex; align-items: center; justify-content: center; transform: rotate(-45deg); color: black; font-weight: bold; font-size: 0.7em;">__ESP__</div>
                    </div>
                </div>
                """
                render = html_template.replace("__CSS__", css_content)
                render = render.replace("__FOGO__", str(detalhes.get('fogo', 0)))
                render = render.replace("__REAT__", str(detalhes.get('reatividade', 0)))
                render = render.replace("__SAUDE__", str(detalhes.get('saude', 0)))
                render = render.replace("__ESP__", str(detalhes.get('especial', '')))
                st.markdown(render, unsafe_allow_html=True)

            with col_txt:
                st.warning(f"**Emergência:**\n\n{detalhes.get('instrucoes', 'N/A')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')}")

            with col_qr:
                # Alterado para o novo domínio solicitado
                url_base = "https://sistemadeqrcodes.streamlit.app/"
                qr_link = f"{url_base}?id={detalhes['id']}" 
                
                img_qr = qrcode.make(qr_link)
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                st.image(buf.getvalue(), width=130, caption="QR Ficha Digital")
                
                if st.download_button("📥 Baixar QR", buf.getvalue(), f"qr_{substancia_alvo}.png", use_container_width=True):
                    registrar_historico("Gerar QR", substancia_alvo, detalhes['quantidade'], "Download de QR Code individual", user_data)

            # --- FERRAMENTAS DE ADM TI ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("⚙️ Ferramentas de Administrador (Massa)"):
                    if st.button("📦 Gerar Tudo (ZIP de HTML e QR Codes)"):
                        zip_buf = BytesIO()
                        with zipfile.ZipFile(zip_buf, "a") as z:
                            # Adicionando HTMLs (se o template existir)
                            if os.path.exists("HTML/substancias.html"):
                                with open("HTML/substancias.html", "r") as f:
                                    tmpl = f.read()
                                for _, r in df.iterrows():
                                    h = tmpl
                                    for col in r.index: h = h.replace(f"{{{{{col}}}}}", str(r[col]))
                                    z.writestr(f"fichas/{r['id']}.html", h)
                            
                            # Gerando QR Codes apontando para o novo sistema para cada item
                            for _, r in df.iterrows():
                                link_item = f"https://sistemadeqrcodes.streamlit.app/?id={r['id']}"
                                q = qrcode.make(link_item)
                                b = BytesIO()
                                q.save(b, format="PNG")
                                z.writestr(f"qrcodes/qr_{r['nome']}.png", b.getvalue())
                        
                        st.download_button("📥 Baixar Projeto Completo", zip_buf.getvalue(), "estoque_digital.zip")
                        registrar_historico("Gerar ZIP", "Múltiplos", "N/A", "Geração de pacote completo de QR Codes", user_data)

    except Exception as e:
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    show_substances()

