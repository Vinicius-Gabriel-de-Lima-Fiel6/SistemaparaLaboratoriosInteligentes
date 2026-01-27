import streamlit as st
import os
import sys
import auth_db as db 
from supabase import create_client

# Garante que o caminho do projeto está no sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração da Página
st.set_page_config(
    page_title="LabSmartAI", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS GLOBAL REFINADO ---
st.markdown("""
    <style>
    /* Fundo principal e texto */
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
    }
    
    /* Estilização da Sidebar Dark */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }

    /* Cartão Postal de Usuário na Sidebar */
    .profile-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #000000 100%);
        border: 1px solid #28a745;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 10px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .profile-pic {
        width: 80px; height: 80px;
        border-radius: 50%;
        border: 2px solid #28a745;
        margin: 10px auto;
        object-fit: cover;
        display: block;
    }
    .org-label { font-size: 0.6rem; color: #28a745; text-transform: uppercase; letter-spacing: 2px; font-weight: 800; }
    .user-name { font-size: 1.1rem; font-weight: bold; margin: 5px 0; color: white !important; }
    .user-role { font-size: 0.7rem; background: #28a745; color: white !important; padding: 2px 10px; border-radius: 10px; }

    /* Menu Suspenso (Popover) Custom */
    div[data-testid="stPopover"] > button {
        background-color: transparent !important;
        color: #28a745 !important;
        border: 1px solid #28a745 !important;
        width: 100%;
        border-radius: 5px;
    }

    /* Navegação */
    .nav-header { 
        font-size: 0.7rem; color: #666 !important; 
        margin: 20px 0 10px 0; letter-spacing: 2px; font-weight: bold;
    }

    /* Divisores */
    hr { border-top: 1px solid #28a745 !important; opacity: 0.3; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def tela_acesso():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>🧪</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>LabSmartAI</h1>", unsafe_allow_html=True)
        st.subheader("Login Administrativo")
        email_input = st.text_input("E-mail Profissional", key="l_email")
        senha_input = st.text_input("Senha de Acesso", type="password", key="l_pass")
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            user = db.buscar_usuario_por_email(email_input)
            if user and db.verificar_senha(senha_input, user['password_hash']):
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else:
                st.error("Dados incorretos.")
        
        st.markdown("---")
        st.link_button("Cadastro Empresarial", "https://cadastro-de-empresas-e7bkusdk4tsdchmx89fh8c.streamlit.app/", use_container_width=True)

# --- FLUXO PRINCIPAL ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'selection' not in st.session_state:
    st.session_state.selection = "🏠 Dashboard"

if not st.session_state.logado:
    tela_acesso()
else:
    # IMPORTAÇÃO DOS MÓDULOS
    try:
        from substancias import show_substances
        from ControleEstoque import show_estoque
        from equipamentos import show_equipamentos
        from calculadora import show_calculadora
        from sistematabela import show_tabelas
        from graficos import show_graficos
        from config_empresa import show_config_empresa 
        import ia
        import relatorios
    except ImportError as e:
        st.error(f"Erro ao carregar módulos: {e}")

    user = st.session_state.user_data
    role = user.get('role', 'Visualizador')
    org_atual = user.get('org_name')
    
    # --- SIDEBAR CUSTOMIZADA ---
    with st.sidebar:
        # 1. Cartão Postal do Usuário
        # Usando um avatar padrão, mas você pode substituir user.get('avatar_url') se tiver no banco
        avatar_url = "https://api.dicebear.com/7.x/avataaars/svg?seed=" + user['username']
        
        st.markdown(f"""
            <div class="profile-card">
                <div class="org-label">ORGANIZAÇÃO</div>
                <div class="user-name" style="font-size: 1.3rem; margin-bottom:10px;">{org_atual}</div>
                <hr>
                <img src="{avatar_url}" class="profile-pic">
                <div class="user-name">{user['username']}</div>
                <span class="user-role">{role}</span>
            </div>
        """, unsafe_allow_html=True)

        # 2. Menu Suspenso (Três Pontos / Opções)
        with st.popover("⋮ Opções de Perfil"):
            st.markdown("### ⚙️ Configurações")
            if st.button("📝 Editar Perfil"):
                st.info("Funcionalidade de edição em breve.")
            if st.button("🔒 Alterar Senha"):
                st.info("Redirecionando para segurança...")
            st.divider()
            if st.button("🚪 SAIR DO SISTEMA", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.markdown("<div class='nav-header'>NAVEGAÇÃO</div>", unsafe_allow_html=True)
        
        abas = ["🏠 Dashboard", "🤖 IA & Visão", "🧪 Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
        if role in ["Tecnico", "ADM"]:
            abas.extend(["⚗️ Cadastro de Substâncias", "📦 Estoque"])
        if role == "ADM":
            abas.extend(["🛠️ Equipamentos", "👥 Gestão de Equipe", "📄 Relatórios"])

        selection = st.radio("Selecione a aba:", abas, label_visibility="collapsed")
        st.session_state.selection = selection

    # --- RENDERIZAÇÃO DE CONTEÚDO ---
    clean_selection = selection.split(" ", 1)[-1]

    if clean_selection == "Dashboard":
        st.title(f"🚀 Painel de Controle - {org_atual}")
        
        # Grid de Métricas (Mantido conforme seu original)
        try:
            res_sub = supabase.table("substancias").select("quantidade").eq("org_name", org_atual).execute()
            total_itens = sum([i['quantidade'] for i in res_sub.data]) if res_sub.data else 0
            res_eq = supabase.table("equipamentos").select("id", count="exact").eq("org_name", org_atual).execute()
            total_equip = res_eq.count if res_eq.count else 0
            total_analises = len(res_sub.data)
        except:
            total_itens, total_equip, total_analises = 0, 0, 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Itens no Estoque", total_itens)
        m2.metric("Equipamentos", total_equip)
        m3.metric("Registros Ativos", total_analises)
        m4.metric("Sessão", user['username'], role)

        st.markdown("---")
        st.subheader("Atalhos Rápidos")
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("🤖 Central de IA", use_container_width=True): 
                st.session_state.selection = "🤖 IA & Visão"; st.rerun()
        with c2: 
            if st.button("🧪 Tabelas Químicas", use_container_width=True): 
                st.session_state.selection = "🧪 Tabelas Químicas"; st.rerun()
        with c3: 
            if st.button("📦 Ver Estoque", use_container_width=True): 
                st.session_state.selection = "📦 Estoque"; st.rerun()

    # NAVEGAÇÃO DOS MÓDULOS
    elif clean_selection == "IA & Visão": ia.show_chatbot()
    elif clean_selection == "Tabelas Químicas": show_tabelas()
    elif clean_selection == "Calculadora Química": show_calculadora()
    elif clean_selection == "Gráficos": show_graficos()
    elif clean_selection == "Cadastro de Substâncias": show_substances()
    elif clean_selection == "Estoque": show_estoque()
    elif clean_selection == "Equipamentos": show_equipamentos()
    elif clean_selection == "Gestão de Equipe": show_config_empresa()
    elif clean_selection == "Relatórios": relatorios.show_reports(supabase)
