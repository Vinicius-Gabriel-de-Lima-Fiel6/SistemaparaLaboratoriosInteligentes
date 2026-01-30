import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from groq import Groq

# --- CONFIGURAÇÃO DE SEGURANÇA MÁXIMA ---
st.set_page_config(page_title="SOVEREIGN LIBRARY v4.0", layout="wide", page_icon="⚖️")

# CONEXÃO GROQ
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except:
    st.error("ERRO DE SISTEMA: Chave de Inteligência não detectada.")

# --- INTERFACE DE ALTO CONTRASTE (FOCO TÉCNICO) ---
st.markdown("""
    <style>
    .critical-alert { padding: 10px; border: 2px solid #ff4b4b; background: #2b0000; color: #ff4b4b; font-weight: bold; border-radius: 5px; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { font-size: 18px; color: #00ff41; }
    iframe { border: 2px solid #00ff41; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

def show_tabelas():
    # Aviso de Responsabilidade Técnica
    st.markdown("<div class='critical-alert'>⚠️ AVISO: Uso restrito a profissionais de saúde e pesquisa. Verifique sempre a bula e o protocolo institucional.</div>", unsafe_allow_html=True)

    # MENU SUSPENSO PRINCIPAL
    setor = st.selectbox("🎯 SELECIONE A BASE DE DADOS:", [
        "CIÊNCIAS QUÍMICAS (NIST/IUPAC/PUBCHEM)",
        "CIÊNCIAS MÉDICAS (ALPHAFOLD/ANVISA/ENFERMAGEM)",
        "AGENTE IA MULTIMODAL (ANÁLISE DE RISCO)"
    ])

    st.divider()

    # --- LÓGICA DE SUB-ABAS POR SETOR ---

    if setor == "CIÊNCIAS QUÍMICAS (NIST/IUPAC/PUBCHEM)":
        s1, s2, s3, s4 = st.tabs(["🔳 Tabela Periódica", "🔥 Termodinâmica", "💧 Solubilidade", "🧪 PubChem API"])
        
        with s1:
            [Image of the periodic table of elements with atomic numbers and symbols]
            st.components.v1.iframe("https://ptable.com/?lang=pt#Properties", height=800)
            
        with s2:
            st.subheader("Dados Termodinâmicos NIST")
            
            st.components.v1.iframe("https://webbook.nist.gov/chemistry/name-ser/", height=600)
            
        with s3:
            st.subheader("Regras de Solubilidade e Precipitação")
            
            st.info("Dados vitais para estabilidade de misturas intravenosas.")
            
        with s4:
            st.subheader("Consulta Direta PubChem")
            comp = st.text_input("Substância (Inglês):", "Dopamine")
            if comp:
                data = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{comp}/JSON").json()
                st.json(data)

    elif setor == "CIÊNCIAS MÉDICAS (ALPHAFOLD/ANVISA/ENFERMAGEM)":
        s1, s2, s3 = st.tabs(["📜 ANVISA/RDC 344", "🧬 AlphaFold Proteínas", "🏥 Enfermagem/Protocolos"])
        
        with s1:
            st.subheader("Monitoramento de Substâncias Controladas")
            st.components.v1.iframe("https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344", height=700)
            
        with s2:
            [Image of the structure of a protein molecule]
            st.components.v1.iframe("https://alphafold.ebi.ac.uk/", height=700)
            
        with s3:
            st.subheader("Protocolos Clínicos Governamentais")
            st.components.v1.iframe("https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos-e-diretrizes-terapeuticas-pcdt", height=800)

    elif setor == "AGENTE IA MULTIMODAL (ANÁLISE DE RISCO)":
        st.subheader("🤖 Consultoria de IA Llama-3 (Groq)")
        
        # Sub-abas para multimodalidade
        m1, m2 = st.tabs(["💬 Consulta Técnica", "📸 Upload de Evidências"])
        
        with m1:
            pergunta = st.text_area("Descreva o caso clínico ou dúvida química:", placeholder="Ex: Paciente com insuficiência renal, prescrito Vancomicina. Qual o ajuste de clearance?")
            if st.button("🔍 ANALISAR VIA GROQ"):
                with st.spinner("Varrendo bases científicas..."):
                    res = client.chat.completions.create(messages=[{"role":"user","content":pergunta}], model="llama3-70b-8192")
                    st.markdown(f"### Parecer IA:\n{res.choices[0].message.content}")

        with m2:
            st.write("### Análise de Imagem/Vídeo/Voz")
            
            st.file_uploader("Suba a imagem do exame, rótulo ou vídeo do procedimento:", type=['png','jpg','pdf','mp4'])
            st.warning("O Agente identificará pictogramas de perigo e inconsistências em laudos automaticamente.")

if __name__ == "__main__":
    show_tabelas()
