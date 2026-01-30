import streamlit as st
import os
import requests
from groq import Groq

def show_tabelas():
    # --- INICIALIZAÇÃO DO AGENTE IA ---
    client = None
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
    except Exception:
        pass

    st.title("🏛️ Central de Inteligência e Bases de Dados")

    # --- NÍVEL 1: SELEÇÃO DE DOMÍNIO (Menu Suspenso Principal) ---
    dominio = st.selectbox("🎯 SELECIONE O DOMÍNIO DE PESQUISA:", [
        "CIÊNCIAS QUÍMICAS E MATERIAIS",
        "SAÚDE, FARMACOLOGIA E REGULAÇÃO",
        "AGENTE DE ANÁLISE PREDITIVA (IA)"
    ])

    st.divider()

    # --- NÍVEL 2: DISTRIBUIÇÃO DE BASES ---

    if dominio == "CIÊNCIAS QUÍMICAS E MATERIAIS":
        sub_categoria = st.radio("Filtro Especializado:", ["Tabelas Periódicas", "Termodinâmica/NIST", "Segurança/PubChem"], horizontal=True)
        
        if sub_categoria == "Tabelas Periódicas":
            st.subheader("🔳 Tabela Periódica Interativa CRQ-SP")
            
            st.components.v1.iframe("https://crqsp.org.br/tabelaperiodica/", height=850, scrolling=True)
            
        elif sub_categoria == "Termodinâmica/NIST":
            st.subheader("🔥 Base de Dados NIST Chemistry WebBook")
            
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=700)
            
        elif sub_categoria == "Segurança/PubChem":
            st.subheader("🧪 Portal Global de Segurança Química")
            st.write("Acesso a FISPQ/MSDS e toxicidade.")
            st.link_button("Consultar PubChem (NIH)", "https://pubchem.ncbi.nlm.nih.gov/")

    elif dominio == "SAÚDE, FARMACOLOGIA E REGULAÇÃO":
        tab_med = st.tabs(["📜 ANVISA/RDC 344", "🧬 Genômica/AlphaFold", "🏥 Protocolos Clínicos"])
        
        with tab_med[0]:
            st.subheader("Monitoramento de Substâncias Controladas")
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)
            
        with tab_med[1]:
            st.subheader("Predição de Estruturas Proteicas")
            

[Image of the structure of a protein molecule]

            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=700)
            
        with tab_med[2]:
            st.subheader("Protocolos de Manejo e Diretrizes (MS)")
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=700)

    elif dominio == "AGENTE DE ANÁLISE PREDITIVA (IA)":
        st.subheader("🤖 Agente Llama-3 de Auditoria e Risco")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            pergunta = st.text_area("Descreva a situação clínica ou reação química para análise:", height=150, placeholder="Ex: Interação entre Cloreto de Potássio e Espironolactona em paciente renal...")
            if st.button("🔍 EXECUTAR ANÁLISE CRÍTICA"):
                if client and pergunta:
                    with st.spinner("Agente consultando bases científicas..."):
                        chat = client.chat.completions.create(
                            messages=[{"role": "user", "content": f"Aja como um especialista em toxicologia e farmacologia clínica. Analise: {pergunta}"}],
                            model="llama-3.3-70b-versatile"
                        )
                        st.markdown("### Parecer Técnico:")
                        st.write(chat.choices[0].message.content)
                else:
                    st.error("Erro: Agente Offline ou campo vazio.")
        
        with col2:
            st.info("🕒 **Status do Sistema:** Operacional")
            st.warning("⚠️ **Alerta:** Este agente auxilia a decisão, mas não substitui a validação profissional.")
            
            st.write("Utilize a série de reatividade para cruzamento manual de dados.")

if __name__ == "__main__":
    show_tabelas()

