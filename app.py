import streamlit as st
import os
import sys
import auth_db as db 
from supabase import create_client


sys.path.append(os.path.dirname(os.path.abspath(__file__)))


st.set_page_config(
    page_title="LabSmartAI", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
    <style>
    /* 1. VARIÁVEIS DE CORES - PALETA ESMERALDA PROFISSIONAL */
    :root {
        --bg-black: #000000;
        --bg-card: #0d1117;
        --emerald-primary: #10b981; /* Verde Esmeralda vibrante mas elegante */
        --emerald-dark: #065f46;
        --emerald-light: #34d399;
        --text-white: #ffffff;
        --text-gray: #9ca3af;
        --border-color: #30363d;
    }

    /* 2. FUNDO E GERAL */
    .stApp {
        background-color: var(--bg-black) !important;
        color: var(--text-white);
    }

    /* 3. SIDEBAR (PRETO TOTAL) */
    [data-testid="stSidebar"] {
        background-color: var(--bg-black) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    /* 4. BOTÕES (VERDE ESMERALDA) */
    div.stButton > button {
        width: 100%;
        background-color: var(--emerald-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button:hover {
        background-color: var(--emerald-light) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* 5. EXPANDERS (Aquele do Marketplace) */
    .streamlit-expanderHeader {
        background-color: var(--bg-card) !important;
        color: var(--text-white) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }

    .streamlit-expanderContent {
        background-color: var(--bg-black) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
    }

    /* 6. CARDS DE USUÁRIO E MÉTRICAS */
    .user-card, div[data-testid="metric-container"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }

    /* Títulos e Valores das Métricas */
    div[data-testid="stMetricLabel"] > div {
        color: var(--text-gray) !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: var(--emerald-primary) !important;
        font-weight: 700;
    }

    /* 7. INPUTS (TEXTO E SENHA) */
    .stTextInput input {
        background-color: var(--bg-black) !important;
        color: white !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
    }

    .stTextInput input:focus {
        border-color: var(--emerald-primary) !important;
    }

    /* 8. CABEÇALHOS */
    h1, h2, h3 {
        color: var(--text-white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* Ajuste para o link button (Cadastro) */
    div.stLinkButton > a {
        background-color: transparent !important;
        color: var(--text-gray) !important;
        border: 1px solid var(--border-color) !important;
        transition: 0.3s;
    }
    
    div.stLinkButton > a:hover {
        border-color: var(--emerald-primary) !important;
        color: var(--emerald-primary) !important;
    }
    </style>
    """, unsafe_allow_html=True)


if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'selection' not in st.session_state:
    st.session_state.selection = "🏠 Dashboard"

# --- CONEXÃO SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def tela_acesso():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("")
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>🧪</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #2D3748 !important;'>LabSmartAI</h1>", unsafe_allow_html=True)
        
        st.subheader("Login Administrativo")
        email_input = st.text_input("E-mail Profissional", key="l_email")
        senha_input = st.text_input("Senha de Acesso", type="password", key="l_pass")
        
        if st.button("ACESSAR SISTEMA"):
            user = db.buscar_usuario_por_email(email_input)
            if user and db.verificar_senha(senha_input, user['password_hash']):
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else:
                st.error("Dados incorretos.")
        
     
        st.markdown("---")
        st.markdown("<p style='text-align: center; color: #4A5568 !important;'>Se não tiver uma conta, clique abaixo:</p>", unsafe_allow_html=True)
        
        # Altere o link "https://seulink.com" conforme sua necessidade
        st.link_button("Cadastro Empresarial","https://cadastro-de-empresas-e7bkusdk4tsdchmx89fh8c.streamlit.app/", use_container_width=True)

if not st.session_state.logado:
    tela_acesso()
else:
    # --- IMPORTAÇÃO DOS MÓDULOS ---
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
    
    # --- SIDEBAR E NAVEGAÇÃO ---
    st.sidebar.markdown(f"""
        <div class="user-card">
            <small style="font-weight: 800; font-size: 0.7rem;">ORGANIZAÇÃO</small><br>
            <span style="font-size: 1rem; font-weight: 700;">{org_atual}</span><br>
            <div style="margin-top: 10px; border-top: 1px solid #CBD5E0; padding-top: 5px;">
                <span style="font-size: 0.9rem;">{user['username']}</span><br>
                <span style="background: #000000; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px;">{role}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    abas = ["🏠 Dashboard", "🤖 IA & Visão", "🧪 Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
    if role in ["Tecnico", "ADM"]:
        abas.extend(["⚗️ Cadastro de Substâncias", "📦 Estoque"])
    if role == "ADM":
        abas.extend(["🛠️ Equipamentos", "👥 Gestão de Equipe", "📄 Relatórios"])

    selection = st.sidebar.radio("NAVEGAÇÃO", abas, index=abas.index(st.session_state.selection) if st.session_state.selection in abas else 0)
    st.session_state.selection = selection

    if st.sidebar.button("SAIR"):
        st.session_state.clear()
        st.rerun()

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

        # --- LÓGICA DE COR PARA ESTOQUE BAIXO ---
        limite_alerta = 100 
        if total_itens < limite_alerta:
            cor_estoque = "inverse" # Vermelho no Streamlit para deltas negativos
            delta_label = f"-{limite_alerta - total_itens} un. (Crítico)"
        else:
            cor_estoque = "normal" # Verde/Padrão
            delta_label = "Estoque Operacional"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Itens no Estoque", f"{total_itens:,}".replace(",", "."), delta=delta_label, delta_color=cor_estoque)
        m2.metric("Equipamentos", total_equip, "Ativos")
        m3.metric("Registros Ativos", total_analises, "Banco de Dados")
        m4.metric("Usuário Atual", user['username'], f"Acesso {role}")

        st.markdown("---")
        st.subheader("Atalhos do Sistema")
        
        # Linha 1 de Atalhos
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🤖 Central de IA"):
                st.session_state.selection = "🤖 IA & Visão"; st.rerun()
        with c2:
            if st.button("🧪 Tabelas e Reagentes"):
                st.session_state.selection = "🧪 Tabelas Químicas"; st.rerun()
        with c3:
            if st.button("🧮 Calculadora de Soluções"):
                st.session_state.selection = "🧮 Calculadora Química"; st.rerun()

       
        c4, c5, c6 = st.columns(3)
        with c4:
            if st.button("📊 Painel de Gráficos"):
                st.session_state.selection = "📊 Gráficos"; st.rerun()
        with c5:
            if role in ["Tecnico", "ADM"]:
                if st.button("📦 Gestão de Estoque"):
                    st.session_state.selection = "📦 Estoque"; st.rerun()
        with c6:
            if role == "ADM":
                if st.button("📄 Gerador de Relatórios"):
                    st.session_state.selection = "📄 Relatórios"; st.rerun()

    # --- NAVEGAÇÃO PARA OUTROS MÓDULOS ---
    elif clean_selection == "IA & Visão":
        ia.show_chatbot()
    elif clean_selection == "Tabelas Químicas":
        show_tabelas()
    elif clean_selection == "Calculadora Química":
        show_calculadora()
    elif clean_selection == "Gráficos":
        show_graficos()
    elif clean_selection == "Cadastro de Substâncias":
        show_substances()
    elif clean_selection == "Estoque":
        show_estoque()
    elif clean_selection == "Equipamentos":
        show_equipamentos()
    elif clean_selection == "Gestão de Equipe":
        show_config_empresa()
    elif clean_selection == "Relatórios":
        relatorios.show_reports(supabase)

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI • v1.0")












