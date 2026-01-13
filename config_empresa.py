import streamlit as st
import pandas as pd
from supabase import create_client
import auth_db as db
import datetime

# Importação segura
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
                st.write("📊 **Distribuição de Cargos**")
                st.bar_chart(df['role'].value_counts(), height=150)

            st.divider()

          
            with st.expander("➕ **Adicionar Novo Membro**"):
                with st.form("cadastrar_interno"):
                    c1, c2 = st.columns(2)
                    n_f = c1.text_input("Nome")
                    e_f = c2.text_input("E-mail")
                    s_f = c1.text_input("Senha", type="password")
                    c_f = c2.selectbox("Acesso", ["Visualizador", "Tecnico", "ADM"])
                    if st.form_submit_button("Liberar Acesso", use_container_width=True):
                        if n_f and e_f and s_f:
                            suc, msg = db.cadastrar_usuario(n_f, e_f, s_f, org_name, c_f)
                            if suc: st.rerun()
                            else: st.error(msg)

            # Lista de Equipe
            if not df.empty:
                for _, f in df.iterrows():
                    with st.container(border=True):
                        col_t, col_b = st.columns([4, 1])
                        col_t.markdown(f"**{f['username']}** ({f['role']}) \n\n {f['email']}")
                        if f['email'] != user_data['email']:
                            if col_b.button("Remover", key=f"del_{f['id']}", use_container_width=True):
                                db.excluir_usuario_por_id(f['id'])
                                st.rerun()

            st.divider()
            st.write("### 🤖 Automação de Dados")
            res_bot = supabase.table("config_automacao").select("*").eq("org_name", org_name).execute()
            config_bot = res_bot.data[0] if res_bot.data else {}

            with st.container(border=True):
                with st.expander("⚙️ Configurar Agendamento"):
                    e_salvos = [x.strip() for x in config_bot.get('email_destino', '').split(',')] if config_bot.get('email_destino') else []
                    
                   
                    with st.form("form_bot_final"):
                        receptores = st.multiselect("Destinatários", options=lista_emails, default=[e for e in e_salvos if e in lista_emails])
                        col_b1, col_b2 = st.columns(2)
                        dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                        dia_bot = col_b1.selectbox("Dia", dias)
                        hora_bot = col_b2.time_input("Hora", value=datetime.time(8, 0))
                        
                        st.write("---")
                        s_user = st.text_input("E-mail Remetente", value=config_bot.get('smtp_user', ''))
                        s_pass = st.text_input("Senha de App", type="password")

                        # O BOTÃO DE SALVAR ESTÁ AGORA DENTRO DO FORM (Essencial!)
                        if st.form_submit_button("💾 Salvar Configuração", use_container_width=True):
                            bot_data = {
                                "org_name": org_name, "email_destino": ", ".join(receptores),
                                "dia_semana": dia_bot, "horario": str(hora_bot),
                                "smtp_user": s_user, "smtp_pass": s_pass if s_pass else config_bot.get('smtp_pass')
                            }
                            supabase.table("config_automacao").upsert(bot_data).execute()
                            st.success("Salvo!")
                            st.rerun()

        except Exception as e:
            st.error(f"Erro na equipe: {e}")

   
    with aba_laboratorio:
        st.subheader("🏢 Perfil da Organização")
        

        if not org_id or org_id == "None":
            st.error("⚠️ Erro Crítico: ID da Organização não detectado. Contate o suporte.")
            return

        try:
            # Tenta buscar os dados
            org_res = supabase.table("organizations").select("*").eq("id", org_id).execute()
            
            if not org_res.data:
                
                st.info(f"O perfil da **{org_name}** ainda não foi finalizado.")
                with st.form("ativar_empresa"):
                    plano = st.selectbox("Plano", ["Trial / Beta", "Essencial", "Premium"])
                    metodo = st.selectbox("Pagamento", ["PIX", "Cartão", "Boleto"])
                    if st.form_submit_button("🚀 Ativar Perfil da Empresa"):
                        supabase.table("organizations").insert({
                            "id": org_id, "name": org_name, 
                            "plano_ativo": plano, "metodo_pagto": metodo,
                            "status_assinatura": "Ativo"
                        }).execute()
                        st.rerun()
            else:
            
                dados = org_res.data[0]
                c_id, c_pl = st.columns(2)
                with c_id:
                    with st.container(border=True):
                        st.markdown(f"### 🆔 Identidade\n**Nome:** {org_name}\n\n**ID:** `{org_id}`")
                with c_pl:
                    with st.container(border=True):
                        st.markdown(f"### 💳 Assinatura\n**Status:** :green[ATIVO ✅]\n\n**Plano:** {dados.get('plano_ativo')}")

        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
