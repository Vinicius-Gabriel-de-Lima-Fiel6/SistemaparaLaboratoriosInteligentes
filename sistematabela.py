import streamlit as st

def show_tabelas():
    st.title("📚 Biblioteca Técnica de Referência")

    # MENU DE SUBABAS (Tabs nativas do Streamlit)
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔳 Tabela Periódica", 
        "🧪 PubChem (Química)", 
        "📜 ANVISA (RDC 344)", 
        "🏥 Protocolos Saúde"
    ])

    with tab1:
        st.subheader("Tabela Periódica Interativa CRQ-SP")
        # Iframe da CRQ-SP: Clicável e oficial
        st.components.v1.iframe("https://crqsp.org.br/tabelaperiodica/", height=900, scrolling=True)

    with tab2:
        st.subheader("Consulta de Substâncias - PubChem")
        st.write("Base internacional para busca de compostos, toxicidade e reatividade.")
        # Link botão para evitar bloqueio de segurança do site do NIH
        st.link_button("Abrir Portal PubChem (NIH)", "https://pubchem.ncbi.nlm.nih.gov/")

    with tab3:
        st.subheader("Legislação e Substâncias Controladas")
        st.write("Consulta direta ao Diário Oficial da União (DOU).")
        st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)

    with tab4:
        st.subheader("Protocolos Clínicos (PCDT)")
        st.write("Diretrizes de tratamento oficiais do Ministério da Saúde.")
        st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

if __name__ == "__main__":
    show_tabelas()
