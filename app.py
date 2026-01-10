import streamlit as st
import os
import sys
import auth_db as db 

# --- 1. Configuração de Caminho e Importações ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Configuração da Página ---
st.set_page_config(
    page_title="LabSmartAI PRO", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Gerenciamento de Estado de Login ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- TELA DE ACESSO (Login / Cadastro) ---
def tela_acesso():
    st.title("🧪 LabSmartAI - Gestão Empresarial")
    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta Empresa"])

    with aba_login:
        email_input = st.text_input("E-mail Cadastrado", key="l_email")
        senha_input = st.text_input("Senha", type="password", key="l_pass")
        
        if st.button("Fazer Login"):
            user = db.buscar_usuario_por_email(email_input)
            if user and db.verificar_senha(senha_input, user['password_hash']):
                st.session_state.logado = True
                st.session_state.user_data = user
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")

    with aba_cadastro:
        st.info("O primeiro cadastro cria a Organização e define o Administrador (ADM).")
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Seu Nome Completo")
            new_email = st.text_input("E-mail Corporativo")
            new_pass = st.text_input("Senha", type="password")
        with col2:
            new_org = st.text_input("Nome da Empresa/Laboratório")
            st.warning("Cargo padrão: ADM")
        
        if st.button("Finalizar Cadastro"):
            if new_email and new_pass and new_org:
                sucesso, msg = db.cadastrar_usuario(new_name, new_email, new_pass, new_org, "ADM")
                if sucesso: st.success(msg)
                else: st.error(msg)

# --- 3. LÓGICA DE EXIBIÇÃO APÓS LOGIN ---

if not st.session_state.logado:
    tela_acesso()
else:
    # Importação dos módulos
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
    
    # --- 4. Construção do Menu Lateral (Sincronização de Nomes) ---
    abas = ["Dashboard", "IA & Visão", "Tabelas Químicas", "Calculadora Química", "Gráficos"]
    
    if role in ["Tecnico", "ADM"]:
        abas.append("Cadastro de Substâncias")
        abas.append("Estoque")
    
    if role == "ADM":
        abas.append("Equipamentos")
        abas.append("Gestão de Equipe")
        abas.append("Painel de Controle (Tinkercad)") # Nome exato para o link
        abas.append("Relatórios")

    st.sidebar.title(f"🧪 {user.get('org_name', 'Laboratório')}")
    st.sidebar.write(f"Usuário: **{user['username']}**")
    st.sidebar.write(f"Cargo: **{role}**")
    
    selection = st.sidebar.radio("Navegação", abas)
    
    if st.sidebar.button("Sair/Logout"):
        st.session_state.clear()
        st.rerun()

    # --- 5. Roteamento de Conteúdo ---
    if selection == "Dashboard":
        st.title(f"🚀 Dashboard - {user.get('org_name')}")
        st.info(f"Bem-vindo, {user['username']}!")

    elif selection == "IA & Visão":
        if "ia_engine" not in st.session_state:
            st.session_state.ia_engine = ia.LabSmartAI()
        ia.show_chatbot()

    elif selection == "Tabelas Químicas":
        show_tabelas()

    elif selection == "Calculadora Química":
        show_calculadora()

    elif selection == "Gráficos":
        show_graficos()

    elif selection == "Cadastro de Substâncias":
        show_substances()

    elif selection == "Estoque":
        show_estoque()

    elif selection == "Equipamentos":
        show_equipamentos()

    elif selection == "Gestão de Equipe":
        show_config_empresa()

    elif selection == "Painel de Controle (Tinkercad)":
        url_tinkercad = "https://www.tinkercad.com/things/1dHXe2Yoo33-sistemafisicolabia/editel"
        st.title("📟 Painel de Controle Físico")
        st.write("Acesse o simulador/controle de hardware externo abaixo:")
        st.link_button("Abrir Tinkercad", url_tinkercad, type="primary")

    elif selection == "Relatórios":
        relatorios.show_reports()

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI Project - v3.0")
