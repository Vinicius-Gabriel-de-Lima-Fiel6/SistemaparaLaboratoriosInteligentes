import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db
import datetime

# Importação do bot (certifique-se que o arquivo bot_automat.py existe na mesma pasta)
try:
    from bot_automat import disparar_email_manual
except ImportError:
    pass

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def show_config_empresa():
    # 1. Estilo CSS Original
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


    with aba_equipe:
        try:
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)
            lista_emails = df['email'].tolist() if not df.empty else []

            if not df.empty:
                # Dashboard de Métricas (Igual ao seu original)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Membros", len(df))
                c2.metric("Técnicos", len(df[df['role'] == 'Tecnico']))
                c3.metric("ADMs", len(df[df['role'] == 'ADM']))
                c4.metric("Visualizadores", len(df[df['role'] == 'Visualizador']))
                
                st.write("📊 **Distribuição de Cargos**")
                st.bar_chart(df['role'].value_counts(), height=180)

            st.divider()

            # Formulário de Adição (Igual ao seu original)
            with st.expander("➕ **Adicionar Novo Membro à Equipe**"):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    nome_f = c1.text_input("Nome Completo")
                    email_f = c2.text_input("E-mail de Login")
                    senha_f = c1.text_input("Senha Provisória", type="password")
                    cargo_f = c2.selectbox("Nível de Acesso", ["Visualizador", "Tecnico", "ADM"])
                    
                    if st.form_submit_button("🚀 Liberar Acesso", use_container_width=True):
                        if nome_f and email_f and senha_f:
                            sucesso, msg = db.cadastrar_usuario(nome_f, email_f, senha_f, org_name, cargo_f)
                            if sucesso:
                                st.success("Acesso liberado!")
                                st.rerun()
                            else: st.error(msg)

            st.write("### 📋 Equipe Atual")
            if not df.empty:
                for _, func in df.iterrows():
                    with st.container(border=True):
                        col_t, col_b = st.columns([4, 1])
                        with col_t:
                            role_color = "blue" if func['role'] == "Tecnico" else "red" if func['role'] == "ADM" else "gray"
                            st.markdown(f"**{func['username']}** :{role_color}[({func['role']})]")
                            st.caption(f"📧 {func['email']}")
                        
                        if func['email'] != user_data['email']:
                            if col_b.button("Remover", key=f"del_{func['id']}", type="secondary", use_container_width=True):
                                if db.excluir_usuario_por_id(func['id'])[0]: st.rerun()
                        else: col_b.write("✨ (Você)")
            
       
            st.divider()
            st.write("### 🤖 Automação de Dados")
            res_bot = supabase.table("config_automacao").select("*").eq("org_name", org_name).execute()
            config_bot = res_bot.data[0] if res_bot.data else {}

            with st.container(border=True):
                st.markdown("**Relatórios Automáticos por E-mail**")
            
                with st.expander("⚙️ Configurar Agendamento e Receptores"):
                    # Prepara os e-mails
                    e_salvos = [x.strip() for x in config_bot.get('email_destino', '').split(',')] if config_bot.get('email_destino') else []
                    e_validos = [x for x in e_salvos if x in lista_emails]

                    
                    with st.form("form_config_bot_final"):
                        escolhidos = st.multiselect("Selecione quem recebe:", options=lista_emails, default=e_validos)
                        
                        cb1, cb2 = st.columns(2)
                        dias_lista = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                        dia_b = cb1.selectbox("Dia do envio", dias_lista, index=dias_lista.index(config_bot.get('dia_semana', 'Segunda')) if config_bot.get('dia_semana') in dias_lista else 0)
                        
                        # Horário
                        h_padrão = datetime.time(8, 0)
                        if config_bot.get('horario'):
                            try:
                                h_split = list(map(int, config_bot.get('horario').split(':')))
                                h_padrão = datetime.time(h_split[0], h_split[1])
                            except: pass
                        hora_b = cb2.time_input("Horário", value=h_padrão)
                        
                        st.write("---")
                        st.caption("Credenciais de Envio (SMTP)")
                        s_user = st.text_input("E-mail Remetente (Gmail)", value=config_bot.get('smtp_user', ''))
                        s_pass = st.text_input("Senha de App", type="password", placeholder="Vazio mantém a atual")

                        # BOTÃO DE SALVAR DENTRO DO FORM (Obrigatório)
                        if st.form_submit_button("💾 Salvar Configurações", use_container_width=True):
                            bot_dados = {
                                "org_name": org_name, "email_destino": ", ".join(escolhidos),
                                "dia_semana": dia_b, "horario": str(hora_b),
                                "smtp_user": s_user, "smtp_pass": s_pass if s_pass else config_bot.get('smtp_pass')
                            }
                            supabase.table("config_automacao").upsert(bot_dados).execute()
                            st.success("Configuração salva!")
                            st.rerun()
                    
                    # Ajuda (Popover) fora do form para não dar conflito
                    with st.popover("❓ Como conseguir a Senha de App?"):
                        st.write("1. Conta Google > Segurança > Verificação 2 Etapas.\n2. No final da página: Senhas de App.\n3. Gere a senha de 16 dígitos e cole no campo acima.")

                if config_bot:
                    if st.button("🚀 Disparar Relatório Manual Agora", use_container_width=True, type="primary"):
                        with st.spinner("Enviando..."):
                            if disparar_email_manual(config_bot, st): st.toast("Relatório enviado!", icon="✅")

        except Exception as e:
            st.error(f"Ocorreu um erro na aba equipe: {e}")

   
    with aba_laboratorio:
        st.subheader("🏢 Perfil da Organização")
        try:
            org_res = supabase.table("organizations").select("*").eq("id", org_id).execute()
            
         
            if not org_res.data:
                st.info("👋 Bem-vindo! Finalize o perfil da sua empresa abaixo.")
                with st.form("cadastro_org_novo"):
                    p_ativo = st.selectbox("Plano", ["Trial / Beta", "Essencial", "Premium"])
                    m_pagto = st.selectbox("Forma de Pagamento", ["PIX", "Cartão", "Boleto"])
                    if st.form_submit_button("Confirmar e Ativar Perfil"):
                        supabase.table("organizations").insert({
                            "id": org_id, "name": org_name, 
                            "plano_ativo": p_ativo, "metodo_pagto": m_pagto,
                            "status_assinatura": "Ativo"
                        }).execute()
                        st.rerun()
            else:
                # Se encontrar, mostra o layout original preenchido
                d = org_res.data[0]
                col_i, col_s = st.columns(2)
                with col_i:
                    with st.container(border=True):
                        st.markdown("### 🆔 Identidade")
                        st.write(f"**Laboratório:** {org_name}")
                        st.write("**ID Único:**")
                        st.code(org_id, language="text")
                with col_s:
                    with st.container(border=True):
                        st.markdown("### 💳 Assinatura")
                        st.markdown(f"**Status:** :green[{d.get('status_assinatura', 'Ativo').upper()} ✅]")
                        st.markdown(f"**Plano:** `{d.get('plano_ativo')}`")
                        st.write(f"**Pagamento:** {d.get('metodo_pagto')}")
                
                st.divider()
                st.button("Exportar Backup dos Dados", use_container_width=True, disabled=True)

        except Exception as e:
            st.error(f"Erro ao carregar laboratório: {e}")
