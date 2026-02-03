import streamlit as st

def show_configuracoes(supabase, user_data):
    # Botão de Voltar para sair da aba e retornar ao Dashboard
    if st.button("⬅️ Voltar para o Sistema", use_container_width=True):
        st.session_state.selection = "🏠 Dashboard"
        st.rerun()

    st.title("🛠️ Central de Personalização do Usuário")
    st.markdown(f"Configurações para: **{user_data['username']}** | Unidade: **{user_data.get('org_name')}**")
    st.markdown("---")

    # Inicializa estados de preferência se não existirem
    if 'prefs' not in st.session_state:
        st.session_state.prefs = {
            "cor_primaria": "#28a745",
            "tema_selecionado": "Padrão Synapse",
            "modulos_ocultos": [],
            "links_externos": []
        }

    tab_visual, tab_modulos, tab_links = st.tabs([
        "🎨 Identidade Visual", "🙈 Gestão de Menu", "🔗 Links Externos"
    ])

    # --- 1. IDENTIDADE VISUAL (Paletas de Cores) ---
    with tab_visual:
        st.subheader("Temas Disponíveis")
        st.write("Escolha uma paleta de cores para sua interface:")

        # Galeria de temas predefinidos
        temas = {
            "Padrão Synapse": "#28a745",
            "Oceanic Blue": "#0077b6",
            "Deep Purple": "#6f42c1",
            "Carbon Dark": "#343a40",
            "Solar Orange": "#fd7e14",
            "Laboratory Red": "#dc3545"
        }

        # Criando colunas para a galeria de temas
        cols = st.columns(3)
        for idx, (nome_tema, cor_tema) in enumerate(temas.items()):
            with cols[idx % 3]:
                # Mostra um quadrado da cor
                st.markdown(f"""
                    <div style="background-color: {cor_tema}; width: 100%; height: 20px; border-radius: 5px; margin-bottom: 5px;"></div>
                """, unsafe_allow_html=True)
                
                if st.button(nome_tema, key=f"btn_tema_{idx}", use_container_width=True):
                    st.session_state.prefs["cor_primaria"] = cor_tema
                    st.session_state.prefs["tema_selecionado"] = nome_tema
                    st.toast(f"Tema {nome_tema} aplicado!")
                    st.rerun()

        st.divider()
        # Opção de cor customizada caso ele não queira os temas prontos
        st.write("Ou escolha uma cor personalizada:")
        cor_custom = st.color_picker("Cor Personalizada", st.session_state.prefs["cor_primaria"])
        if cor_custom != st.session_state.prefs["cor_primaria"]:
            st.session_state.prefs["cor_primaria"] = cor_custom
            st.session_state.prefs["tema_selecionado"] = "Customizado"
            st.rerun()

    # --- 2. VISIBILIDADE (Mostrar/Ocultar botões do Sidebar) ---
    with tab_modulos:
        st.subheader("Personalizar Menu Lateral")
        st.write("Escolha quais botões você deseja que apareçam no seu menu principal:")
        
        # Módulos que o usuário pode ligar/desligar momentaneamente
        opcoes_modulos = ["🤖 IA & Visão", "💼 Laboratório", "⚛️ Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
        
        for modulo in opcoes_modulos:
            # Se o módulo NÃO está na lista de ocultos, o checkbox começa marcado
            is_visible = modulo not in st.session_state.prefs["modulos_ocultos"]
            
            check = st.checkbox(f"Mostrar {modulo}", value=is_visible, key=f"vis_{modulo}")
            
            # Se ele desmarcar, adicionamos aos ocultos
            if not check and is_visible:
                st.session_state.prefs["modulos_ocultos"].append(modulo)
                st.rerun()
            # Se ele marcar, removemos dos ocultos
            elif check and not is_visible:
                st.session_state.prefs["modulos_ocultos"].remove(modulo)
                st.rerun()

    # --- 3. LINKS EXTRAS ---
    with tab_links:
        st.subheader("Meus Atalhos")
        
        col_n, col_u, col_b = st.columns([2, 2, 1])
        nome_link = col_n.text_input("Nome do Site", placeholder="Ex: Google")
        url_link = col_u.text_input("URL", placeholder="https://...")
        if col_b.write("") or col_b.button("Adicionar", use_container_width=True):
            if nome_link and url_link:
                st.session_state.prefs["links_externos"].append({"nome": nome_link, "url": url_link})
                st.rerun()

        st.divider()
        for i, link in enumerate(st.session_state.prefs["links_externos"]):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"🔗 **[{link['nome']}]({link['url']})**")
            if c2.button("Remover", key=f"del_link_{i}"):
                st.session_state.prefs["links_externos"].pop(i)
                st.rerun()

    st.markdown("---")
    st.caption(f"SynapseLab - Configurações Individuais Aplicadas | Tema Atual: {st.session_state.prefs['tema_selecionado']}")
