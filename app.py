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

# --- CSS GLOBAL (Mantendo sua estrutura de cores com a separação solicitada) ---
st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; color: #212529; }
        [data-testid="stSidebar"] { background-color: #000000 !important; color: #ffffff !important; }
        
        /* 1. SEPARAÇÃO: Texto das abas e labels em BRANCO */
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span { 
            color: #ffffff !important; 
        }
        
        /* 2. SEPARAÇÃO: Texto dos botões da sidebar em PRETO */
        [data-testid="stSidebar"] .stButton button {
            background-color: #28a745 !important;
            color: #000000 !important;
        }

        /* Estilo do Cartão Postal conforme sua imagem */
        .user-card {
            background: #111;
            border: 1px solid #28a745;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            margin-bottom: 10px;
        }
        .profile-img {
            width: 75px; height: 75px;
            border-radius: 50%;
            border: 2px solid #28a745;
            margin: 10px auto;
            object-fit: cover;
        }
        
        /* Botão de 3 pontos (Popover) */
        div[data-testid="stPopover"] > button {
            background-color: transparent !important;
            border: 1px solid #333 !important;
            color: #28a745 !important;
            width: 100%;
        }

        hr { border-top: 2px solid #28a745 !important; }
        </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def tela_acesso():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("")
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>🧪</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>LabSmartAI</h1>", unsafe_allow_html=True)
        
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
        st.markdown("<p style='text-align: center; color: var(--text-gray);'>Se não tiver uma conta, clique abaixo:</p>", unsafe_allow_html=True)
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
    # IMPORTAÇÃO DOS MÓDULOS (Original)
    try:
        from substancias import show_substances
        from ControleEstoque import show_estoque
        from equipamentos import show_equipamentos
        from calculadora import show_calculadora
        from sistematabela import show_tabelas
        from graficos import show_graficos
        from config_empresa import show_config_empresa 
        import ia
        from configurações import show_configuracoes
        import relatorios
    except ImportError as e:
        st.error(f"Erro ao carregar módulos: {e}")

    user = st.session_state.user_data
    role = user.get('role', 'Visualizador')
    org_atual = user.get('org_name')
    
    # --- SIDEBAR (Mantendo sua estrutura exata) ---
    with st.sidebar:
        # Seu User Card transformado em "Postal"
        st.markdown(f"""
            <div class="user-card">
                <small style="font-weight: 800; font-size: 0.7rem; color: #28a745;">ORGANIZAÇÃO</small><br>
                <span style="font-size: 1rem; font-weight: 700;">{org_atual}</span><br>
                <hr>
                <img src="https://api.dicebear.com/7.x/avataaars/svg?seed={user['username']}" class="profile-img">
                <div style="margin-top: 5px;">
                    <span style="font-size: 0.9rem;">{user['username']}</span><br>
                    <span style="background: #28a745; color: green; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px;">{role}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # O Menu de 3 Pontos (Popover)
        with st.popover("⋮ Opções"):
            st.write("👤 Perfil do Usuário")
            
            if st.button("⚙️ Configurações Gerais", use_container_width=True):
                st.session_state.selection = "Configurações"
                st.rerun()
            st.divider()
            if st.button("SAIR", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.write("") 
        
        # Sua lógica de abas original
        abas = ["🏠 Dashboard", "🤖 IA & Visão", "🧪 Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
        if role in ["Tecnico", "ADM"]:
            abas.extend(["⚗️ Cadastro de Substâncias", "📦 Estoque"])
        if role == "ADM":
            abas.extend(["🛠️ Equipamentos", "👥 Gestão de Equipe", "📄 Relatórios"])

        selection = st.radio("NAVEGAÇÃO", abas, index=abas.index(st.session_state.selection) if st.session_state.selection in abas else 0)
        st.session_state.selection = selection

    clean_selection = selection.split(" ", 1)[-1]

    # DASHBOARD (Lógica original de métricas)
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

        limite_alerta = 100 
        cor_estoque = "inverse" if total_itens < limite_alerta else "normal"
        delta_label = f"-{limite_alerta - total_itens} un. (Crítico)" if total_itens < limite_alerta else "Estoque Operacional"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Itens no Estoque", f"{total_itens:,}".replace(",", "."), delta=delta_label, delta_color=cor_estoque)
        m2.metric("Equipamentos", total_equip, "Ativos")
        m3.metric("Registros Ativos", total_analises, "Banco de Dados")
        m4.metric("Usuário Atual", user['username'], f"Acesso {role}")

        st.markdown("---")
        st.subheader("Atalhos do Sistema")
        
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

    # NAVEGAÇÃO DOS MÓDULOS (Chamadas originais preservadas)
    elif clean_selection == "IA & Visão": ia.show_chatbot()
    elif clean_selection == "Tabelas Químicas": show_tabelas()
    elif clean_selection == "Calculadora Química": show_calculadora()
    elif clean_selection == "Gráficos": show_graficos()
    elif clean_selection == "Cadastro de Substâncias": show_substances()
    elif clean_selection == "Estoque": show_estoque()
    elif clean_selection == "Equipamentos": show_equipamentos()
    elif clean_selection == "Gestão de Equipe": show_config_empresa()
    elif clean_selection == "Relatórios": relatorios.show_reports(supabase)

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI • v1.0")

