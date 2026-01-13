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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background-color: #0E1117;
        color: #E0E6ED;
    }

    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }

    h1, h2, h3, p {
        font-family: 'Inter', sans-serif;
        color: #FFFFFF !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background: linear-gradient(135deg, #00B4DB 0%, #0083B0 100%);
        color: white;
        border: none;
        padding: 0.6rem;
        font-weight: 700;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(0, 180, 219, 0.5);
        transform: scale(1.02);
        color: white;
    }

    .stTextInput>div>div>input {
        background-color: #0D1117;
        color: white;
        border: 1px solid #30363D;
        border-radius: 8px;
    }

    div[data-testid="stExpander"], div.stAlert {
        background-color: #1C2128;
        border: 1px solid #30363D;
        border-radius: 12px;
        color: white;
    }

    .user-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #00B4DB;
        margin-bottom: 20px;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0E1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363D;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

def tela_acesso():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("")
        st.markdown("<h1 style='text-align: center; font-size: 3rem;'>🧪</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; margin-top:-20px;'>LabSmartAI <span style='color:#00B4DB'>PRO</span></h1>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div style="background-color: #161B22; padding: 40px; border-radius: 20px; border: 1px solid #30363D; box-shadow: 0 20px 40px rgba(0,0,0,0.4);">', unsafe_allow_html=True)
            
            st.subheader("Login do Sistema")
            email_input = st.text_input("E-mail", key="l_email", placeholder="Digite seu e-mail...")
            senha_input = st.text_input("Senha", type="password", key="l_pass", placeholder="••••••••")
            
            if st.button("Entrar"):
                user = db.buscar_usuario_por_email(email_input)
                if user and db.verificar_senha(senha_input, user['password_hash']):
                    st.session_state.logado = True
                    st.session_state.user_data = user
                    st.success("Acesso autorizado!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8B949E; margin-top: 20px;'>v1.0 • Laboratório de Alta Precisão</p>", unsafe_allow_html=True)

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
        st.error(f"Erro de módulo: {e}")

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
            <small style="color: #00B4DB; font-weight: bold;">{user.get('org_name', 'LAB')}</small><br>
            <span style="font-size: 1.1rem; font-weight: 600;">{user['username']}</span><br>
            <span style="color: #8B949E; font-size: 0.8rem;">{role}</span>
        </div>
    """, unsafe_allow_html=True)
    
    selection = st.sidebar.radio("MENU DE OPERAÇÕES", abas)
    
    st.sidebar.markdown("<br>"*5, unsafe_allow_html=True)
    if st.sidebar.button("LOGOUT"):
        st.session_state.clear()
        st.rerun()

    clean_selection = selection.split(" ", 1)[-1]

    if clean_selection == "Dashboard":
        st.title(f"🚀 Status do {user.get('org_name')}")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.info(f"Monitoramento ativo para: **{user['username']}**")
        with col_m2:
            st.success(f"Sistema Operacional | Nível de Acesso: {role}")

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
        st.title("📟 Interface de Hardware")
        st.link_button("Abrir Simulador Tinkercad", "https://www.tinkercad.com/things/1dHXe2Yoo33-sistemafisicolabia/editel")

    elif clean_selection == "Relatórios":
        relatorios.show_reports()

    st.sidebar.caption("LabSmartAI PRO © 2024")
