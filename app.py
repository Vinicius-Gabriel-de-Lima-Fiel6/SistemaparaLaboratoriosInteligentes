import streamlit as st
import os
import sys
import auth_db as db 

# Adiciona o caminho ao sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="LabSmartAI PRO", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
    <style>
    /* Importação de fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Estilização da Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }

    /* Estilização de Botões */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #0066cc;
        color: white;
        border: none;
        transition: all 0.3s ease;
        font-weight: 600;
    }
    
    .stButton>button:hover {
        background-color: #0052a3;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }

    /* Cards e Inputs */
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    
    /* Customização de Títulos */
    h1 {
        color: #1e293b;
        font-weight: 700 !important;
        letter-spacing: -1px;
    }
    
    /* Estilo para o Badge de Usuário */
    .user-badge {
        padding: 10px;
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- TELA DE ACESSO ---
def tela_acesso():
    # Centralização visual usando colunas
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.write("") # Espaçamento
        st.write("")
        st.markdown("<h1 style='text-align: center;'>🧪 LabSmartAI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Laboratório Inteligente & Gestão PRO</p>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div style="background-color: #ffffff; padding: 30px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
            
            st.subheader("Entrar no Sistema")
            email_input = st.text_input("E-mail Cadastrado", key="l_email", placeholder="exemplo@lab.com")
            senha_input = st.text_input("Senha", type="password", key="l_pass", placeholder="••••••••")
            
            if st.button("Acessar Painel"):
                user = db.buscar_usuario_por_email(email_input)
                if user and db.verificar_senha(senha_input, user['password_hash']):
                    st.session_state.logado = True
                    st.session_state.user_data = user
                    st.success("Autenticado com sucesso!")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.write("")
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #94a3b8;'>Novo por aqui? Realize o cadastro no nosso portal externo.</p>", unsafe_allow_html=True)

# --- LÓGICA DE EXIBIÇÃO APÓS LOGIN ---
if not st.session_state.logado:
    tela_acesso()
else:
    # Importações (Mantidas conforme seu original)
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
    
    # Navegação Profissional
    abas = ["🏠 Dashboard", "🤖 IA & Visão", "🧪 Tabelas Químicas", "🧮 Calculadora Química", "📊 Gráficos"]
    
    if role in ["Tecnico", "ADM"]:
        abas.append("⚗️ Cadastro de Substâncias")
        abas.append("📦 Estoque")
    
    if role == "ADM":
        abas.append("🛠️ Equipamentos")
        abas.append("👥 Gestão de Equipe")
        abas.append("📟 Painel Tinkercad")
        abas.append("📄 Relatórios")

    # Sidebar Estilizada
    st.sidebar.markdown(f"""
        <div class='user-badge'>
            <small style='color: #64748b;'>Organização</small><br>
            <strong>{user.get('org_name', 'Laboratório')}</strong><br><br>
            <small style='color: #64748b;'>Usuário</small><br>
            <strong>{user['username']}</strong><br>
            <span style='font-size: 0.7rem; background: #e2e8f0; padding: 2px 6px; border-radius: 4px;'>{role}</span>
        </div>
    """, unsafe_allow_html=True)
    
    selection = st.sidebar.radio("Navegação Principal", abas)
    
    st.sidebar.write("")
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.clear()
        st.rerun()

    
    
    clean_selection = selection.split(" ", 1)[-1] 

    if clean_selection == "Dashboard":
        st.title(f"🚀 Dashboard - {user.get('org_name')}")
        st.info(f"Bem-vindo de volta, {user['username']}! Aqui está o resumo do laboratório.")

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
        url_tinkercad = "https://www.tinkercad.com/things/1dHXe2Yoo33-sistemafisicolabia/editel"
        st.title("📟 Painel de Controle Físico")
        st.link_button("Abrir Tinkercad", url_tinkercad, type="primary")

    elif clean_selection == "Relatórios":
        relatorios.show_reports()

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI Project - v1.0")
