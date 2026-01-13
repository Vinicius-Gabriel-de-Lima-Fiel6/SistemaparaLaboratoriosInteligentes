import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db
import datetime

# Importação segura do bot
try:
    from bot_automat import disparar_email_manual
except ImportError:
    pass

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    # Estilo CSS (Mantido Original)
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
        .st-emotion-cache-1cvow48 { border-radius: 12px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("⚙️ Painel de Controle")
    
    user_data = st.session_state.user_data
    org_id = user_data.get('org_id')
    org_name = user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    # --- ABA 1: GESTÃO DE EQUIPE ---
    with aba_equipe:
        try:
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)
            lista_emails = df['email'].tolist() if not df.empty else []

            if not df.empty:
                # Dashboard de Métricas (RESTAURADO)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Membros", len(df))
                c2.metric("Técnicos", len(df[df['role'] == 'Tecnico']))
                c3.metric("ADMs", len(df[df['role'] == 'ADM']))
                c4.metric("Visualizadores", len(df[df['role'] == 'Visualizador']))
                
                st.write("📊 **Distribuição de Cargos**")
                st.bar_chart(df['role'].value_counts(), height=180)

            st.divider()

            with st.expander("➕ **Adicionar Novo Membro**"):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    nome_func = c1.text_input("Nome Completo")
                    email_func = c2.text_input("E-mail")
                    senha_func = c1.text_input("Senha Provisória", type="password")
                    cargo_func = c2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                    
                    if st.form_submit_button("🚀 Liberar Acesso", use_container_width=True):
                        if nome_func and email_func and senha_func:
                            sucesso, msg = db.cadastrar_usuario(nome_func, email_func, senha_func, org_name, cargo_func)
                            if sucesso:
                                st.success("Acesso liberado!")
                                st.rerun()
                            else:
                                st.error(msg)

            st.write("### 📋 Equipe Atual")
            if not df.empty:
                for _, func in df.iterrows():
                    with st.container(border=True):
                        col_txt, col_btn = st.columns([4, 1])
                        with col_txt:
                            role_color = "blue" if func['role'] == "Tecnico" else "red" if func['role'] == "ADM" else "gray"
                            st.markdown(f"**{func['username']}** :{role_color}[({func['role']})]")
                            st.caption(f"📧 {func['email']}")
                        
                        if func['email'] != user_data['email']:
                            if col_btn.button("Remover", key=f"del_{func['id']}", use_container_width=True):
                                if db.excluir_usuario_por_id(func['id'])[0]:
                                    st.rerun()
                        else:
                            col_btn.write("✨ (Você)")
            
            # --- SEÇÃO DO BOT ---
            st.divider()
            st.write("### 🤖 Automação de Dados")
            res_bot = supabase.table("config_automacao").select("*").eq("org_name", org_name).execute()
            config_bot = res_bot.data[0] if res_bot.data else {}

            with st.container(border=True):
                with st.expander("⚙️ Configurar Destinatários e SMTP"):
                    # Carregamento dos e-mails salvos
                    e_salvos = [x.strip() for x in config_bot.get('email_destino', '').split(',')] if config_bot.get('email_destino') else []
                    e_validos = [x for x in e_salvos if x in lista_emails]

                    # TUDO DENTRO DO FORM PARA CORRIGIR O ERRO DA FOTO
                    with st.form("form_automacao_v3"):
                        receptores = st.multiselect("Quem receberá o relatório?", options=lista_emails, default=e_validos)
                        
                        col1, col2 = st.columns(2)
                        dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                        dia_bot = col1.selectbox("Dia", dias, index=dias.index(config_bot.get('dia_semana', 'Segunda')) if config_bot.get('dia_semana') in dias else 0)
                        hora_bot = col2.time_input("Horário", value=datetime.time(8, 0))
                        
                        st.caption("Credenciais SMTP")
                        s_user = st.text_input("Seu E-mail (Gmail)", value=config_bot.get('smtp_user', ''))
                        s_pass = st.text_input("Senha de App", type="password", placeholder="Deixe vazio para manter a atual")

                        if st.form_submit_button("💾 Salvar Tudo", use_container_width=True):
                            bot_data = {
                                "org_name": org_name, "email_destino": ", ".join(receptores),
                                "dia_semana": dia_bot, "horario": str(hora_bot),
                                "smtp_user": s_user, "smtp_pass": s_pass if s_pass else config_bot.get('smtp_pass')
                            }
                            supabase.table("config_automacao").upsert(bot_data).execute()
                            st.success("Configurações salvas!")
                            st.rerun()

                    # Botão de ajuda fora do form
                    with st.popover("❓ Ajuda: Senha de App"):
                        st.write("Gere a senha de 16 dígitos na sua Conta Google > Segurança > Senhas de App.")

                if config_bot:
                    if st.button("🚀 Disparar Agora", use_container_width=True, type="primary"):
                        if disparar_email_manual(config_bot, st):
                            st.toast("Relatório enviado!", icon="✅")

        except Exception as e:
            st.error(f"Erro: {e}")

    # --- ABA 2: DADOS DA EMPRESA (CORREÇÃO DA FOTO 4) ---
    with aba_laboratorio:
        st.subheader("🏢 Perfil da Organização")
        try:
            # Busca os dados da empresa
            org_res = supabase.table("organizations").select("*").eq("id", org_id).execute()
            
            # SE NÃO EXISTIR DADOS (Caso da foto 4), MOSTRA FORMULÁRIO DE CADASTRO
            if not org_res.data:
                st.warning("📊 Dados da empresa ainda não configurados no banco.")
                with st.form("completar_cadastro_empresa"):
                    st.write("### 📝 Finalizar Cadastro da Empresa")
                    plano = st.selectbox("Plano Ativo", ["Trial / Beta", "Essencial", "Premium"])
                    metodo = st.selectbox("Pagamento", ["PIX", "Cartão", "Boleto"])
                    
                    if st.form_submit_button("Salvar Perfil da Empresa"):
                        supabase.table("organizations").insert({
                            "id": org_id, "name": org_name, 
                            "plano_ativo": plano, "metodo_pagto": metodo,
                            "status_assinatura": "Ativo"
                        }).execute()
                        st.rerun()
            else:
                # Se os dados existirem, mostra o layout original (Foto 3 corrigida)
                dados = org_res.data[0]
                col_info, col_status = st.columns(2)
                
                with col_info:
                    with st.container(border=True):
                        st.markdown("### 🆔 Identidade")
                        st.write(f"**Laboratório:** {org_name}")
                        st.write("**ID Único:**")
                        st.code(org_id, language="text")

                with col_status:
                    with st.container(border=True):
                        st.markdown("### 💳 Assinatura")
                        status = dados.get('status_assinatura', 'ATIVO').upper()
                        st.markdown(f"**Status:** :green[{status} ✅]")
                        st.write(f"**Plano:** `{dados.get('plano_ativo')}`")
                        if st.button("Gerenciar Assinatura", use_container_width=True):
                            st.info("Acessando financeiro...")
                
                st.divider()
                with st.container(border=True):
                    st.markdown("### 🔒 Segurança")
                    st.write("Seus dados estão protegidos sob as normas da LGPD.")
                    st.button("Editar Perfil Público", use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao carregar laboratório: {e}")
