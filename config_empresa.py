import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db
import datetime

try:
    from bot_automat import disparar_email_manual
except ImportError:
    pass

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    # Estilo CSS personalizado (Mantido Original)
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

    # --- ABA: GESTÃO DE EQUIPE ---
    with aba_equipe:
        try:
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)
            lista_emails = df['email'].tolist() if not df.empty else []

            if not df.empty:
                # Dashboard de Métricas Moderno (Original)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Membros", len(df))
                c2.metric("Técnicos", len(df[df['role'] == 'Tecnico']))
                c3.metric("ADMs", len(df[df['role'] == 'ADM']))
                c4.metric("Visualizadores", len(df[df['role'] == 'Visualizador']))
                
                st.write("📊 **Distribuição de Cargos**")
                st.bar_chart(df['role'].value_counts(), height=180)

            st.divider()

            with st.expander("➕ **Adicionar Novo Membro à Equipe**"):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    nome_func = c1.text_input("Nome Completo")
                    email_func = c2.text_input("E-mail de Login")
                    senha_func = c1.text_input("Senha Provisória", type="password")
                    cargo_func = c2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                    
                    if st.form_submit_button("🚀 Liberar Acesso", use_container_width=True):
                        if nome_func and email_func and senha_func:
                            sucesso, msg = db.cadastrar_usuario(nome_func, email_func, senha_func, org_name, cargo_func)
                            if sucesso:
                                st.success(f"Acesso liberado para {nome_func}!")
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
                            if col_btn.button("Remover", key=f"del_{func['id']}", type="secondary", use_container_width=True):
                                if db.excluir_usuario_por_id(func['id'])[0]:
                                    st.rerun()
                        else:
                            col_btn.write("✨ (Você)")
            
            st.divider()
            st.write("### 🤖 Automação de Dados")
            
            res_bot = supabase.table("config_automacao").select("*").eq("org_name", org_name).execute()
            config_bot = res_bot.data[0] if res_bot.data else {}

            with st.container(border=True):
                st.markdown("**Relatórios Automáticos por E-mail**")
                st.caption("O bot analisa tráfego, estoque e equipamentos desta unidade.")
                
                with st.expander("⚙️ Configurar Agendamento"):
                    # Processamento para o multiselect
                    email_salvo_raw = config_bot.get('email_destino', '')
                    emails_ja_selecionados = [e.strip() for e in email_salvo_raw.split(",")] if email_salvo_raw else []
                    emails_validos = [e for e in emails_ja_selecionados if e in lista_emails]

                    # TUDO DENTRO DO FORM PARA NÃO DAR O ERRO DA IMAGEM
                    with st.form("form_bot_config_v2"):
                        receptores = st.multiselect("Receptores do Relatório", options=lista_emails, default=emails_validos)
                        
                        col_b1, col_b2 = st.columns(2)
                        dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                        dia_bot = col_b1.selectbox("Dia do envio", dias, index=dias.index(config_bot.get('dia_semana', 'Segunda')) if config_bot.get('dia_semana') in dias else 0)
                        
                        hora_atual = datetime.time(8, 0)
                        if config_bot.get('horario'):
                            try:
                                h, m, s = map(int, config_bot.get('horario').split(':'))
                                hora_atual = datetime.time(h, m)
                            except: pass
                        hora_bot = col_b2.time_input("Horário", value=hora_atual)
                        
                        st.write("---")
                        st.caption("Credenciais de Envio (SMTP)")
                        s_user = st.text_input("E-mail Remetente", value=config_bot.get('smtp_user', ''))
                        s_pass = st.text_input("Senha de App", type="password", placeholder="Deixe vazio para manter a atual")

                        if st.form_submit_button("Salvar Configuração", use_container_width=True):
                            bot_data = {
                                "org_name": org_name, "email_destino": ", ".join(receptores),
                                "dia_semana": dia_bot, "horario": str(hora_bot),
                                "smtp_user": s_user, "smtp_pass": s_pass if s_pass else config_bot.get('smtp_pass')
                            }
                            supabase.table("config_automacao").upsert(bot_data).execute()
                            st.success("Configuração salva!")
                            st.rerun()
                    
                    # Popover de Ajuda fora do Form
                    with st.popover("❓ Como conseguir a Senha de App?"):
                        st.markdown("1. Conta Google > Segurança\n2. Ative Verificação em 2 Etapas\n3. Selecione 'Senhas de App'\n4. Gere e cole os 16 dígitos.")

                if config_bot:
                    if st.button("🚀 Disparar Relatório Agora", use_container_width=True, type="primary"):
                        with st.spinner("Bot processando dados..."):
                            if disparar_email_manual(config_bot, st):
                                st.toast("Relatório enviado!", icon="✅")
                            else:
                                st.error("Erro no envio.")

        except Exception as e:
            st.error(f"Erro ao carregar equipe: {e}")

    with aba_laboratorio:
        st.subheader("🏢 Perfil da Organização")
        try:
            org_res = supabase.table("organizations").select("*").eq("id", org_id).execute()
            
            if not org_res.data:
                st.warning("📊 Dados da organização não encontrados. Vamos preenchê-los?")
                with st.form("completar_cadastro_org"):
                    novo_plano = st.selectbox("Escolha seu Plano", ["Trial / Beta", "Essencial", "Premium"])
                    metodo = st.selectbox("Método de Pagamento Preferencial", ["PIX", "Cartão", "Boleto"])
                    if st.form_submit_button("Finalizar Cadastro da Empresa"):
                        supabase.table("organizations").insert({
                            "id": org_id, "name": org_name, 
                            "plano_ativo": novo_plano, "metodo_pagto": metodo,
                            "status_assinatura": "Ativo"
                        }).execute()
                        st.rerun()
            else:
                dados = org_res.data[0]
                col_id, col_plano = st.columns(2)
                with col_id:
                    with st.container(border=True):
                        st.markdown("### 🆔 Identidade")
                        st.write(f"**Nome:** {org_name}")
                        st.write("**ID Único:**")
                        st.code(org_id, language="text")

                with col_plano:
                    with st.container(border=True):
                        st.markdown("### 💳 Assinatura")
                        status = dados.get('status_assinatura', 'Ativo').upper()
                        st.markdown(f"**Status:** :green[{status} ✅]")
                        st.markdown(f"**Plano:** `{dados.get('plano_ativo', 'Trial')}`")
                        st.write(f"**Pagamento via:** {dados.get('metodo_pagto', 'N/A')}")
                
                st.divider()
                with st.container(border=True):
                    st.markdown("### 🔒 Segurança e Dados")
                    st.write("Dados criptografados conforme a LGPD.")
                    st.button("Editar Informações Públicas", use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao carregar dados da empresa: {e}")
