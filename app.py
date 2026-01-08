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

    with aba_recuperar:
        st.subheader("Recuperação de Acesso")
        email_rec = st.text_input("Digite o e-mail cadastrado")
        if st.button("Recuperar"):
            st.info("Se este e-mail existir na base, você receberá instruções em breve.")

# --- LÓGICA DE EXIBIÇÃO ---

if not st.session_state.logado:
    tela_acesso()
else:
    # SE ESTIVER LOGADO, CARREGA O RESTANTE DO SISTEMA
    try:
        from substancias import show_substances
        from ControleEstoque import show_estoque
        from equipamentos import show_equipamentos
        from calculadora import show_calculadora
        from sistematabela import show_tabelas
        from graficos import show_graficos
        import ia
        import relatorios
        import PainelControle  # Importando seu novo módulo
    except ImportError as e:
        st.error(f"Erro de importação de módulos: {e}")

    # --- Menu Lateral ---
    st.sidebar.title("🧪 LabSmartAI")
    st.sidebar.write(f"Conectado como: **{st.session_state.usuario_atual}**")
    
    if st.sidebar.button("Sair/Logout"):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.rerun()
        
    st.sidebar.markdown("---")

    selection = st.sidebar.radio(
        "Navegação", 
        ["Dashboard", "Cadastro de Substâncias", "Estoque", "Equipamentos", "Tabelas Químicas", "Calculadora Química", "Gráficos", "IA", "Relatórios","Painel de Controle"]
    )

    # --- Conteúdo Principal ---
    if selection == "Dashboard":
        st.title("🚀 Painel de Controle Laboratorial")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Status", "Nuvem (Supabase)")
        col2.metric("Módulos", "10 Ativos")
        col3.metric("Usuário", st.session_state.usuario_atual)
        col4.metric("Versão", "1.0")
        st.divider()
        st.info(f"Olá {st.session_state.usuario_atual}, seus dados estão protegidos no banco de dados em nuvem.")

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
    elif selection == "IA":
        if "ia_engine" not in st.session_state:
            st.session_state.ia_engine = ia.LabSmartAI()
        ia.show_chatbot()
    elif selection == "Relatórios":
        relatorios.show_reports()
    elif selection == "Painel de Controle":
        # CHAMA A FUNÇÃO QUE CRIA A INTERFACE DO ARDUINO
        PainelControle.renderizar_painel()

    st.sidebar.markdown("---")
    st.sidebar.caption("LabSmartAI Project - v3.0 © 2026")
