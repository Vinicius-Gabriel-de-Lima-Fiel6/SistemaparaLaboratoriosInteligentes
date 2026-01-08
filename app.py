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

# Gerenciamento de Estado de Login
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'usuario_atual' not in st.session_state:
    st.session_state.usuario_atual = None

# --- TELA DE ACESSO ---
def tela_acesso():
    st.title("🧪 LabSmartAI - Acesso ao Sistema")
    aba_login, aba_cadastro, aba_recuperar = st.tabs(["Entrar", "Criar Conta", "Recuperar Senha"])

    with aba_login:
        user_input = st.text_input("Usuário", key="l_user")
        senha_input = st.text_input("Senha", type="password", key="l_pass")
        
        if st.button("Fazer Login"):
            dados_usuario = db.buscar_usuario(user_input)
            
            if dados_usuario and db.verificar_senha(senha_input, dados_usuario['password_hash']):
                st.session_state.logado = True
                st.session_state.usuario_atual = user_input
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba_cadastro:
        new_user = st.text_input("Novo Usuário")
        new_email = st.text_input("E-mail")
        new_pass = st.text_input("Senha", type="password")
        
        if st.button("Cadastrar"):
            if new_user and new_pass and new_email:
                sucesso, mensagem = db.cadastrar_usuario(new_user, new_email, new_pass)
                if sucesso:
                    st.success(mensagem)
                    st.info("Agora você pode fazer login na aba 'Entrar'.")
                else:
                    st.error(mensagem)
            else:
                st.warning("Preencha todos os campos.")

# --- LÓGICA DE EXIBIÇÃO ---

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
        import ia
        import relatorios
    except ImportError as e:
        st.error(f"Erro de importação: {e}")

    # --- Menu Lateral ---
    st.sidebar.title("🧪 LabSmartAI")
    
    if st.sidebar.button("Sair/Logout"):
        st.session_state.logado = False
        st.rerun()
        
    st.sidebar.markdown("---")

    selection = st.sidebar.radio(
        "Navegação", 
        ["Dashboard", "IA & Visão", "Painel de Controle", "Cadastro de Substâncias", "Estoque", "Equipamentos", "Tabelas Químicas", "Calculadora Química", "Gráficos", "Relatórios"]
    )

    # --- Conteúdo Principal ---
    if selection == "Dashboard":
        st.title("🚀 Dashboard")
        st.info(f"Bem-vindo, {st.session_state.usuario_atual}!")

    elif selection == "IA & Visão":
        if "ia_engine" not in st.session_state:
            st.session_state.ia_engine = ia.LabSmartAI()
        ia.show_chatbot()

    elif selection == "Painel de Controle":
        # LINK DO TINKERCAD
        url_tinkercad = "https://www.tinkercad.com/dashboard" 
        
        st.title("📟 Redirecionando...")
        st.write("Se o Tinkercad não abrir automaticamente, clique no botão abaixo.")
        
        # Script para abrir o link automaticamente ao selecionar a aba
        st.components.v1.html(
            f"""
            <script>
                window.open('{url_tinkercad}', '_blank');
            </script>
            """,
            height=0,
        )
        
        # Botão de backup caso o pop-up seja bloqueado pelo navegador
        st.link_button("Abrir Tinkercad Manualmente", url_tinkercad, type="primary")

    elif selection == "Cadastro de Substâncias":
        show_substances()
    elif selection == "Estoque":
        show_estoque()
    elif selection == "Equipamentos":
        show_equipamentos()
    elif selection == "Tabelas Químicas":
        show_tabelas()
    elif selection == "Calculadora Química":
        show_calculadora()
    elif selection == "Gráficos":
        show_graficos()
    elif selection == "Relatórios":
        relatorios.show_reports()

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI Project - v3.0")
