import streamlit as st
import os
import sys
import auth_db as db 
from supabase import create_client

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração da página
st.set_page_config(
    page_title="SynapseLab", 
    page_icon="https://i.ibb.co/6cKPZ5Pr/Gemini-Generated-Image-jes56ljes56ljes5.png", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONEXÃO COM SUPABASE ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erro de conexão com Banco de Dados: {e}")
    st.stop()

# --- INICIALIZAÇÃO DE ESTADOS ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'user_data' not in st.session_state: st.session_state.user_data = None
if 'selection' not in st.session_state: st.session_state.selection = "🏠 Dashboard"
# Inicializa preferências com o padrão (Verde e sem ocultos)
if 'prefs' not in st.session_state:
    st.session_state.prefs = {
        "cor_primaria": "#28a745", 
        "modulos_ocultos": [], 
        "links_externos": []
    }

# --- APLICAÇÃO DE ESTILO (CSS DINÂMICO) ---
# Lê o CSS original e substitui a cor principal pela preferência do usuário
try:
    with open("style.css", "r", encoding="utf-8") as f:
        base_css = f.read()
        
    # Pega a cor do usuário (ou usa o verde padrão se não tiver)
    cor_user = st.session_state.prefs.get("cor_primaria", "#28a745")
    
    # TRUQUE DE MESTRE: Substitui todas as ocorrências do Verde Original pela Cor do Usuário
    # Isso mantém 100% da estrutura do seu CSS, mudando apenas a paleta.
    css_dinamico = base_css.replace("#28a745", cor_user)
    
    st.markdown(f"<style>{css_dinamico}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Arquivo style.css não encontrado.")

def tela_acesso():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("")
        logo_url = "https://i.ibb.co/6cKPZ5Pr/Gemini-Generated-Image-jes56ljes56ljes5.png"
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
                <img src="{logo_url}" style="
                    width: 180px; 
                    height: 180px; 
                    border-radius: 50%; 
                    object-fit: cover;
                    background-color: transparent;
                ">
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.subheader("Login Administrativo")
        email_input = st.text_input("E-mail Profissional", key="l_email")
        senha_input = st.text_input("Senha de Acesso", type="password", key="l_pass")
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            user = db.buscar_usuario_por_email(email_input)
            if user and db.verificar_senha(senha_input, user['password_hash']):
                st.session_state.logado = True
                st.session_state.user_data = user
                
                # --- CARREGA PREFERÊNCIAS DO BANCO ---
                # Se as colunas não existirem no banco ainda, usa o .get() com valor padrão
                st.session_state.prefs = {
                    "cor_primaria": user.get("cor_primaria", "#28a745"),
                    "modulos_ocultos": user.get("modulos_ocultos", []),
                    "links_externos": user.get("links_externos", [])
                }
                st.rerun()
            else:
                st.error("Dados incorretos.")
        
        st.markdown("---")
        st.markdown("<p style='text-align: center; color: var(--text-gray);'>Se não tiver uma conta, clique abaixo:</p>", unsafe_allow_html=True)
        st.link_button("Cadastro Empresarial", "https://synapselab-cadastro-clientes.vercel.app/", use_container_width=True)

if not st.session_state.logado:
    tela_acesso()
else:
    # --- IMPORTAÇÃO DE MÓDULOS ---
    try:
        from substancias import show_substances
        from ControleEstoque import show_estoque
        from equipamentos import show_equipamentos
        from calculadora import show_calculadora
        from sistematabela import show_tabelas
        from graficos import show_graficos
        from vidrarias import *
        from projetos import *
        from config_empresa import show_config_empresa 
        import ia
        from configurações import show_configuracoes
        import relatorios
        from perfil_usuario import show_perfil
    except ImportError as e:
        st.error(f"Erro ao carregar módulos: {e}")

    user = st.session_state.user_data
    role = user.get('role', 'Visualizador')
    org_atual = user.get('org_name')
    
    # Lógica de foto dinâmica para a Sidebar
    foto_sidebar = user.get('avatar_url') if user.get('avatar_url') else f"https://api.dicebear.com/7.x/avataaars/svg?seed={user['username']}"
    
    # --- SIDEBAR DE NAVEGAÇÃO ---
    with st.sidebar:
        # Pega a cor do usuário para aplicar na borda da foto e do card via inline style também, por garantia
        cor_borda = st.session_state.prefs.get("cor_primaria", "#28a745")
        
        st.markdown(f"""
            <div class="user-card" style="border: 1px solid {cor_borda};">
                <small style="font-weight: 800; font-size: 0.7rem; color: {cor_borda};">ORGANIZAÇÃO</small><br>
                <span style="font-size: 1rem; font-weight: 700;">{org_atual}</span><br>
                <hr style="border-top: 2px solid {cor_borda} !important;">
                <img src="{foto_sidebar}" class="profile-img" style="border: 2px solid {cor_borda};">
                <div style="margin-top: 5px;">
                    <span style="font-size: 0.9rem;">{user['username']}</span><br>
                    <span style="background: {cor_borda}; color: black; font-weight:bold; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px;">{role}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.popover("⋮ Opções"):
            if st.button("👤 Perfil do Usuário", use_container_width=True):
                st.session_state.selection = "👤 Perfil"
                st.rerun()
            if st.button("⚙️ Configurações Gerais", use_container_width=True):
                st.session_state.selection = "⚙️ Configurações"
                st.rerun()
            st.divider()
            if st.button("SAIR", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.write("") 
        
        # Lista original completa de abas
        abas_base = ["🏠 Dashboard", "🤖 IA & Visão", "💼 Laboratório", "⚛️ Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
        if role == "ADM":
            abas_base.extend(["👥 Gestão de Equipe", "📄 Relatórios"])

        # FILTRO DE MÓDULOS (Novidade: Remove os ocultos da lista)
        modulos_ocultos = st.session_state.prefs.get("modulos_ocultos", [])
        abas = [aba for aba in abas_base if aba not in modulos_ocultos]

        # Sincroniza o rádio com a seleção
        opcoes_radio = abas.copy()
        if st.session_state.selection not in opcoes_radio:
            opcoes_radio.append(st.session_state.selection)

        selection = st.radio("NAVEGAÇÃO", opcoes_radio, index=opcoes_radio.index(st.session_state.selection))
        st.session_state.selection = selection
        
        # Exibe Links Externos cadastrados na Sidebar
        links_extras = st.session_state.prefs.get("links_externos", [])
        if links_extras:
            st.markdown("---")
            st.caption("Atalhos Rápidos")
            for link in links_extras:
                st.markdown(f"🔗 [{link['nome']}]({link['url']})")

    # --- ROTEAMENTO ---
    if st.session_state.selection == "👤 Perfil":
        show_perfil() # Se precisar de user_data aqui futuramente, adicione
    elif st.session_state.selection == "⚙️ Configurações":
        show_configuracoes(supabase, user) # Passando as variáveis necessárias
    else:
        clean_selection = selection.split(" ", 1)[-1]

        if clean_selection == "Dashboard":
            st.title(f"🚀 Painel de Controle - {org_atual}")
            try:
                res_sub = supabase.table("substancias").select("quantidade").eq("org_name", org_atual).execute()
                total_itens = sum([i['quantidade'] for i in res_sub.data]) if res_sub.data else 0
                res_eq = supabase.table("equipamentos").select("id", count="exact").eq("org_name", org_atual).execute()
                total_equip = res_eq.count if res_eq.count else 0
                total_analises = len(res_sub.data)
            except:
                total_itens, total_equip, total_analises = 0, 0, 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Itens no Estoque", f"{total_itens:,}".replace(",", "."), delta="Operacional")
            m2.metric("Equipamentos", total_equip, "Ativos")
            m3.metric("Registros", total_analises, "Total")
            m4.metric("Usuário", user['username'], f"Nível {role}")

            st.markdown("---")
            st.subheader("Atalhos e Guias Rápidos")
            
            # Atalhos só aparecem se o módulo não estiver oculto nas configurações
            c1, c2, c3 = st.columns(3)
            with c1:
                if "🤖 IA & Visão" not in modulos_ocultos:
                    if st.button("🤖 Central de IA", use_container_width=True):
                        st.session_state.selection = "🤖 IA & Visão"; st.rerun()
            with c2:
                if "⚛️ Tabelas Químicas" not in modulos_ocultos:
                    if st.button("⚛️ Tabelas e Reagentes", use_container_width=True):
                        st.session_state.selection = "⚛️ Tabelas Químicas"; st.rerun()
            with c3:
                if "🧮 Calculadora Química" not in modulos_ocultos:
                    if st.button("🧮 Calculadora de Soluções", use_container_width=True):
                        st.session_state.selection = "🧮 Calculadora Química"; st.rerun()

            st.write("")
            ca, cb, cc = st.columns(3)
            with ca:
                if "📊 Gráficos" not in modulos_ocultos:
                    if st.button("📊 Analisar Gráficos", use_container_width=True):
                        st.session_state.selection = "📊 Gráficos"; st.rerun()
            
            if role in ["Tecnico", "ADM"]:
                with cb:
                    if "💼 Laboratório" not in modulos_ocultos:
                        if st.button("📦 Abrir Estoque", use_container_width=True):
                            st.session_state.selection = "💼 Laboratório"; st.rerun()
                with cc:
                     if "💼 Laboratório" not in modulos_ocultos:
                        if st.button("⚗️ Novo Cadastro", use_container_width=True):
                            st.session_state.selection = "💼 Laboratório"; st.rerun()
            else:
                with cb:
                    st.button("🔒 Estoque (Restrito)", disabled=True, use_container_width=True)

        elif clean_selection == "Laboratório":
            st.title("💼 Central do Laboratório")
            if role in ["Tecnico", "ADM"]:
                sub_tabs = st.tabs(["📦 Estoque Atual", "⚗️ Cadastro de Substâncias", "🛠️ Equipamentos","🧪 Vidrarias","📋 Projetos"])
                with sub_tabs[0]: show_estoque()
                with sub_tabs[1]: show_substances()
                with sub_tabs[2]: show_equipamentos()
                with sub_tabs[3]: render_vidrarias()
                with sub_tabs[4]: render_projetos()
            else:
                st.info("Você tem permissão apenas para visualização do estoque.")
                show_estoque()

        elif clean_selection == "IA & Visão": ia.show_chatbot()
        elif clean_selection == "Tabelas Químicas": show_tabelas()
        elif clean_selection == "Calculadora Química": show_calculadora()
        elif clean_selection == "Gráficos": show_graficos()
        elif clean_selection == "Gestão de Equipe": show_config_empresa()
        elif clean_selection == "Relatórios": relatorios.show_reports(supabase)

    st.sidebar.markdown("---")
    st.sidebar.caption("SynapseLab V.Beta")

