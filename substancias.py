import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import qrcode
from io import BytesIO
import zipfile

# --- CONEXÃO COM O BANCO DE DADOS ---
# Certifique-se que estas chaves estão no seu secrets.toml
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"Erro de conexão com Supabase: {e}")

# --- FUNÇÃO: REGISTRAR NA TABELA HISTORICO_ATIVIDADES ---
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
        # O .execute() retorna os dados ou levanta uma exceção
        res = supabase.table("historico_atividades").insert(log).execute()
        st.toast("✅ Histórico alimentado!") 
    except Exception as e:
        # ISSO VAI MOSTRAR O MOTIVO REAL (Ex: Coluna inexistente ou RLS)
        st.error(f"🚨 ERRO CRÍTICO NO SUPABASE: {e}")
        st.write("Dados que tentei enviar:", log)

# --- FUNÇÃO AUXILIAR: RENDERIZAR DIAMANTE DE HOMMEL ---
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
    st.header("🔬 Gestão de Inventário e Segurança")
    
    user_data = st.session_state.get('user_data', {})
    org_usuario = user_data.get('org_name', 'Default')
    role_usuario = user_data.get('role', 'Visualizador')

    # --- 1. CADASTRO DE SUBSTÂNCIAS ---
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        
        if role_usuario == "Visualizador":
            st.warning("Seu perfil permite apenas visualização.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome da Substância")
                finalidade = st.text_input("Finalidade")
            with col2:
                concentracao = st.text_input("Concentração")
                quantidade = st.number_input("Quantidade Atual", min_value=0.0, step=0.1)
            with col3:
                estoque_minimo = st.number_input("Estoque Mínimo", min_value=0.0)
                validade = st.text_input("Validade (MM/AAAA)")
                cas = st.text_input("Número CAS")

            with st.expander("🛡️ Informações de Segurança"):
                c1, c2, c3, c4 = st.columns(4)
                s_saude = c1.slider("Saúde", 0, 4, 0)
                s_fogo = c2.slider("Fogo", 0, 4, 0)
                s_reat = c3.slider("Reatividade", 0, 4, 0)
                s_esp = c4.selectbox("Especial", ["", "W", "OX", "SA", "BIO"])
                instrucoes = st.text_area("Instruções de Emergência")
                
            if st.button("➕ Adicionar ao Inventário", use_container_width=True):
                if nome and quantidade:
                    with st.spinner("Sincronizando com Supabase..."):
                        # 1. Alimenta tabela 'substancias'
                        dados_sub = {
                            "nome": nome, "finalidade": finalidade, "concentracao": concentracao,
                            "quantidade": float(quantidade), "estoque_minimo": float(estoque_minimo),
                            "validade": validade, "org_name": org_usuario, "cas": cas,
                            "saude": int(s_saude), "fogo": int(s_fogo), "reatividade": int(s_reat),
                            "especial": s_esp, "instrucoes": instrucoes
                        }
                        supabase.table("substancias").insert(dados_sub).execute()
                        
                        # 2. Alimenta tabela 'historico_atividades' conforme sua imagem
                        registrar_log_atividades(
                            acao="CADASTRO",
                            substancia=nome,
                            quantidade=quantidade,
                            detalhes=f"Novo item cadastrado por {user_data.get('username', 'usuário')}",
                            user_data=user_data
                        )
                        
                        st.success(f"'{nome}' registrado e histórico atualizado!")
                        st.rerun()

    st.divider()

    # --- 2. EXIBIÇÃO E CONSULTA ---
    try:
        res = supabase.table("substancias").select("*").eq("org_name", org_usuario).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.subheader("📋 Itens em Estoque")
            st.dataframe(df[['id', 'nome', 'quantidade', 'validade', 'cas']], use_container_width=True, hide_index=True)

            # --- SEÇÃO DE CONSULTA (MANTIDA ORIGINAL) ---
            st.subheader("🛡️ Consulta de Segurança (FISPQ)")
            selecionado = st.selectbox("Selecione para ver detalhes:", options=df['nome'].tolist())
            detalhes = df[df['nome'] == selecionado].iloc[0]
            
            c_vis, c_txt = st.columns([1, 3])
            with c_vis:
                render_hommel(detalhes['saude'], detalhes['fogo'], detalhes['reatividade'], detalhes.get('especial', ''))
            with c_txt:
                st.warning(f"**Emergência:** {detalhes.get('instrucoes', 'Não informada.')}")
                st.caption(f"CAS: {detalhes.get('cas', 'N/A')}")

            st.divider()

            # --- ABA DE QR CODES (Abaixo da consulta, como solicitado) ---
            st.subheader("🏷️ Gerador de Etiquetas (QR Code)")
            with st.container(border=True):
                col_sel, col_qr = st.columns([2, 1])
                with col_sel:
                    st.write("Link mobile para o novo sistema:")
                    item_qr = st.selectbox("Gerar QR para:", options=df['nome'].tolist(), key="qr_item")
                    id_selecionado = df[df['nome'] == item_qr]['id'].values[0]
                    url_dest = f"https://sistemadeqrcodes.streamlit.app/?id={id_selecionado}"
                    
                    if st.button("📦 Gerar ZIP de Etiquetas", use_container_width=True):
                        zip_io = BytesIO()
                        with zipfile.ZipFile(zip_io, "a") as z:
                            for _, r in df.iterrows():
                                link_z = f"https://sistemadeqrcodes.streamlit.app/?id={r['id']}"
                                img_z = qrcode.make(link_z)
                                b_z = BytesIO()
                                img_z.save(b_z, format="PNG")
                                z.writestr(f"qr_{r['nome']}.png", b_z.getvalue())
                        
                        st.download_button("📥 Baixar ZIP", zip_io.getvalue(), "etiquetas_laboratorio.zip")
                        registrar_log_atividades("EXPORTAÇÃO", "Múltiplos", "0", "Gerado ZIP de etiquetas", user_data)

                with col_qr:
                    img = qrcode.make(url_dest)
                    b_io = BytesIO()
                    img.save(b_io, format="PNG")
                    st.image(b_io.getvalue(), width=130)
                    st.download_button("📥 Baixar Imagem", b_io.getvalue(), f"qr_{item_qr}.png")

            # --- OPÇÕES ADM ---
            if role_usuario in ["ADM", "Tecnico"]:
                with st.expander("🗑️ Excluir Item"):
                    if st.button(f"Confirmar Exclusão de {selecionado}", type="primary"):
                        supabase.table("substancias").delete().eq("id", detalhes['id']).execute()
                        registrar_log_atividades("EXCLUSÃO", selecionado, "0", "Item removido do estoque", user_data)
                        st.rerun()

    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")

if __name__ == "__main__":
    show_substances()

