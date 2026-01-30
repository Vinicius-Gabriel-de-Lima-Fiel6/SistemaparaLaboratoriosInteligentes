import streamlit as st
import os
from groq import Groq

def show_tabelas():
    # Inicialização segura da IA Groq
    client = None
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
    except Exception:
        pass

    st.title("🏛️ Central de Inteligência e Bases de Dados")

    # --- ORGANIZAÇÃO EM NÍVEIS ---
    # O Selectbox permite escala infinita de tabelas sem poluir a UI
    categoria = st.selectbox("📂 ESCOLHA A ÁREA TÉCNICA:", [
        "QUÍMICA: Tabelas e Termodinâmica",
        "SAÚDE: Regulação e Farmacologia",
        "IA: Agente de Consultoria e Risco"
    ])

    st.divider()

    # --- ÁREA QUÍMICA ---
    if categoria == "QUÍMICA: Tabelas e Termodinâmica":
        sub = st.radio("Base de Dados:", ["CRQ-SP (Clicável)", "NIST (Termofísica)", "PubChem (Segurança)"], horizontal=True)
        
        if sub == "CRQ-SP (Clicável)":
            st.markdown("### Tabela Periódica Interativa")
            # Tabela solicitada: funciona como ferramenta de clique
            st.components.v1.iframe("https://crqsp.org.br/tabelaperiodica/", height=900, scrolling=True)
            
        elif sub == "NIST (Termofísica)":
            st.markdown("### NIST Chemistry WebBook")
            st.write("Referência para constantes físicas e reações.")
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=700)
            
        elif sub == "PubChem (Segurança)":
            st.markdown("### Portal PubChem (NIH)")
            st.write("Base para MSDS, Toxicidade e Fórmulas.")
            st.link_button("Acessar Base Internacional PubChem", "https://pubchem.ncbi.nlm.nih.gov/")

    # --- ÁREA DA SAÚDE ---
    elif categoria == "SAÚDE: Regulação e Farmacologia":
        tab1, tab2, tab3 = st.tabs(["📜 ANVISA (RDC 344)", "🧬 Bioquímica (AlphaFold)", "🏥 Protocolos MS"])
        
        with tab1:
            st.markdown("### Monitoramento Legislativo (DOU)")
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)
            
        with tab2:
            st.markdown("### Predição Estrutural AlphaFold")
            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=700)
            
        with tab3:
            st.markdown("### Protocolos Clínicos e Diretrizes")
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

    # --- AGENTE IA ---
    elif categoria == "IA: Agente de Consultoria e Risco":
        st.markdown("### 🤖 Agente Llama-3 (Expert em Farmacologia)")
        
        pergunta = st.text_area("Descreva a dúvida técnica ou cruzamento de dados:", placeholder="Ex: Riscos da mistura de hipoclorito com amônia...")
        
        if st.button("EXECUTAR CONSULTA IA"):
            if client and pergunta:
                with st.spinner("Analisando bases científicas..."):
                    chat = client.chat.completions.create(
                        messages=[{"role": "user", "content": f"Aja como um consultor técnico sênior em química e farmácia. Analise com rigor: {pergunta}"}],
                        model="llama3-70b-8192"
                    )
                    st.markdown("---")
                    st.markdown("#### Parecer do Agente:")
                    st.write(chat.choices[0].message.content)
            else:
                st.warning("IA indisponível ou pergunta vazia.")

if __name__ == "__main__":
    show_tabelas()
