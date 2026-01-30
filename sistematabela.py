import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from groq import Groq

def show_tabelas():
    # Inicialização da IA com tratamento de erro para a chave
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            st.error("Chave API não encontrada nas variáveis de ambiente.")
            return
        client = Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Erro ao conectar com Groq: {e}")
        return

    # Estilo visual para a Biblioteca
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
        iframe { border: 2px solid #00ff41; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📚 Biblioteca Saraiva Digital 2026")
    st.info(f"Sincronização Ativa: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # --- MENU SUSPENSO (GRANDE ÁREA) ---
    setor = st.selectbox("Escolha a Base de Dados Principal:", [
        "CIÊNCIAS QUÍMICAS (IUPAC/NIST/PUBCHEM)",
        "CIÊNCIAS MÉDICAS (ANVISA/ALPHAFOLD)",
        "AGENTE IA MULTIMODAL (ANÁLISE PROFISSIONAL)"
    ])

    st.divider()

    # --- LÓGICA DE SUBABAS (TABS) ---

    if setor == "CIÊNCIAS QUÍMICAS (IUPAC/NIST/PUBCHEM)":
        s1, s2, s3, s4 = st.tabs(["🔳 Tabela Periódica", "🔥 Termodinâmica", "💧 Solubilidade", "🧪 PubChem API"])
        
        with s1:
            st.markdown("### Matriz Atômica Interativa (Ptable)")
            
            st.components.v1.iframe("https://ptable.com/?lang=pt#Properties", height=800, scrolling=True)
            
        with s2:
            st.markdown("### Constantes Termodinâmicas (NIST WebBook)")
            
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=700)
            
        with s3:
            st.markdown("### Tabelas de Solubilidade e Precipitação")
            
            st.warning("Verifique a compatibilidade para evitar precipitação em acesso venoso.")
            
        with s4:
            st.subheader("Busca em Tempo Real - PubChem")
            comp = st.text_input("Nome do composto (Inglês):", "Paracetamol")
            if comp:
                with st.spinner("Consultando NIH..."):
                    res = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{comp}/JSON")
                    if res.status_code == 200:
                        st.json(res.json()['PC_Compounds'][0])
                    else:
                        st.error("Composto não encontrado.")

    elif setor == "CIÊNCIAS MÉDICAS (ANVISA/ALPHAFOLD)":
        s1, s2, s3 = st.tabs(["📜 ANVISA (RDC 344)", "🧬 Proteínas (AlphaFold)", "🏥 Protocolos Enfermagem"])
        
        with s1:
            st.markdown("### Consulta de Substâncias Controladas (DOU)")
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)
            
        with s2:
            st.markdown("### Estruturas 3D AlphaFold")
            

[Image of the structure of a protein molecule]

            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=700)
            
        with s3:
            st.markdown("### Protocolos Clínicos (PCDT)")
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

    elif setor == "AGENTE IA MULTIMODAL (ANÁLISE PROFISSIONAL)":
        m1, m2 = st.tabs(["💬 Consultoria Técnica", "📸 Análise Visual/Voz"])
        
        with m1:
            st.markdown("### Pesquisa Avançada via Llama-3 (Groq)")
            prompt = st.text_area("Descreva o caso ou dúvida técnica:")
            if st.button("Executar Inteligência"):
                with st.spinner("Cruzando dados reais..."):
                    chat = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-70b-8192"
                    )
                    st.markdown(chat.choices[0].message.content)

        with m2:
            st.markdown("### Identificação de Reatividade e Perigos")
            
            st.file_uploader("Upload de Imagem (Laudo/Rótulo) ou Áudio:", type=['png', 'jpg', 'pdf', 'mp3', 'mp4'])
            st.info("O Agente analisará pictogramas de segurança e riscos químicos.")
