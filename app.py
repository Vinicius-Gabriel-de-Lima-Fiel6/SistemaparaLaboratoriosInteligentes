import streamlit as st
import os
import sys
import auth_db as db 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="LabSmartAI", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background-color: #E2E8F0;
        color: #1A202C;
    }

    [data-testid="stSidebar"] {
        background-color: #CBD5E0;
        border-right: 2px solid #A0AEC0;
    }

    h1, h2, h3, p, span, label {
        font-family: 'Inter', sans-serif;
        color: #1A202C !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #FFFFFF;
        color: #1A202C;
        border: 1px solid #A0AEC0;
        padding: 0.5rem;
        font-weight: 700;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background-color: #EDF2F7;
        border-color: #718096;
        transform: translateY(-1px);
    }

    .stTextInput>div>div>input {
        background-color: #FFFFFF;
        color: #1A202C;
        border: 1px solid #A0AEC0;
        border-radius: 6px;
    }

    div[data-testid="stExpander"], div.stAlert {
        background-color: #F7FAFC;
        border: 1px solid #A0AEC0;
        border-radius: 10px;
    }

    .user-card {
        background: #F7FAFC;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #A0AEC0;
        margin-bottom: 20px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    }

    [data-testid="stSidebarNav"] {
        background-color: transparent;
    }
    
    .stRadio [data-testid="stWidgetLabel"] p {
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

def tela_acesso():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("")
        st.write("")
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom:0;'>🧪</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; margin-top:0; color: #2D3748 !important;'>LabSmartAI PRO</h1>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div style="background-color: #F7FAFC; padding: 35px; border-radius: 15px; border: 1px solid #A0AEC0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
            
            st.subheader("Login Administrativo")
            email_input = st.text_input("E-mail Profissional", key="l_email", placeholder="nome@empresa.com")
            senha_input = st.text_input("Senha de Acesso", type="password", key="l_pass", placeholder="••••••••")
            
            if st.button("ACESSAR SISTEMA"):
                user = db.buscar_usuario_por_email(email_input)
                if user and db.verificar_senha(senha_input, user['password_hash']):
                    st.session_state.logado = True
                    st.session_state.user_data = user
                    st.success("Login confirmado.")
                    st.rerun()
                else:
                    st.error("Dados incorretos.")
            
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
        st.error(f"Erro de carregamento: {e}")

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
            <small style="color: #4A5568; text-transform: uppercase; font-weight: 800; font-size: 0.7rem;">Organização</small><br>
            <span style="font-size: 1rem; font-weight: 700; color: #2D3748;">{user.get('org_name', 'LAB')}</span><br>
            <div style="margin-top: 10px; border-top: 1px solid #CBD5E0; padding-top: 5px;">
                <span style="font-size: 0.9rem; color: #1A202C;">{user['username']}</span><br>
                <span style="background: #E2E8F0; color: #4A5568; font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; font-weight: bold;">{role}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    selection = st.sidebar.radio("NAVEGAÇÃO", abas)
    
    st.sidebar.markdown("<br>"*3, unsafe_allow_html=True)
    if st.sidebar.button("SAIR"):
        st.session_state.clear()
        st.rerun()

    clean_selection = selection.split(" ", 1)[-1]

    if clean_selection == "Dashboard":
        st.title(f"🚀 Painel de Controle - {user.get('org_name')}")
        st.markdown(f"**Status:** Conectado como {user['username']}")

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
        st.title("📟 Controle Externo")
        st.link_button("Acessar Hardware Virtual", "https://www.tinkercad.com/things/1dHXe2Yoo33-sistemafisicolabia/editel")

    elif clean_selection == "Relatórios":
        relatorios.show_reports()

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI • v1.0")
