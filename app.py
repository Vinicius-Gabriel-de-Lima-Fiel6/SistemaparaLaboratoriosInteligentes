import streamlit as st
import auth_db as db

# ... (Configurações de página iniciais iguais) ...

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

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
                st.session_state.user_data = user # Guarda todos os dados (role, org, etc)
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

if not st.session_state.logado:
    tela_acesso()
else:
    user = st.session_state.user_data
    role = user['role']
    
    # --- Definição de Permissões (Suas Regras) ---
    abas = ["Dashboard", "Tabelas Químicas", "Calculadora Química", "Gráficos"]
    
    # Regra do Tecnico e ADM (Acesso a bancos de dados)
    if role in ["Tecnico", "ADM"]:
        abas.extend(["Estoque", "Cadastro de Substâncias"])
    
    # Regra do ADM (Acesso total + Painel de Controle + Equipamentos)
    if role == "ADM":
        abas.extend(["Equipamentos", "Painel de Controle", "Relatórios"])
    
    # Nota: O Visualizador só fica com a lista base (Cálculos, Tabelas, Gráficos)

    selection = st.sidebar.radio("Navegação", abas)
    
    # --- Lógica de Exibição das Abas ---
    if selection == "Dashboard":
        st.title(f"🚀 {user['org_name']}")
        st.subheader(f"Bem-vindo, {user['username']}")
        st.info(f"Nível de Acesso: **{role}**")

    elif selection == "Painel de Controle":
        # Apenas ADM chega aqui pelo menu
        url_tinkercad = "SEU_LINK_AQUI"
        st.components.v1.html(f"<script>window.open('{url_tinkercad}', '_blank');</script>", height=0)
        st.link_button("Abrir Tinkercad", url_tinkercad)

    # ... (Restante dos elifs chamando os módulos show_substances(), show_estoque(), etc) ...

    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()
