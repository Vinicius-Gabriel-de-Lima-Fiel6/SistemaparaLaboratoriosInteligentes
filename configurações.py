import streamlit as st

def show_configuracoes(supabase, user_data):
    # Botão de Voltar para sair da aba e retornar ao Dashboard
    if st.button("⬅️ Voltar para o Sistema", use_container_width=True):
        st.session_state.selection = "🏠 Dashboard"
        st.rerun()

    st.title("🛠️ Central de Personalização do Usuário")
    st.markdown(f"Configurações para: **{user_data['username']}** | Unidade: **{user_data.get('org_name')}**")
    st.markdown("---")

    # Garante que as chaves existam na sessão
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
        st.write("Escolha uma paleta. Isso alterará botões, bordas e detalhes:")

        # Galeria de temas predefinidos (Expansível conforme sua vontade)
        temas = {
            "Padrão Synapse (Verde)": "#28a745",
            "Oceanic Blue (Azul)": "#0077b6",
            "Deep Purple (Roxo)": "#6f42c1",
            "Carbon Dark (Cinza)": "#343a40",
            "Solar Orange (Laranja)": "#fd7e14",
            "Laboratory Red (Vermelho)": "#dc3545",
            "Pink Neon (Rosa)": "#ff007f",
            "Cyan Future (Ciano)": "#00e5ff"
        }

        # Criando colunas para a galeria de temas
        cols = st.columns(4)
        for idx, (nome_tema, cor_tema) in enumerate(temas.items()):
            with cols[idx % 4]:
                # Mostra um quadrado da cor
                st.markdown(f"""
                    <div style="background-color: {cor_tema}; width: 100%; height: 30px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #fff;"></div>
                """, unsafe_allow_html=True)
                
                if st.button(nome_tema, key=f"btn_tema_{idx}", use_container_width=True):
                    # 1. Atualiza Sessão
                    st.session_state.prefs["cor_primaria"] = cor_tema
                    st.session_state.prefs["tema_selecionado"] = nome_tema
                    
                    # 2. Salva no Supabase (coluna cor_primaria na tabela users)
                    try:
                        supabase.table("users").update({
                            "cor_primaria": cor_tema
                        }).eq("id", user_data['id']).execute()
                        st.toast(f"Tema {nome_tema} aplicado e salvo!")
                    except Exception as e:
                        st.error(f"Erro ao salvar tema: {e}")
                    
                    st.rerun()

        st.divider()
        st.write("Ou escolha uma cor personalizada:")
        cor_custom = st.color_picker("Seletor de Cor", st.session_state.prefs["cor_primaria"])
        
        if st.button("Aplicar Cor Personalizada", use_container_width=True):
            st.session_state.prefs["cor_primaria"] = cor_custom
            st.session_state.prefs["tema_selecionado"] = "Customizado"
            
            # Salva no Supabase
            supabase.table("users").update({
                "cor_primaria": cor_custom
            }).eq("id", user_data['id']).execute()
            
            st.rerun()

    # --- 2. VISIBILIDADE (Mostrar/Ocultar botões do Sidebar) ---
    with tab_modulos:
        st.subheader("Personalizar Menu Lateral")
        st.write("Marque o que você quer ver no menu. Desmarque para esconder.")
        
        opcoes_modulos = ["🤖 IA & Visão", "💼 Laboratório", "⚛️ Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
        
        for modulo in opcoes_modulos:
            # Lógica invertida: Se NÃO está na lista de ocultos, checkbox = True
            is_visible = modulo not in st.session_state.prefs["modulos_ocultos"]
            
            check = st.checkbox(f"Mostrar {modulo}", value=is_visible, key=f"vis_{modulo}")
            
            # Detecta mudança
            if check != is_visible:
                if not check: # Usuário desmarcou -> Adicionar aos ocultos
                    st.session_state.prefs["modulos_ocultos"].append(modulo)
                else: # Usuário marcou -> Remover dos ocultos
                    st.session_state.prefs["modulos_ocultos"].remove(modulo)
                
                # Salva no Supabase
                supabase.table("users").update({
                    "modulos_ocultos": st.session_state.prefs["modulos_ocultos"]
                }).eq("id", user_data['id']).execute()
                
                st.rerun()

    # --- 3. LINKS EXTRAS ---
    with tab_links:
        st.subheader("Meus Atalhos")
        
        col_n, col_u, col_b = st.columns([2, 2, 1])
        nome_link = col_n.text_input("Nome do Site", placeholder="Ex: Google")
        url_link = col_u.text_input("URL", placeholder="https://...")
        
        if col_b.button("Adicionar Link", use_container_width=True):
            if nome_link and url_link:
                novo_link = {"nome": nome_link, "url": url_link}
                st.session_state.prefs["links_externos"].append(novo_link)
                
                # Salva no Supabase
                supabase.table("users").update({
                    "links_externos": st.session_state.prefs["links_externos"]
                }).eq("id", user_data['id']).execute()
                
                st.rerun()

        st.divider()
        st.write("Seus links atuais:")
        for i, link in enumerate(st.session_state.prefs["links_externos"]):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"🔗 **[{link['nome']}]({link['url']})**")
            if c2.button("🗑️ Remover", key=f"del_link_{i}"):
                st.session_state.prefs["links_externos"].pop(i)
                
                # Atualiza no Supabase após remover
                supabase.table("users").update({
                    "links_externos": st.session_state.prefs["links_externos"]
                }).eq("id", user_data['id']).execute()
                
                st.rerun()

    st.markdown("---")
    st.caption(f"SynapseLab - Configurações salvas na nuvem | Tema Atual: {st.session_state.prefs.get('tema_selecionado', 'N/A')}")
