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
    st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; font-weight: 700; }</style>", unsafe_allow_html=True)
    st.title("⚙️ Painel de Controle")
    
    user_data = st.session_state.user_data
    org_id, org_name = user_data.get('org_id'), user_data.get('org_name')
    
    aba_equipe, aba_laboratorio = st.tabs(["👥 Gestão de Equipe", "🏢 Dados da Empresa"])

    with aba_equipe:
        try:
            res = supabase.table("users").select("*").eq("org_name", org_name).execute()
            df = pd.DataFrame(res.data)
            lista_emails = df['email'].tolist() if not df.empty else []

            if not df.empty:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Membros", len(df))
                c2.metric("Técnicos", len(df[df['role'] == 'Tecnico']))
                c3.metric("ADMs", len(df[df['role'] == 'ADM']))
                c4.metric("Visualizadores", len(df[df['role'] == 'Visualizador']))
                st.bar_chart(df['role'].value_counts(), height=150)

            st.divider()
            with st.expander("➕ **Adicionar Membro**"):
                with st.form("cadastrar_interno", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    n, e = c1.text_input("Nome"), c2.text_input("E-mail")
                    s, cargo = c1.text_input("Senha", type="password"), c2.selectbox("Cargo", ["Visualizador", "Tecnico", "ADM"])
                    if st.form_submit_button("Liberar Acesso", use_container_width=True):
                        if n and e and s:
                            suc, msg = db.cadastrar_usuario(n, e, s, org_name, cargo)
                            if suc: st.rerun()
                            else: st.error(msg)

            st.write("### 📋 Equipe")
            if not df.empty:
                for _, f in df.iterrows():
                    with st.container(border=True):
                        col_t, col_b = st.columns([4, 1])
                        col_t.write(f"**{f['username']}** ({f['role']})")
                        if f['email'] != user_data['email']:
                            if col_b.button("Remover", key=f"del_{f['id']}", use_container_width=True):
                                db.excluir_usuario_por_id(f['id'])
                                st.rerun()

            st.divider()
            st.write("### 🤖 Automação")
            res_bot = supabase.table("config_automacao").select("*").eq("org_name", org_name).execute()
            config_bot = res_bot.data[0] if res_bot.data else {}

            with st.container(border=True):
                with st.expander("⚙️ Configurar Destinatários e SMTP"):
                    e_salvos = [x.strip() for x in config_bot.get('email_destino', '').split(',')] if config_bot.get('email_destino') else []
                    e_validos = [x for x in e_salvos if x in lista_emails]

                    receptores = st.multiselect("Quem receberá o relatório?", options=lista_emails, default=e_validos)
                    
                    col_b1, col_b2 = st.columns(2)
                    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                    dia_bot = col_b1.selectbox("Dia", dias, index=dias.index(config_bot.get('dia_semana', 'Segunda')) if config_bot.get('dia_semana') in dias else 0)
                    hora_bot = col_b2.time_input("Hora", value=datetime.time(8,0))

                    st.write("---")
                    c_label, c_help = st.columns([3, 1])
                    c_label.caption("Credenciais SMTP")
                    with c_help.popover("❓ Ajuda"):
                        st.markdown("**Como obter a Senha de App:**\n1. Conta Google > Segurança\n2. Ative Verificação em 2 Etapas\n3. No fim, crie uma 'Senha de App'\n4. Copie os 16 dígitos.")

                    s_user = st.text_input("Seu E-mail (Gmail)", value=config_bot.get('smtp_user', ''))
                    s_pass = st.text_input("Senha de App", type="password", placeholder="Deixe vazio para manter a atual")

                    if st.form_submit_button("Salvar Tudo", use_container_width=True):
                        bot_data = {
                            "org_name": org_name, "email_destino": ", ".join(receptores),
                            "dia_semana": dia_bot, "horario": str(hora_bot),
                            "smtp_user": s_user, "smtp_pass": s_pass if s_pass else config_bot.get('smtp_pass')
                        }
                        supabase.table("config_automacao").upsert(bot_data).execute()
                        st.success("Salvo!")
                        st.rerun()

                if config_bot:
                    if st.button("🚀 Disparar Agora", use_container_width=True, type="primary"):
                        if disparar_email_manual(config_bot, st): st.toast("Enviado!")

        except Exception as ex: st.error(f"Erro: {ex}")

    with aba_laboratorio:
        # (Seu código original da aba laboratório aqui)
        st.subheader(f"🏢 {org_name}")
        st.write(f"ID: `{org_id}`")
