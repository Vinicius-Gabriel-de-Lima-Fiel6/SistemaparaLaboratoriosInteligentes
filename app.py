import streamlit as st
import os
import sys
import auth_db as db 

# 1. Configuração de Caminho e Importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Configuração da Página ---
st.set_page_config(
    page_title="LabSmartAI PRO", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Gerenciamento de Estado de Login ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- TELA DE ACESSO ---
def tela_acesso():
    st.title("🧪 LabSmartAI - Gestão Empresarial")
    aba_login, aba_cadastro, aba_recuperar = st.tabs(["Entrar", "Criar Conta Empresa", "Recuperar Senha"])

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
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Seu Nome Completo")
            new_email = st.text_input("E-mail Corporativo")
            new_pass = st.text_input("Senha", type="password")
        with col2:
            new_org = st.text_input("Nome da Empresa/Laboratório")
            new_role = st.selectbox("Seu Cargo", ["Visualizador", "Tecnico", "ADM"])
        
        if st.button("Finalizar Cadastro"):
            if new_email and new_pass and new_org:
                sucesso, msg = db.cadastrar_usuario(new_name, new_email, new_pass, new_org, new_role)
                if sucesso: st.success(msg)
                else: st.error(msg)

    with aba_recuperar:
        st.subheader("Recuperação de Senha")
        email_rec = st.text_input("E-mail cadastrado", key="rec_email")
        nova_senha = st.text_input("Nova Senha", type="password", key="rec_pass")
        confirmar_senha = st.text_input("Confirme a Nova Senha", type="password", key="rec_pass_conf")
        
        if st.button("Redefinir Senha"):
            if nova_senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            else:
                sucesso, msg = db.redefinir_senha(email_rec, nova_senha)
                if sucesso: st.success(msg)
                else: st.error(msg)

# --- LÓGICA DE EXIBIÇÃO ---

if not st.session_state.logado:
    tela_acesso()
else:
    # Importação dos módulos (Coloquei dentro do IF para evitar erros antes do login)
    try:
        from substancias import show_substances
        from ControleEstoque import show_estoque
        from equipamentos import show_equipamentos
        from calculadora import show_calculadora
        from sistematabela import show_tabelas
        from graficos import show_graficos
        import ia
        import relatorios
    except ImportError as e:
        st.error(f"Erro ao carregar módulos: {e}")

    user = st.session_state.user_data
    role = user['role']
    
    # 1. Definir as abas que aparecerão no Menu Lateral
    # IMPORTANTE: Os nomes aqui devem ser IDÊNTICOS aos dos blocos IF abaixo
    abas = ["Dashboard", "IA & Visão", "Tabelas Químicas", "Calculadora Química", "Gráficos"]
    
    if role in ["Tecnico", "ADM"]:
        abas.append("Cadastro de Substâncias")
        abas.append("Estoque")
    
    if role == "ADM":
        abas.append("Equipamentos")
        abas.append("Painel de Controle")
        abas.append("Relatórios")

    # 2. Criar o Menu Lateral
    st.sidebar.title(f"🧪 {user['org_name']}")
    st.sidebar.write(f"Usuário: **{user['username']}**")
    st.sidebar.write(f"Cargo: **{role}**")
    
    selection = st.sidebar.radio("Navegação", abas)
    
    if st.sidebar.button("Sair/Logout"):
        st.session_state.logado = False
        st.session_state.user_data = None
        st.rerun()

    # 3. Lógica de Redirecionamento (Onde o conteúdo aparece)
    if selection == "Dashboard":
        st.title(f"🚀 Dashboard - {user['org_name']}")
        st.info(f"Bem-vindo, {user['username']}! Use o menu lateral para navegar.")

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

    elif selection == "Painel de Controle":
        url_tinkercad = "https://www.tinkercad.com/things/1dHXe2Yoo33-sistemafisicolabia/editel"
        st.title("📟 Redirecionando...")
        st.components.v1.html(f"<script>window.open('{url_tinkercad}', '_blank');</script>", height=0)
        st.link_button("Abrir Tinkercad Manualmente", url_tinkercad, type="primary")

    elif selection == "Relatórios":
        relatorios.show_reports()

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI Project - v3.0")
