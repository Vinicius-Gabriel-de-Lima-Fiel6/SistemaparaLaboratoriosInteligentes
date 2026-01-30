import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from groq import Groq

def show_tabelas():
    # Inicialização da IA com tratamento de erro
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        client = Groq(api_key=api_key) if api_key else None
    except Exception:
        client = None

    st.title("📚 Biblioteca Saraiva Digital 2026")
    
    # MENU SUSPENSO (BASE PRINCIPAL)
    setor = st.selectbox("Escolha a Base de Dados:", [
        "CIÊNCIAS QUÍMICAS (IUPAC/NIST/PUBCHEM)",
        "CIÊNCIAS MÉDICAS (ANVISA/ALPHAFOLD)",
        "AGENTE IA MULTIMODAL (ANÁLISE PROFISSIONAL)"
    ])

    st.divider()

    # --- LÓGICA DE SUBABAS (TABS) ---

    if setor == "CIÊNCIAS QUÍMICAS (IUPAC/NIST/PUBCHEM)":
        s1, s2, s3, s4 = st.tabs(["🔳 Tabela Periódica", "🔥 Termodinâmica", "💧 Solubilidade", "🧪 PubChem API"])
        
        with s1:
            st.write("### Matriz Atômica Interativa")
            st.write("")
            st.components.v1.iframe("https://ptable.com/?lang=pt#Properties", height=800, scrolling=True)
            
        with s2:
            st.write("### Constantes Termodinâmicas NIST")
            st.write("")
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=700)
            
        with s3:
            st.write("### Tabelas de Solubilidade")
            st.write("")
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=600) # Fallback para dados
            
        with s4:
            st.subheader("Busca PubChem")
            comp = st.text_input("Nome do composto (Inglês):", key="search_pubchem")
            if comp:
                res = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{comp}/JSON")
                if res.status_code == 200:
                    st.json(res.json()['PC_Compounds'][0])

    elif setor == "CIÊNCIAS MÉDICAS (ANVISA/ALPHAFOLD)":
        s1, s2, s3 = st.tabs(["📜 ANVISA (RDC 344)", "🧬 AlphaFold", "🏥 Enfermagem"])
        
        with s1:
            st.write("### Monitoramento Legislativo")
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)
            
        with s2:
            st.write("### Estruturas Proteicas 3D")
            st.write("

[Image of the structure of a protein molecule]
")
            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=700)
            
        with s3:
            st.write("### Protocolos Clínicos (PCDT)")
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

    elif setor == "AGENTE IA MULTIMODAL (ANÁLISE PROFISSIONAL)":
        m1, m2 = st.tabs(["💬 Consultoria Llama-3", "📸 Análise Visual/Voz"])
        
        with m1:
            prompt = st.text_area("Descreva o caso técnico:")
            if st.button("Executar IA") and client:
                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-70b-8192"
                )
                st.write(chat.choices[0].message.content)

        with m2:
            st.write("### Identificação de Reatividade")
            st.write("")
            st.file_uploader("Upload de arquivos para análise:", type=['png', 'jpg', 'pdf'])
