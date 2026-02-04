import streamlit as st

def show_configuracoes(supabase, user_data):
    if st.button("⬅️ Voltar para o Sistema", use_container_width=True):
        st.session_state.selection = "🏠 Dashboard"
        st.rerun()

    st.title("🛠️ Central de Personalização do Usuário")
    st.markdown(f"Configurações para: **{user_data['username']}** | Unidade: **{user_data.get('org_name')}**")
    st.markdown("---")

    if 'prefs' not in st.session_state:
        st.session_state.prefs = {
            "cor_primaria": "#28a745",
            "tema_selecionado": "Padrão Synapse",
            "modulos_ocultos": [],
            "links_externos": [],
            "classe_css": ""
        }

    tab_visual, tab_modulos, tab_links = st.tabs([
        "🎨 Identidade Visual", "🙈 Gestão de Menu", "🔗 Links Externos"
    ])

    with tab_visual:
        st.subheader("Temas Disponíveis")
        st.write("Escolha uma paleta. Isso alterará botões, bordas e detalhes:")

        # Atualizado para incluir as classes do style.css
        temas = {
            "Padrão Synapse (Verde)": ("#28a745", ""),
            "Deep Ocean (Azul)": ("#0077b6", "tema-ocean"),
            "Deep Purple (Roxo)": ("#6f42c1", "tema-violet"),
            "Carbon Dark (Cinza)": ("#343a40", "tema-slate"),
            "Solar Orange (Laranja)": ("#fd7e14", "tema-sunset"),
            "Laboratory Red (Vermelho)": ("#dc3545", "tema-red"),
            "Pink Neon (Rosa)": ("#ff007f", "tema-pink"),
            "Cyan Future (Ciano)": ("#00e5ff", "tema-arctic"),
            "Luxury Gold": ("#d4af37", "tema-gold"),
            "Matrix Mode": ("#00ff41", "tema-matrix")
        }

        cols = st.columns(4)
        for idx, (nome_tema, dados) in enumerate(temas.items()):
            cor_tema, classe_css = dados
            with cols[idx % 4]:
                st.markdown(f"""
                    <div style="background-color: {cor_tema}; width: 100%; height: 30px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #fff;"></div>
                """, unsafe_allow_html=True)
                
                if st.button(nome_tema, key=f"btn_tema_{idx}", use_container_width=True):
                    st.session_state.prefs["cor_primaria"] = cor_tema
                    st.session_state.prefs["classe_css"] = classe_css
                    st.session_state.prefs["tema_selecionado"] = nome_tema
                    
                    try:
                        supabase.table("users").update({
                            "cor_primaria": cor_tema,
                            "classe_css": classe_css
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
            st.session_state.prefs["classe_css"] = ""
            
            supabase.table("users").update({
                "cor_primaria": cor_custom,
                "classe_css": ""
            }).eq("id", user_data['id']).execute()
            
            st.rerun()

    with tab_modulos:
        st.subheader("Personalizar Menu Lateral")
        st.write("Marque o que você quer ver no menu. Desmarque para esconder.")
        
        opcoes_modulos = ["🤖 IA & Visão", "💼 Laboratório", "⚛️ Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
        
        for modulo in opcoes_modulos:
            is_visible = modulo not in st.session_state.prefs["modulos_ocultos"]
            check = st.checkbox(f"Mostrar {modulo}", value=is_visible, key=f"vis_{modulo}")
            
            if check != is_visible:
                if not check:
                    st.session_state.prefs["modulos_ocultos"].append(modulo)
                else:
                    st.session_state.prefs["modulos_ocultos"].remove(modulo)
                
                supabase.table("users").update({
                    "modulos_ocultos": st.session_state.prefs["modulos_ocultos"]
                }).eq("id", user_data['id']).execute()
                
                st.rerun()

    with tab_links:
        st.subheader("Meus Atalhos")
        
        col_n, col_u, col_b = st.columns([2, 2, 1])
        nome_link = col_n.text_input("Nome do Site", placeholder="Ex: Google")
        url_link = col_u.text_input("URL", placeholder="https://...")
        
        if col_b.button("Adicionar Link", use_container_width=True):
            if nome_link and url_link:
                novo_link = {"nome": nome_link, "url": url_link}
                st.session_state.prefs["links_externos"].append(novo_link)
                
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
                
                supabase.table("users").update({
                    "links_externos": st.session_state.prefs["links_externos"]
                }).eq("id", user_data['id']).execute()
                
                st.rerun()

    st.markdown("---")
    st.caption(f"SynapseLab - Configurações salvas na nuvem | Tema Atual: {st.session_state.prefs.get('tema_selecionado', 'N/A')}")
