import streamlit as st

def show_configuracoes(supabase, user_data):
    # Botão de Voltar no topo para sair dessa "aba" e voltar ao Dashboard
    if st.button("⬅️ Voltar para o Sistema"):
        st.session_state.selection = "🏠 Dashboard"
        st.rerun()

    st.title("🛠️ Central de Personalização do Usuário")
    st.markdown("---")

    # Inicializa estados de preferência se não existirem
    if 'prefs' not in st.session_state:
        st.session_state.prefs = {
            "cor_primaria": "#28a745",
            "modulos_ocultos": [],
            "links_externos": [
                {"nome": "Planilha de Apoio Excel", "url": "https://office.com"},
                {"nome": "Dashboard Power BI", "url": "https://powerbi.com"}
            ]
        }

    tab_perfil, tab_visual, tab_modulos, tab_links = st.tabs([
        "👤 Perfil & Foto", "🎨 Identidade Visual", "🙈 Visibilidade", "🔗 Links Externos"
    ])

    # --- 1. PERFIL E FOTO ---
    with tab_perfil:
        st.subheader("Configurações de Identidade")
        col1, col2 = st.columns([1, 2])
        with col1:
            foto_url = user_data.get('avatar_url') if user_data.get('avatar_url') else f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_data['username']}"
            st.image(foto_url, width=150)
            st.file_uploader("Alterar Foto", type=['jpg', 'png'])
        with col2:
            st.text_input("Nome Profissional", value=user_data['username'])
            st.text_input("Cargo/Função", value=user_data.get('role', 'Técnico'))
            if st.button("Salvar Perfil"):
                st.success("Dados de perfil salvos!")

    # --- 2. IDENTIDADE VISUAL (Dinamismo de Cores) ---
    with tab_visual:
        st.subheader("Paleta de Cores Pessoal")
        st.info("Estas cores serão aplicadas à sua interface individual.")
        nova_cor = st.color_picker("Cor Primária do Sistema (Botões e Destaques)", st.session_state.prefs["cor_primaria"])
        
        if nova_cor != st.session_state.prefs["cor_primaria"]:
            st.session_state.prefs["cor_primaria"] = nova_cor
            st.success(f"Cor alterada para {nova_cor}. O sistema aplicará as mudanças.")
            st.rerun()

    # --- 3. VISIBILIDADE (O que ele não quer ver) ---
    with tab_modulos:
        st.subheader("Gerenciar Módulos Visíveis")
        st.write("Desmarque os módulos que você não utiliza para simplificar sua navegação.")
        
        opcoes_modulos = ["🤖 IA & Visão", "🧪 Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
        
        for modulo in opcoes_modulos:
            is_visible = modulo not in st.session_state.prefs["modulos_ocultos"]
            check = st.checkbox(modulo, value=is_visible)
            
            if not check and is_visible:
                st.session_state.prefs["modulos_ocultos"].append(modulo)
                st.rerun()
            elif check and not is_visible:
                st.session_state.prefs["modulos_ocultos"].remove(modulo)
                st.rerun()

    # --- 4. LINKS EXTRAS (Excel, Power BI, etc) ---
    with tab_links:
        st.subheader("Meus Atalhos Externos")
        
        # Exibe links atuais
        for link in st.session_state.prefs["links_externos"]:
            col_l, col_b = st.columns([3, 1])
            col_l.markdown(f"🔗 **[{link['nome']}]({link['url']})**")
            if col_b.button("Remover", key=link['nome']):
                st.session_state.prefs["links_externos"].remove(link)
                st.rerun()
        
        st.divider()
        st.write("Adicionar Novo Atalho")
        nome_link = st.text_input("Nome do Site")
        url_link = st.text_input("URL (Link)")
        if st.button("Adicionar Link"):
            if nome_link and url_link:
                st.session_state.prefs["links_externos"].append({"nome": nome_link, "url": url_link})
                st.success("Link adicionado!")
                st.rerun()

    st.markdown("---")
    st.caption("LabSmartAI - Configurações Avançadas v1.0")
