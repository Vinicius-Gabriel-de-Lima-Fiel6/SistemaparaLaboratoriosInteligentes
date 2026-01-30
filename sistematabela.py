import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from groq import Groq

def show_tabelas():
    # 1. Configuração de Estilo e IA
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        client = Groq(api_key=api_key) if api_key else None
    except Exception:
        client = None

    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; color: #00d4ff; }
        .info-card { background: #131836; border: 1px solid #00d4ff; border-radius: 10px; padding: 15px; }
        iframe { border: 1px solid #ff006e; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧪 Central de Tabelas e Conhecimento")

    # 2. Menu Principal (Selectbox)
    setor = st.selectbox("Escolha o Domínio de Pesquisa:", [
        "BASE QUÍMICA (IUPAC/NIST/PUBCHEM)",
        "BASE MÉDICA E REGULATÓRIA (ANVISA/ALPHAFOLD)",
        "IA MULTIMODAL (ANÁLISE DE RISCO)"
    ])

    st.divider()

    # 3. Lógica de Subabas
    if setor == "BASE QUÍMICA (IUPAC/NIST/PUBCHEM)":
        s1, s2, s3, s4 = st.tabs(["🔳 Tabela Periódica", "🔥 Termodinâmica", "💧 Solubilidade", "🧪 PubChem API"])
        
        with s1:
            st.write("### Matriz Periódica Interativa")
            st.markdown("Consulte propriedades atômicas em tempo real.")
            
            st.components.v1.iframe("https://ptable.com/?lang=pt#Properties", height=800, scrolling=True)
            
        with s2:
            st.write("### Base de Dados NIST (Termofísica)")
            st.markdown("Cálculos de entalpia, entropia e estados gasosos.")
            
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=700)
            
        with s3:
            st.write("### Regras de Solubilidade Universal")
            st.markdown("Previsão de precipitação em soluções aquosas.")
            
            st.info("Utilize para verificar compatibilidade de fármacos e reagentes.")
            
        with s4:
            st.subheader("Consulta PubChem (NIH)")
            comp = st.text_input("Nome da Substância (Inglês):", key="chem_search")
            if comp:
                try:
                    res = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{comp}/JSON")
                    if res.status_code == 200:
                        st.json(res.json()['PC_Compounds'][0])
                    else:
                        st.error("Composto não encontrado na base PubChem.")
                except:
                    st.error("Erro na conexão com o servidor NIH.")

    elif setor == "BASE MÉDICA E REGULATÓRIA (ANVISA/ALPHAFOLD)":
        s1, s2, s3 = st.tabs(["📜 ANVISA (RDC 344)", "🧬 Bioquímica/Proteínas", "🏥 Protocolos"])
        
        with s1:
            st.write("### Monitoramento de Substâncias Controladas")
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)
            
        with s2:
            st.write("### Modelagem AlphaFold (DeepMind)")
            st.markdown("Visualização de estruturas proteicas e dobramentos.")
            

[Image of the structure of a protein molecule]

            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=700)
            
        with s3:
            st.write("### Protocolos Clínicos e Diretrizes Terapêuticas")
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

    elif setor == "IA MULTIMODAL (ANÁLISE DE RISCO)":
        m1, m2 = st.tabs(["💬 Consultoria Técnica IA", "📸 Visão e Segurança"])
        
        with m1:
            st.write("### Assistente Llama-3 (Groq)")
            prompt = st.text_area("Descreva a dúvida técnica ou cruzamento de dados:")
            if st.button("Analisar") and client:
                with st.spinner("Processando..."):
                    chat = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-70b-8192"
                    )
                    st.markdown(chat.choices[0].message.content)

        with m2:
            st.write("### Reconhecimento de Riscos Químicos")
            st.markdown("Série de Reatividade para Metais:")
            
            st.file_uploader("Suba a imagem de rótulos, exames ou diagramas para análise:", type=['png', 'jpg', 'pdf'])
            st.info("A IA identificará perigos e incompatibilidades visuais.")
