import streamlit as st
import os
import sys

# 1. Configuração de Caminho e Importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from substancias import show_substances
    from ControleEstoque import show_estoque
    from equipamentos import show_equipamentos
    from calculadora import show_calculadora
    from sistematabela import show_tabelas  # NOVA IMPORTAÇÃO
    from graficos import show_graficos
    import ia
    import relatorios
except ImportError as e:
    st.error(f"Erro de importação: Verifique se os arquivos .py estão na mesma pasta. Detalhe: {e}")

# --- Configuração da Página ---
st.set_page_config(
    page_title="LabSmartAI PRO", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Menu Lateral ---
st.sidebar.title("🧪 LabSmartAI")
st.sidebar.markdown("---")

# Lista de navegação completa
selection = st.sidebar.radio(
    "Navegação", 
    [
        "Dashboard", 
        "Cadastro de Substâncias", 
        "Estoque", 
        "Equipamentos",
        "Tabelas Químicas",    # ADICIONADO
        "Calculadora Química", 
        "Gráficos", 
        "IA", 
        "Relatórios"
    ]
)

# --- Lógica de Navegação ---

if selection == "Dashboard":
    st.title("🚀 Painel de Controle Laboratorial")
    st.write("Bem-vindo ao LabSmartAI. Seu ecossistema completo de gestão e consulta científica.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", "Online", "OK")
    col2.metric("Módulos", "9 Ativos") # Atualizado para 9
    col3.metric("Banco de Dados", "Conectado")
    col4.metric("Versão", "2.3")

    st.divider()
    st.info("💡 Dica: Na aba 'Tabelas Químicas', você pode consultar Kps e reatividade instantaneamente.")

elif selection == "Cadastro de Substâncias":
    show_substances()

elif selection == "Estoque":
    show_estoque()

elif selection == "Equipamentos":
    show_equipamentos()

elif selection == "Tabelas Químicas":
    # Chamada para o módulo de Tabela Periódica e Dados Químicos
    try:
        show_tabelas()
    except Exception as e:
        st.error(f"Erro ao carregar Tabelas: {e}")

elif selection == "Calculadora Química":
    show_calculadora()

elif selection == "Gráficos":
    show_graficos()

elif selection == "IA":
    if "ia_engine" not in st.session_state:
        with st.spinner("Iniciando IA..."):
            st.session_state.ia_engine = ia.LabSmartAI()
    ia.show_chatbot()

elif selection == "Relatórios":
    relatorios.show_reports()

# --- Rodapé ---
st.sidebar.markdown("---")
st.sidebar.caption("LabSmartAI Project - v2.3")
st.sidebar.caption("© 2026")