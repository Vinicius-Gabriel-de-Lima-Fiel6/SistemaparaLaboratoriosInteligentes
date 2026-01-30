import streamlit as st
import os
from groq import Groq

def show_tabelas():
    # Inicialização do Agente IA
    client = None
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
    except Exception:
        pass

    st.title("🏛️ Hub de Inteligência Científica")
    st.markdown("---")

    # --- NÍVEL 1: NAVEGAÇÃO POR SISTEMA (Menu Lateral ou Superior) ---
    with st.sidebar:
        st.header("📂 Navegação")
        sistema = st.radio(
            "Selecione o Sistema:",
            ["Dashboard Inicial", "Química Fundamental", "Saúde e Regulação", "Agente Consultor"]
        )

    # --- LÓGICA DE RENDERIZAÇÃO ESTRUTURADA ---

    if sistema == "Dashboard Inicial":
        st.subheader("Bem-vindo à Central de Bases de Dados")
        st.info("Selecione um sistema no menu lateral para carregar as ferramentas de análise.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("🧪 **Sistemas Químicos:** Tabela Periódica, NIST, PubChem.")
        with c2:
            st.write("🏥 **Sistemas de Saúde:** ANVISA, AlphaFold, Protocolos MS.")

    elif sistema == "Química Fundamental":
        st.subheader("🧪 Sistemas de Análise Química")
        
        # Menu Suspenso de Ferramentas
        ferramenta = st.selectbox("Escolha a Base de Dados:", [
            "Tabela Periódica Interativa (CRQ-SP)",
            "Termodinâmica e Reatividade (NIST)",
            "Propriedades de Compostos (PubChem)"
        ])

        if "CRQ-SP" in ferramenta:
            st.markdown("#### Matriz Atômica Clicável")
            
            st.components.v1.iframe("https://crqsp.org.br/tabelaperiodica/", height=900, scrolling=True)
            
        elif "NIST" in ferramenta:
            st.markdown("#### Constantes Termodinâmicas")
            
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=800)
            
        elif "PubChem" in ferramenta:
            st.markdown("#### Base de Dados PubChem")
            st.write("Acesso a estruturas e toxicologia.")
            st.link_button("🚀 Abrir PubChem em Nova Aba", "https://pubchem.ncbi.nlm.nih.gov/")

    elif sistema == "Saúde e Regulação":
        st.subheader("🏥 Sistemas de Saúde e Normativas")
        
        base_saude = st.selectbox("Selecione a Base:", [
            "Monitor Legislativo (ANVISA RDC 344)",
            "Biologia Estrutural (AlphaFold)",
            "Diretrizes Terapêuticas (PCDT)"
        ])

        if "ANVISA" in base_saude:
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=800)
        
        elif "AlphaFold" in base_saude:
            st.markdown("#### Modelagem de Proteínas")
            

[Image of the structure of a protein molecule]

            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=800)
            
        elif "PCDT" in base_saude:
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

    elif sistema == "Agente Consultor":
        st.subheader("🤖 Agente Llama-3: Auditoria e Risco")
        
        pergunta = st.text_area("Descreva o caso técnico para análise profunda:", placeholder="Ex: Avaliação de risco em descarte de efluentes com alta concentração de metais pesados...")
        
        if st.button("🔍 Executar Parecer Técnico"):
            if client and pergunta:
                with st.spinner("Analisando bases..."):
                    chat = client.chat.completions.create(
                        messages=[{"role": "user", "content": f"Aja como um doutor em química e farmacologia. Forneça uma análise técnica e segura: {pergunta}"}],
                        model="llama3-70b-8192"
                    )
                    st.success("Análise Concluída")
                    st.markdown(chat.choices[0].message.content)
            else:
                st.warning("IA não configurada ou pergunta ausente.")

if __name__ == "__main__":
    show_tabelas()
