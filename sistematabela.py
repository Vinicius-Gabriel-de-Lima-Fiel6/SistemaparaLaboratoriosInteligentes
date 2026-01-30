import streamlit as st
import os

def show_tabelas():
    # Estilização para garantir que o Iframe ocupe a tela corretamente
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab"] { font-size: 18px; font-weight: bold; }
        iframe { border: 2px solid #444; border-radius: 10px; background-color: white; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📚 Biblioteca Técnica de Referência")

    # MENU DE SUBABAS
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔳 Tabela Periódica", 
        "🧪 PubChem (Química)", 
        "📜 ANVISA (RDC 344)", 
        "🏥 Protocolos Saúde"
    ])

    with tab1:
        st.subheader("Tabela Periódica Interativa CRQ-SP")
        st.write("Fonte: Conselho Regional de Química (IV Região)")
        
        # Integrando a tabela clicável específica solicitada
        st.components.v1.iframe("https://crqsp.org.br/tabelaperiodica/", height=900, scrolling=True)

    with tab2:
        st.subheader("Consulta de Substâncias - PubChem")
        st.write("Base de dados internacional para busca de compostos, toxicidade e reatividade.")
        

[Image of the structure of a protein molecule]

        # O PubChem é mais estável via link direto para evitar bloqueios de frame
        st.link_button("Abrir Busca PubChem (NIH)", "https://pubchem.ncbi.nlm.nih.gov/")
        st.info("Utilize para verificar Fichas de Segurança (FISPQ/MSDS).")

    with tab3:
        st.subheader("Legislação e Substâncias Controladas")
        st.write("Consulta direta ao Diário Oficial da União (DOU) sobre a RDC 344.")
        # Link focado na busca da portaria 344 para evitar erros de navegação
        st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)

    with tab4:
        st.subheader("Protocolos Clínicos (PCDT)")
        st.write("Diretrizes de tratamento e manejo de pacientes do Ministério da Saúde.")
        

[Image of the human digestive system]

        st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=700)

if __name__ == "__main__":
    show_tabelas()
