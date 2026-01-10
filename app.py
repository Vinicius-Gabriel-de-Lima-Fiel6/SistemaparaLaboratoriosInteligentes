import streamlit as st
import os
import sys
import auth_db as db 
from config_empresa import show_config_empresa  # Novo arquivo que criaremos

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
        st.info("O primeiro cadastro será automaticamente o Administrador da empresa.")
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Seu Nome Completo")
            new_email = st.text_input("E-mail Corporativo")
            new_pass = st.text_input("Senha", type="password")
        with col2:
            new_org = st.text_input("Nome da Empresa/Laboratório")
            # Forçamos o primeiro usuário a ser ADM para automação
            st.warning("Cargo padrão: ADM")
        
        if st.button("Finalizar Cadastro da Empresa"):
            if new_email and new_pass and new_org:
                # O sistema gera o org_id automático aqui no auth_db
                sucesso, msg = db.cadastrar_usuario(new_name, new_email, new_pass, new_org, "ADM")
                if sucesso: st.success(msg)
                else: st.error(msg)

# --- LÓGICA DE EXIBIÇÃO PÓS-LOGIN ---

if not st.session_state.logado:
    tela_acesso()
else:
    # Carregamento dinâmico de módulos
    from substancias import show_substances
    from ControleEstoque import show_estoque
    from equipamentos import show_equipamentos
    from calculadora import show_calculadora
    from graficos import show_graficos
    import relatorios

    user = st.session_state.user_data
    role = user['role']
    
    # 1. Menu Lateral Dinâmico (Estilo GitHub/Permissões)
    abas = ["Dashboard", "Calculadora Química", "Gráficos"]
    
    if role in ["Tecnico", "ADM"]:
        abas.extend(["Cadastro de Substâncias", "Estoque"])
    
    if role == "ADM":
        abas.extend(["Equipamentos", "Gestão de Equipe", "Relatórios"])

    st.sidebar.title(f"🧪 {user.get('org_name', 'Laboratório')}")
    st.sidebar.write(f"**{user['username']}** | `{role}`")
    
    selection = st.sidebar.radio("Navegação", abas)
    
    if st.sidebar.button("Sair/Logout"):
        st.session_state.clear()
        st.rerun()

    # 2. Roteamento de Conteúdo
    if selection == "Dashboard":
        st.title(f"🚀 Painel Geral - {user.get('org_name')}")
        st.write(f"Bem-vindo ao sistema de gestão, {user['username']}.")

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

    elif selection == "Relatórios":
        relatorios.show_reports()
