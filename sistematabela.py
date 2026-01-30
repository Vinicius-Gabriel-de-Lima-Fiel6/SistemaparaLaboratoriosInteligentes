import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from groq import Groq

def show_tabelas():
    # Inicialização do Cliente Groq (Llama-3)
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    except:
        st.error("Erro: Chave GROQ_API_KEY não configurada no ambiente.")
        return

    st.title("📚 Biblioteca Saraiva Digital 2026")
    
    # 1. MENU SUSPENSO (ABAS PRINCIPAIS)
    setor = st.selectbox("Selecione a Área de Conhecimento:", [
        "CIÊNCIAS QUÍMICAS",
        "CIÊNCIAS MÉDICAS",
        "AGENTE IA MULTIMODAL"
    ])

    st.divider()

    # 2. LÓGICA DE SUBABAS
    if setor == "CIÊNCIAS QUÍMICAS":
        s1, s2, s3 = st.tabs(["🔳 Tabela Periódica", "🔥 Termodinâmica", "💧 Solubilidade"])
        
        with s1:
            st.markdown("### Matriz Atômica IUPAC")
            # A tag de imagem deve ser passada como string no markdown
            st.markdown("")
            st.components.v1.iframe("https://ptable.com/?lang=pt#Properties", height=850, scrolling=True)
            
        with s2:
            st.markdown("### Constantes de Energia (NIST)")
            st.markdown("")
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=600)
            
        with s3:
            st.markdown("### Tabelas de Solubilidade Química")
            st.markdown("")
            st.info("Consulte para evitar precipitação em misturas intravenosas.")

    elif setor == "CIÊNCIAS MÉDICAS":
        s1, s2, s3 = st.tabs(["📜 ANVISA (RDC 344)", "🧬 AlphaFold", "🏥 Enfermagem"])
        
        with s1:
            st.markdown("### Monitoramento do Diário Oficial - Substâncias Controladas")
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)
            
        with s2:
            st.markdown("### Predição de Estruturas Proteínas")
            st.markdown("

[Image of the structure of a protein molecule]
")
            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=700)
            
        with s3:
            st.markdown("### Protocolos Clínicos e Diretrizes (MS)")
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

    elif setor == "AGENTE IA MULTIMODAL":
        m1, m2 = st.tabs(["💬 Consulta Llama-3", "📸 Análise Visual/Voz"])
        
        with m1:
            pergunta = st.text_area("Dúvida técnica (Farmácia/Enfermagem):")
            if st.button("🔍 Consultar Groq"):
                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": pergunta}],
                    model="llama3-70b-8192"
                )
                st.write(chat.choices[0].message.content)

        with m2:
            st.markdown("### Análise de Reatividade e Pictogramas")
            st.markdown("")
            st.file_uploader("Upload de foto do rótulo ou laudo:", type=['png', 'jpg', 'pdf'])
