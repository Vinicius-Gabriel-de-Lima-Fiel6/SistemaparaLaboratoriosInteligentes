import streamlit as st
import os
import sys
import auth_db as db 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="LabSmartAI PRO", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background-color: #F1F3F6;
        color: #1A202C;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #D1D5DB;
    }

    h1, h2, h3, p, span, label {
        font-family: 'Inter', sans-serif;
        color: #1A202C !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1E3A8A;
        color: #FFFFFF !important;
        border: none;
        padding: 0.6rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background-color: #2563EB;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stTextInput>div>div>input {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 10px;
    }

    /* Remove fundos automáticos de blocos verticais que causam o 'quadrado branco' */
    [data-testid="stVerticalBlock"] > div {
        background-color: transparent !important;
    }

    .user-card {
        background: #F8FAFC;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }

    .login-container {
        max-width: 450px;
        margin: 0 auto;
        padding: 40px;
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

def tela_acesso():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Tudo inserido dentro de um único container para evitar gaps
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>🧪 LabSmartAI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B !important; margin-bottom: 30px;'>Acesse o painel de controle do laboratório</p>", unsafe_allow_html=True)
        
        email_input = st.text_input("E-mail", key="l_email", placeholder="seu@email.com")
        senha_input = st.text_input("Senha", type="password", key="l_pass", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ENTRAR NO SISTEMA"):
            user = db.buscar_usuario_por_email(email_input)
            if user and db.verificar_senha(senha_input, user['password_hash']):
                st.session_state.logado = True
                st.session_state.user_data = user
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.logado:
    tela_acesso()
else:
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
    
    abas = ["🏠 Dashboard", "🤖 IA & Visão", "🧪 Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
    if role in ["Tecnico", "ADM"]:
        abas.append("⚗️ Cadastro de Substâncias")
        abas.append("📦 Estoque")
    if role == "ADM":
        abas.append("🛠️ Equipamentos")
        abas.append("👥 Gestão de Equipe")
        abas.append("📟 Painel Tinkercad")
        abas.append("📄 Relatórios")

    st.sidebar.markdown(f"""
        <div class="user-card">
            <small style="color: #64748B; font-weight: 700; font-size: 0.65rem; text-transform: uppercase;">Organização</small><br>
            <strong style="color: #1E3A8A;">{user.get('org_name', 'LAB')}</strong><br>
            <hr style="margin: 8px 0; border: 0; border-top: 1px solid #E2E8F0;">
            <small style="color: #1A202C; font-weight: 600;">{user['username']}</small><br>
            <span style="color: #64748B; font-size: 0.75rem;">{role}</span>
        </div>
    """, unsafe_allow_html=True)
    
    selection = st.sidebar.radio("NAVEGAÇÃO", abas)
    
    st.sidebar.markdown("<br>"*2, unsafe_allow_html=True)
    if st.sidebar.button("LOGOUT"):
        st.session_state.clear()
        st.rerun()

    clean_selection = selection.split(" ", 1)[-1]

    if clean_selection == "Dashboard":
        st.title(f"🚀 Dashboard")
        st.info(f"Olá, {user['username']}! Bem-vindo ao sistema da {user.get('org_name')}.")

    elif clean_selection == "IA & Visão":
        if "ia_engine" not in st.session_state:
            st.session_state.ia_engine = ia.LabSmartAI()
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

    elif clean_selection == "Painel Tinkercad":
        st.title("📟 Interface Tinkercad")
        st.link_button("Abrir Projeto Externo", "https://www.tinkercad.com/things/1dHXe2Yoo33-sistemafisicolabia/editel")

    elif clean_selection == "Relatórios":
        relatorios.show_reports()

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI PRO v1.0")
