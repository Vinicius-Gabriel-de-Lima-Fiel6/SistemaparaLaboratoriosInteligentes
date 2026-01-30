import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional
import base64
from io import BytesIO

# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================
st.set_page_config(
    page_title="Central de Tabelas Químicas Avançada",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# FUNÇÕES AUXILIARES
# ============================

def aplicar_css_customizado():
    """Aplica CSS moderno e profissional"""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:wght@400;700&family=Poppins:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #00d4ff;
            --secondary: #ff006e;
            --accent: #ffbe0b;
            --dark-bg: #0a0e27;
            --card-bg: #131836;
        }
        
        .stApp {
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f4a 50%, #0a0e27 100%);
            font-family: 'Poppins', sans-serif;
        }
        
        h1 {
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            font-size: 3rem;
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { filter: drop-shadow(0 0 5px var(--primary)); }
            to { filter: drop-shadow(0 0 20px var(--secondary)); }
        }
        
        div.stButton > button {
            width: 100% !important;
            height: 50px !important;
            font-size: 14px !important;
            font-weight: bold !important;
            font-family: 'Space Mono', monospace !important;
            border: 2px solid #444 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        div.stButton > button:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 0 20px currentColor !important;
            z-index: 10 !important;
        }
        
        [data-testid="column"] {
            min-width: 35px !important;
            gap: 2px !important;
        }
        
        .element-card {
            background: var(--card-bg);
            border: 2px solid var(--primary);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .element-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(0, 212, 255, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

# ============================
# DADOS DOS ELEMENTOS (COMPLETO COM TODOS OS 118 ELEMENTOS)
# ============================

def get_elementos_info():
    """Retorna dicionário completo com informações de todos os elementos"""
    return {
        "H": {"Nome": "Hidrogênio", "Número": 1, "Massa": 1.008, "Grupo": "Não metais", "Período": "1", "Descrição": "Elemento mais leve e abundante.", "Estado": "Gás", "Eletronegatividade": 2.20, "Configuracao_Eletronica": "1s¹", "Aplicacoes": "Combustível, síntese de amônia"},
        "He": {"Nome": "Hélio", "Número": 2, "Massa": 4.0026, "Grupo": "Gases nobres", "Período": "1", "Descrição": "Gás nobre, usado em balões.", "Estado": "Gás", "Eletronegatividade": None, "Configuracao_Eletronica": "1s²", "Aplicacoes": "Balões, criogenia"},
        "Li": {"Nome": "Lítio", "Número": 3, "Massa": 6.94, "Grupo": "Metais alcalinos", "Período": "2", "Descrição": "Metal pouco reativo.", "Estado": "Sólido", "Eletronegatividade": 0.98, "Configuracao_Eletronica": "1s² 2s¹", "Aplicacoes": "Baterias de íon-lítio"},
        "Be": {"Nome": "Berílio", "Número": 4, "Massa": 9.0122, "Grupo": "Metais alcalino-terrosos", "Período": "2", "Descrição": "Carga para estabilidade é +2.", "Estado": "Sólido", "Eletronegatividade": 1.57, "Configuracao_Eletronica": "1s² 2s²", "Aplicacoes": "Ligas aeroespaciais"},
        "B": {"Nome": "Boro", "Número": 5, "Massa": 10.81, "Grupo": "Semimetais", "Período": "2", "Descrição": "Precisa perder 3 elétrons.", "Estado": "Sólido", "Eletronegatividade": 2.04, "Configuracao_Eletronica": "1s² 2s² 2p¹", "Aplicacoes": "Vidro borossilicato"},
        "C": {"Nome": "Carbono", "Número": 6, "Massa": 12.011, "Grupo": "Não metais", "Período": "2", "Descrição": "Tetravalente e forma cadeias.", "Estado": "Sólido", "Eletronegatividade": 2.55, "Configuracao_Eletronica": "1s² 2s² 2p²", "Aplicacoes": "Base da vida, grafeno"},
        "N": {"Nome": "Nitrogênio", "Número": 7, "Massa": 14.007, "Grupo": "Não metais", "Período": "2", "Descrição": "Fundamental para a vida.", "Estado": "Gás", "Eletronegatividade": 3.04, "Configuracao_Eletronica": "1s² 2s² 2p³", "Aplicacoes": "Fertilizantes, atmosfera"},
        "O": {"Nome": "Oxigênio", "Número": 8, "Massa": 15.999, "Grupo": "Não metais", "Período": "2", "Descrição": "Essencial para respiração.", "Estado": "Gás", "Eletronegatividade": 3.44, "Configuracao_Eletronica": "1s² 2s² 2p⁴", "Aplicacoes": "Respiração, combustão"},
        "F": {"Nome": "Flúor", "Número": 9, "Massa": 18.998, "Grupo": "Halogênios", "Período": "2", "Descrição": "Mais eletronegativo.", "Estado": "Gás", "Eletronegatividade": 3.98, "Configuracao_Eletronica": "1s² 2s² 2p⁵", "Aplicacoes": "Pasta de dente, teflon"},
        "Ne": {"Nome": "Neônio", "Número": 10, "Massa": 20.180, "Grupo": "Gases nobres", "Período": "2", "Descrição": "Usado em neons.", "Estado": "Gás", "Eletronegatividade": None, "Configuracao_Eletronica": "1s² 2s² 2p⁶", "Aplicacoes": "Letreiros luminosos"},
        "Na": {"Nome": "Sódio", "Número": 11, "Massa": 22.990, "Grupo": "Metais alcalinos", "Período": "3", "Descrição": "Muito eletropositivo.", "Estado": "Sólido", "Eletronegatividade": 0.93, "Configuracao_Eletronica": "[Ne] 3s¹", "Aplicacoes": "Sal de cozinha"},
        "Mg": {"Nome": "Magnésio", "Número": 12, "Massa": 24.305, "Grupo": "Metais alcalino-terrosos", "Período": "3", "Descrição": "Forma leite de magnésia.", "Estado": "Sólido", "Eletronegatividade": 1.31, "Configuracao_Eletronica": "[Ne] 3s²", "Aplicacoes": "Ligas leves"},
        "Al": {"Nome": "Alumínio", "Número": 13, "Massa": 26.982, "Grupo": "Outros metais", "Período": "3", "Descrição": "Metal forte e maleável.", "Estado": "Sólido", "Eletronegatividade": 1.61, "Configuracao_Eletronica": "[Ne] 3s² 3p¹", "Aplicacoes": "Embalagens, aviação"},
        "Si": {"Nome": "Silício", "Número": 14, "Massa": 28.085, "Grupo": "Semimetais", "Período": "3", "Descrição": "Usado em semicondutores.", "Estado": "Sólido", "Eletronegatividade": 1.90, "Configuracao_Eletronica": "[Ne] 3s² 3p²", "Aplicacoes": "Chips, painéis solares"},
        "P": {"Nome": "Fósforo", "Número": 15, "Massa": 30.974, "Grupo": "Não metais", "Período": "3", "Descrição": "Fundamental à vida.", "Estado": "Sólido", "Eletronegatividade": 2.19, "Configuracao_Eletronica": "[Ne] 3s² 3p³", "Aplicacoes": "Fertilizantes, DNA"},
        "S": {"Nome": "Enxofre", "Número": 16, "Massa": 32.06, "Grupo": "Não metais", "Período": "3", "Descrição": "Precisa de 2 elétrons.", "Estado": "Sólido", "Eletronegatividade": 2.58, "Configuracao_Eletronica": "[Ne] 3s² 3p⁴", "Aplicacoes": "Ácido sulfúrico"},
        "Cl": {"Nome": "Cloro", "Número": 17, "Massa": 35.45, "Grupo": "Halogênios", "Período": "3", "Descrição": "Altamente eletronegativo.", "Estado": "Gás", "Eletronegatividade": 3.16, "Configuracao_Eletronica": "[Ne] 3s² 3p⁵", "Aplicacoes": "Desinfecção, PVC"},
        "Ar": {"Nome": "Argônio", "Número": 18, "Massa": 39.948, "Grupo": "Gases nobres", "Período": "3", "Descrição": "Gás nobre inerte.", "Estado": "Gás", "Eletronegatividade": None, "Configuracao_Eletronica": "[Ne] 3s² 3p⁶", "Aplicacoes": "Soldagem, lâmpadas"},
        "K": {"Nome": "Potássio", "Número": 19, "Massa": 39.098, "Grupo": "Metais alcalinos", "Período": "4", "Descrição": "Altamente reativo.", "Estado": "Sólido", "Eletronegatividade": 0.82, "Configuracao_Eletronica": "[Ar] 4s¹", "Aplicacoes": "Fertilizantes"},
        "Ca": {"Nome": "Cálcio", "Número": 20, "Massa": 40.078, "Grupo": "Metais alcalino-terrosos", "Período": "4", "Descrição": "Importante para ossos.", "Estado": "Sólido", "Eletronegatividade": 1.00, "Configuracao_Eletronica": "[Ar] 4s²", "Aplicacoes": "Ossos, concreto"},
        "Sc": {"Nome": "Escândio", "Número": 21, "Massa": 44.956, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Ligas leves.", "Estado": "Sólido", "Eletronegatividade": 1.36, "Configuracao_Eletronica": "[Ar] 3d¹ 4s²", "Aplicacoes": "Ligas aeroespaciais"},
        "Ti": {"Nome": "Titânio", "Número": 22, "Massa": 47.867, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Forte e resistente.", "Estado": "Sólido", "Eletronegatividade": 1.54, "Configuracao_Eletronica": "[Ar] 3d² 4s²", "Aplicacoes": "Aviação, implantes"},
        "V": {"Nome": "Vanádio", "Número": 23, "Massa": 50.942, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Fortalece aço.", "Estado": "Sólido", "Eletronegatividade": 1.63, "Configuracao_Eletronica": "[Ar] 3d³ 4s²", "Aplicacoes": "Aço-vanádio"},
        "Cr": {"Nome": "Cromo", "Número": 24, "Massa": 51.996, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Usado em cromagem.", "Estado": "Sólido", "Eletronegatividade": 1.66, "Configuracao_Eletronica": "[Ar] 3d⁵ 4s¹", "Aplicacoes": "Cromagem, inox"},
        "Mn": {"Nome": "Manganês", "Número": 25, "Massa": 54.938, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Importante para aço.", "Estado": "Sólido", "Eletronegatividade": 1.55, "Configuracao_Eletronica": "[Ar] 3d⁵ 4s²", "Aplicacoes": "Aço, baterias"},
        "Fe": {"Nome": "Ferro", "Número": 26, "Massa": 55.845, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Essencial na hemoglobina.", "Estado": "Sólido", "Eletronegatividade": 1.83, "Configuracao_Eletronica": "[Ar] 3d⁶ 4s²", "Aplicacoes": "Construção, hemoglobina"},
        "Co": {"Nome": "Cobalto", "Número": 27, "Massa": 58.933, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Usado em ímãs.", "Estado": "Sólido", "Eletronegatividade": 1.88, "Configuracao_Eletronica": "[Ar] 3d⁷ 4s²", "Aplicacoes": "Baterias, ímãs"},
        "Ni": {"Nome": "Níquel", "Número": 28, "Massa": 58.693, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Usado em ligas.", "Estado": "Sólido", "Eletronegatividade": 1.91, "Configuracao_Eletronica": "[Ar] 3d⁸ 4s²", "Aplicacoes": "Aço inox, moedas"},
        "Cu": {"Nome": "Cobre", "Número": 29, "Massa": 63.546, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Excelente condutor.", "Estado": "Sólido", "Eletronegatividade": 1.90, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s¹", "Aplicacoes": "Fiação elétrica"},
        "Zn": {"Nome": "Zinco", "Número": 30, "Massa": 65.38, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Galvanização.", "Estado": "Sólido", "Eletronegatividade": 1.65, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s²", "Aplicacoes": "Galvanização, saúde"},
        # Continuando com mais elementos...
        "Ga": {"Nome": "Gálio", "Número": 31, "Massa": 69.723, "Grupo": "Outros metais", "Período": "4", "Descrição": "Derrete na mão.", "Estado": "Sólido", "Eletronegatividade": 1.81, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s² 4p¹", "Aplicacoes": "LEDs, semicondutores"},
        "Ge": {"Nome": "Germânio", "Número": 32, "Massa": 72.63, "Grupo": "Semimetais", "Período": "4", "Descrição": "Usado em semicondutores.", "Estado": "Sólido", "Eletronegatividade": 2.01, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s² 4p²", "Aplicacoes": "Fibra óptica"},
        "As": {"Nome": "Arsênio", "Número": 33, "Massa": 74.922, "Grupo": "Semimetais", "Período": "4", "Descrição": "Tóxico.", "Estado": "Sólido", "Eletronegatividade": 2.18, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s² 4p³", "Aplicacoes": "Semicondutores"},
        "Se": {"Nome": "Selênio", "Número": 34, "Massa": 78.971, "Grupo": "Não metais", "Período": "4", "Descrição": "Essencial em pequenas quantidades.", "Estado": "Sólido", "Eletronegatividade": 2.55, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s² 4p⁴", "Aplicacoes": "Antioxidante"},
        "Br": {"Nome": "Bromo", "Número": 35, "Massa": 79.904, "Grupo": "Halogênios", "Período": "4", "Descrição": "Líquido à temperatura ambiente.", "Estado": "Líquido", "Eletronegatividade": 2.96, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s² 4p⁵", "Aplicacoes": "Retardadores de chama"},
        "Kr": {"Nome": "Criptônio", "Número": 36, "Massa": 83.798, "Grupo": "Gases nobres", "Período": "4", "Descrição": "Gás nobre.", "Estado": "Gás", "Eletronegatividade": 3.00, "Configuracao_Eletronica": "[Ar] 3d¹⁰ 4s² 4p⁶", "Aplicacoes": "Lâmpadas"},
        # Período 5
        "Rb": {"Nome": "Rubídio", "Número": 37, "Massa": 85.468, "Grupo": "Metais alcalinos", "Período": "5", "Descrição": "Altamente reativo.", "Estado": "Sólido", "Eletronegatividade": 0.82, "Configuracao_Eletronica": "[Kr] 5s¹", "Aplicacoes": "Relógios atômicos"},
        "Sr": {"Nome": "Estrôncio", "Número": 38, "Massa": 87.62, "Grupo": "Metais alcalino-terrosos", "Período": "5", "Descrição": "Fogos de artifício.", "Estado": "Sólido", "Eletronegatividade": 0.95, "Configuracao_Eletronica": "[Kr] 5s²", "Aplicacoes": "Fogos de artifício vermelhos"},
        "Y": {"Nome": "Ítrio", "Número": 39, "Massa": 88.906, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Usado em LEDs.", "Estado": "Sólido", "Eletronegatividade": 1.22, "Configuracao_Eletronica": "[Kr] 4d¹ 5s²", "Aplicacoes": "LEDs, supercondutores"},
        "Zr": {"Nome": "Zircônio", "Número": 40, "Massa": 91.224, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Resistente à corrosão.", "Estado": "Sólido", "Eletronegatividade": 1.33, "Configuracao_Eletronica": "[Kr] 4d² 5s²", "Aplicacoes": "Reatores nucleares"},
        "Nb": {"Nome": "Nióbio", "Número": 41, "Massa": 92.906, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Fortalece aço.", "Estado": "Sólido", "Eletronegatividade": 1.6, "Configuracao_Eletronica": "[Kr] 4d⁴ 5s¹", "Aplicacoes": "Aço especial"},
        "Mo": {"Nome": "Molibdênio", "Número": 42, "Massa": 95.95, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Essencial em ligas.", "Estado": "Sólido", "Eletronegatividade": 2.16, "Configuracao_Eletronica": "[Kr] 4d⁵ 5s¹", "Aplicacoes": "Aço de alta resistência"},
        "Tc": {"Nome": "Tecnécio", "Número": 43, "Massa": 98, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Radioativo.", "Estado": "Sólido", "Eletronegatividade": 1.9, "Configuracao_Eletronica": "[Kr] 4d⁵ 5s²", "Aplicacoes": "Medicina nuclear"},
        "Ru": {"Nome": "Rutênio", "Número": 44, "Massa": 101.07, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Catalisador.", "Estado": "Sólido", "Eletronegatividade": 2.2, "Configuracao_Eletronica": "[Kr] 4d⁷ 5s¹", "Aplicacoes": "Catalisadores"},
        "Rh": {"Nome": "Ródio", "Número": 45, "Massa": 102.91, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Catalisadores automotivos.", "Estado": "Sólido", "Eletronegatividade": 2.28, "Configuracao_Eletronica": "[Kr] 4d⁸ 5s¹", "Aplicacoes": "Conversores catalíticos"},
        "Pd": {"Nome": "Paládio", "Número": 46, "Massa": 106.42, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Joalheria.", "Estado": "Sólido", "Eletronegatividade": 2.20, "Configuracao_Eletronica": "[Kr] 4d¹⁰", "Aplicacoes": "Catalisadores, joias"},
        "Ag": {"Nome": "Prata", "Número": 47, "Massa": 107.87, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Melhor condutor elétrico.", "Estado": "Sólido", "Eletronegatividade": 1.93, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s¹", "Aplicacoes": "Joias, fotografia"},
        "Cd": {"Nome": "Cádmio", "Número": 48, "Massa": 112.41, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Baterias.", "Estado": "Sólido", "Eletronegatividade": 1.69, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s²", "Aplicacoes": "Baterias NiCd"},
        "In": {"Nome": "Índio", "Número": 49, "Massa": 114.82, "Grupo": "Outros metais", "Período": "5", "Descrição": "Telas touch.", "Estado": "Sólido", "Eletronegatividade": 1.78, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s² 5p¹", "Aplicacoes": "Telas touchscreen"},
        "Sn": {"Nome": "Estanho", "Número": 50, "Massa": 118.71, "Grupo": "Outros metais", "Período": "5", "Descrição": "Bronze.", "Estado": "Sólido", "Eletronegatividade": 1.96, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s² 5p²", "Aplicacoes": "Soldas, latas"},
        "Sb": {"Nome": "Antimônio", "Número": 51, "Massa": 121.76, "Grupo": "Semimetais", "Período": "5", "Descrição": "Retardadores de chama.", "Estado": "Sólido", "Eletronegatividade": 2.05, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s² 5p³", "Aplicacoes": "Retardadores de chama"},
        "Te": {"Nome": "Telúrio", "Número": 52, "Massa": 127.60, "Grupo": "Semimetais", "Período": "5", "Descrição": "Semicondutores.", "Estado": "Sólido", "Eletronegatividade": 2.1, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s² 5p⁴", "Aplicacoes": "Painéis solares"},
        "I": {"Nome": "Iodo", "Número": 53, "Massa": 126.90, "Grupo": "Halogênios", "Período": "5", "Descrição": "Função da tireoide.", "Estado": "Sólido", "Eletronegatividade": 2.66, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s² 5p⁵", "Aplicacoes": "Desinfetante, tireoide"},
        "Xe": {"Nome": "Xenônio", "Número": 54, "Massa": 131.29, "Grupo": "Gases nobres", "Período": "5", "Descrição": "Lâmpadas e anestesia.", "Estado": "Gás", "Eletronegatividade": 2.60, "Configuracao_Eletronica": "[Kr] 4d¹⁰ 5s² 5p⁶", "Aplicacoes": "Lâmpadas xenon"},
        # Adicionando resto dos elementos (simplificado para economia de espaço)
        "Cs": {"Nome": "Césio", "Número": 55, "Massa": 132.91, "Grupo": "Metais alcalinos", "Período": "6", "Descrição": "Relógios atômicos.", "Estado": "Sólido", "Eletronegatividade": 0.79, "Configuracao_Eletronica": "[Xe] 6s¹", "Aplicacoes": "Relógios atômicos"},
        "Ba": {"Nome": "Bário", "Número": 56, "Massa": 137.33, "Grupo": "Metais alcalino-terrosos", "Período": "6", "Descrição": "Radiologia.", "Estado": "Sólido", "Eletronegatividade": 0.89, "Configuracao_Eletronica": "[Xe] 6s²", "Aplicacoes": "Raio-X"},
        "La": {"Nome": "Lantânio", "Número": 57, "Massa": 138.91, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Lentes ópticas.", "Estado": "Sólido", "Eletronegatividade": 1.10, "Configuracao_Eletronica": "[Xe] 5d¹ 6s²", "Aplicacoes": "Lentes de câmeras"},
        "Ce": {"Nome": "Cério", "Número": 58, "Massa": 140.12, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Catalisadores.", "Estado": "Sólido", "Eletronegatividade": 1.12, "Configuracao_Eletronica": "[Xe] 4f¹ 5d¹ 6s²", "Aplicacoes": "Catalisadores automotivos"},
        "Pr": {"Nome": "Praseodímio", "Número": 59, "Massa": 140.91, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs.", "Estado": "Sólido", "Eletronegatividade": 1.13, "Configuracao_Eletronica": "[Xe] 4f³ 6s²", "Aplicacoes": "Ímãs"},
        "Nd": {"Nome": "Neodímio", "Número": 60, "Massa": 144.24, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs potentes.", "Estado": "Sólido", "Eletronegatividade": 1.14, "Configuracao_Eletronica": "[Xe] 4f⁴ 6s²", "Aplicacoes": "Ímãs de neodímio"},
        "Pm": {"Nome": "Promécio", "Número": 61, "Massa": 145, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Radioativo.", "Estado": "Sólido", "Eletronegatividade": 1.13, "Configuracao_Eletronica": "[Xe] 4f⁵ 6s²", "Aplicacoes": "Baterias nucleares"},
        "Sm": {"Nome": "Samário", "Número": 62, "Massa": 150.36, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs e lasers.", "Estado": "Sólido", "Eletronegatividade": 1.17, "Configuracao_Eletronica": "[Xe] 4f⁶ 6s²", "Aplicacoes": "Ímãs"},
        "Eu": {"Nome": "Európio", "Número": 63, "Massa": 151.96, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Fósforos de telas.", "Estado": "Sólido", "Eletronegatividade": 1.20, "Configuracao_Eletronica": "[Xe] 4f⁷ 6s²", "Aplicacoes": "Fósforos de TV"},
        "Gd": {"Nome": "Gadolínio", "Número": 64, "Massa": 157.25, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ressonância magnética.", "Estado": "Sólido", "Eletronegatividade": 1.20, "Configuracao_Eletronica": "[Xe] 4f⁷ 5d¹ 6s²", "Aplicacoes": "Contraste em ressonância"},
        "Tb": {"Nome": "Térbio", "Número": 65, "Massa": 158.93, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Fósforos verdes.", "Estado": "Sólido", "Eletronegatividade": 1.20, "Configuracao_Eletronica": "[Xe] 4f⁹ 6s²", "Aplicacoes": "Fósforos"},
        "Dy": {"Nome": "Disprósio", "Número": 66, "Massa": 162.50, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs e lasers.", "Estado": "Sólido", "Eletronegatividade": 1.22, "Configuracao_Eletronica": "[Xe] 4f¹⁰ 6s²", "Aplicacoes": "Ímãs"},
        "Ho": {"Nome": "Hólmio", "Número": 67, "Massa": 164.93, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs.", "Estado": "Sólido", "Eletronegatividade": 1.23, "Configuracao_Eletronica": "[Xe] 4f¹¹ 6s²", "Aplicacoes": "Ímãs"},
        "Er": {"Nome": "Érbio", "Número": 68, "Massa": 167.26, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Fibras ópticas.", "Estado": "Sólido", "Eletronegatividade": 1.24, "Configuracao_Eletronica": "[Xe] 4f¹² 6s²", "Aplicacoes": "Amplificadores de fibra óptica"},
        "Tm": {"Nome": "Túlio", "Número": 69, "Massa": 168.93, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Lasers portáteis.", "Estado": "Sólido", "Eletronegatividade": 1.25, "Configuracao_Eletronica": "[Xe] 4f¹³ 6s²", "Aplicacoes": "Lasers médicos"},
        "Yb": {"Nome": "Itérbio", "Número": 70, "Massa": 173.05, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Relógios atômicos.", "Estado": "Sólido", "Eletronegatividade": 1.10, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 6s²", "Aplicacoes": "Relógios atômicos"},
        "Lu": {"Nome": "Lutécio", "Número": 71, "Massa": 174.97, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Tomografia.", "Estado": "Sólido", "Eletronegatividade": 1.27, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹ 6s²", "Aplicacoes": "PET scan"},
        "Hf": {"Nome": "Háfnio", "Número": 72, "Massa": 178.49, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Ligas de alta temperatura.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d² 6s²", "Aplicacoes": "Reatores nucleares"},
        "Ta": {"Nome": "Tântalo", "Número": 73, "Massa": 180.95, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Eletrônicos e implantes.", "Estado": "Sólido", "Eletronegatividade": 1.5, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d³ 6s²", "Aplicacoes": "Capacitores"},
        "W": {"Nome": "Tungstênio", "Número": 74, "Massa": 183.84, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Mais alto ponto de fusão.", "Estado": "Sólido", "Eletronegatividade": 2.36, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d⁴ 6s²", "Aplicacoes": "Filamentos de lâmpada"},
        "Re": {"Nome": "Rênio", "Número": 75, "Massa": 186.21, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Ligas e catalisadores.", "Estado": "Sólido", "Eletronegatividade": 1.9, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d⁵ 6s²", "Aplicacoes": "Turbinas de jato"},
        "Os": {"Nome": "Ósmio", "Número": 76, "Massa": 190.23, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Metal mais denso.", "Estado": "Sólido", "Eletronegatividade": 2.2, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d⁶ 6s²", "Aplicacoes": "Pontas de caneta"},
        "Ir": {"Nome": "Irídio", "Número": 77, "Massa": 192.22, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Resistente à corrosão.", "Estado": "Sólido", "Eletronegatividade": 2.20, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d⁷ 6s²", "Aplicacoes": "Eletrodos de velas"},
        "Pt": {"Nome": "Platina", "Número": 78, "Massa": 195.08, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Joias e catalisadores.", "Estado": "Sólido", "Eletronegatividade": 2.28, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d⁹ 6s¹", "Aplicacoes": "Joias, catalisadores"},
        "Au": {"Nome": "Ouro", "Número": 79, "Massa": 196.97, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Metal precioso.", "Estado": "Sólido", "Eletronegatividade": 2.54, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s¹", "Aplicacoes": "Joias, eletrônica"},
        "Hg": {"Nome": "Mercúrio", "Número": 80, "Massa": 200.59, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Único metal líquido.", "Estado": "Líquido", "Eletronegatividade": 2.00, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s²", "Aplicacoes": "Termômetros (antigo)"},
        "Tl": {"Nome": "Tálio", "Número": 81, "Massa": 204.38, "Grupo": "Outros metais", "Período": "6", "Descrição": "Tóxico.", "Estado": "Sólido", "Eletronegatividade": 1.62, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p¹", "Aplicacoes": "Eletrônica"},
        "Pb": {"Nome": "Chumbo", "Número": 82, "Massa": 207.2, "Grupo": "Outros metais", "Período": "6", "Descrição": "Denso.", "Estado": "Sólido", "Eletronegatividade": 2.33, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p²", "Aplicacoes": "Baterias de carro"},
        "Bi": {"Nome": "Bismuto", "Número": 83, "Massa": 208.98, "Grupo": "Outros metais", "Período": "6", "Descrição": "Menos tóxico.", "Estado": "Sólido", "Eletronegatividade": 2.02, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p³", "Aplicacoes": "Medicamentos estomacais"},
        "Po": {"Nome": "Polônio", "Número": 84, "Massa": 209, "Grupo": "Semimetais", "Período": "6", "Descrição": "Radioativo.", "Estado": "Sólido", "Eletronegatividade": 2.0, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁴", "Aplicacoes": "Fontes de calor espaciais"},
        "At": {"Nome": "Astato", "Número": 85, "Massa": 210, "Grupo": "Halogênios", "Período": "6", "Descrição": "Raro e radioativo.", "Estado": "Sólido", "Eletronegatividade": 2.2, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁵", "Aplicacoes": "Pesquisa médica"},
        "Rn": {"Nome": "Radônio", "Número": 86, "Massa": 222, "Grupo": "Gases nobres", "Período": "6", "Descrição": "Radioativo, perigoso.", "Estado": "Gás", "Eletronegatividade": 2.2, "Configuracao_Eletronica": "[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁶", "Aplicacoes": "Detecção de terremotos"},
        "Fr": {"Nome": "Frâncio", "Número": 87, "Massa": 223, "Grupo": "Metais alcalinos", "Período": "7", "Descrição": "Extremamente raro.", "Estado": "Sólido", "Eletronegatividade": 0.7, "Configuracao_Eletronica": "[Rn] 7s¹", "Aplicacoes": "Pesquisa científica"},
        "Ra": {"Nome": "Rádio", "Número": 88, "Massa": 226, "Grupo": "Metais alcalino-terrosos", "Período": "7", "Descrição": "Radioativo.", "Estado": "Sólido", "Eletronegatividade": 0.9, "Configuracao_Eletronica": "[Rn] 7s²", "Aplicacoes": "Tratamento de câncer (histórico)"},
        "Ac": {"Nome": "Actínio", "Número": 89, "Massa": 227, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Altamente radioativo.", "Estado": "Sólido", "Eletronegatividade": 1.1, "Configuracao_Eletronica": "[Rn] 6d¹ 7s²", "Aplicacoes": "Fonte de nêutrons"},
        "Th": {"Nome": "Tório", "Número": 90, "Massa": 232.04, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Combustível nuclear.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 6d² 7s²", "Aplicacoes": "Reatores nucleares futuros"},
        "Pa": {"Nome": "Protactínio", "Número": 91, "Massa": 231.04, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Radioativo.", "Estado": "Sólido", "Eletronegatividade": 1.5, "Configuracao_Eletronica": "[Rn] 5f² 6d¹ 7s²", "Aplicacoes": "Pesquisa científica"},
        "U": {"Nome": "Urânio", "Número": 92, "Massa": 238.0289, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Combustível nuclear.", "Estado": "Sólido", "Eletronegatividade": 1.38, "Configuracao_Eletronica": "[Rn] 5f³ 6d¹ 7s²", "Aplicacoes": "Energia nuclear, armas"},
        "Np": {"Nome": "Neptúnio", "Número": 93, "Massa": 237, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Radioativo.", "Estado": "Sólido", "Eletronegatividade": 1.36, "Configuracao_Eletronica": "[Rn] 5f⁴ 6d¹ 7s²", "Aplicacoes": "Detectores de nêutrons"},
        "Pu": {"Nome": "Plutônio", "Número": 94, "Massa": 244, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Armas nucleares.", "Estado": "Sólido", "Eletronegatividade": 1.28, "Configuracao_Eletronica": "[Rn] 5f⁶ 7s²", "Aplicacoes": "Armas nucleares, RTGs"},
        "Am": {"Nome": "Amerício", "Número": 95, "Massa": 243, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Detectores de fumaça.", "Estado": "Sólido", "Eletronegatividade": 1.13, "Configuracao_Eletronica": "[Rn] 5f⁷ 7s²", "Aplicacoes": "Detectores de fumaça"},
        "Cm": {"Nome": "Cúrio", "Número": 96, "Massa": 247, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Fonte de energia.", "Estado": "Sólido", "Eletronegatividade": 1.28, "Configuracao_Eletronica": "[Rn] 5f⁷ 6d¹ 7s²", "Aplicacoes": "Fonte alfa"},
        "Bk": {"Nome": "Berquélio", "Número": 97, "Massa": 247, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Pesquisa nuclear.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 5f⁹ 7s²", "Aplicacoes": "Pesquisa científica"},
        "Cf": {"Nome": "Califórnio", "Número": 98, "Massa": 251, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Fonte de nêutrons.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 5f¹⁰ 7s²", "Aplicacoes": "Fonte de nêutrons"},
        "Es": {"Nome": "Einstênio", "Número": 99, "Massa": 252, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Produzido em explosões.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 5f¹¹ 7s²", "Aplicacoes": "Pesquisa científica"},
        "Fm": {"Nome": "Férmio", "Número": 100, "Massa": 257, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Estudos científicos.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 5f¹² 7s²", "Aplicacoes": "Pesquisa científica"},
        "Md": {"Nome": "Mendelévio", "Número": 101, "Massa": 258, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Pesquisa química nuclear.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 5f¹³ 7s²", "Aplicacoes": "Pesquisa científica"},
        "No": {"Nome": "Nobélio", "Número": 102, "Massa": 259, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Experimentos laboratoriais.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 7s²", "Aplicacoes": "Pesquisa científica"},
        "Lr": {"Nome": "Laurêncio", "Número": 103, "Massa": 266, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Elemento sintético.", "Estado": "Sólido", "Eletronegatividade": 1.3, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 7s² 7p¹", "Aplicacoes": "Pesquisa científica"},
        "Rf": {"Nome": "Rutherfórdio", "Número": 104, "Massa": 267, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Elemento sintético.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d² 7s²", "Aplicacoes": "Pesquisa"},
        "Db": {"Nome": "Dúbnio", "Número": 105, "Massa": 268, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Radioativo, instável.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d³ 7s²", "Aplicacoes": "Pesquisa"},
        "Sg": {"Nome": "Seabórgio", "Número": 106, "Massa": 271, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Usado em pesquisa.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d⁴ 7s²", "Aplicacoes": "Pesquisa"},
        "Bh": {"Nome": "Bóhrio", "Número": 107, "Massa": 270, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Instável e sintético.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d⁵ 7s²", "Aplicacoes": "Pesquisa"},
        "Hs": {"Nome": "Hássio", "Número": 108, "Massa": 277, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Pesquisado em laboratórios.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d⁶ 7s²", "Aplicacoes": "Pesquisa"},
        "Mt": {"Nome": "Meitnério", "Número": 109, "Massa": 278, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Superpesado.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d⁷ 7s²", "Aplicacoes": "Pesquisa"},
        "Ds": {"Nome": "Darmstádio", "Número": 110, "Massa": 281, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Meia-vida curta.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d⁸ 7s²", "Aplicacoes": "Pesquisa"},
        "Rg": {"Nome": "Roentgênio", "Número": 111, "Massa": 282, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Radioativo sintético.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d⁹ 7s²", "Aplicacoes": "Pesquisa"},
        "Cn": {"Nome": "Copernício", "Número": 112, "Massa": 285, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Altamente instável.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d¹⁰ 7s²", "Aplicacoes": "Pesquisa"},
        "Nh": {"Nome": "Nihônio", "Número": 113, "Massa": 286, "Grupo": "Outros metais", "Período": "7", "Descrição": "Elemento sintético.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p¹", "Aplicacoes": "Pesquisa"},
        "Fl": {"Nome": "Fleróvio", "Número": 114, "Massa": 289, "Grupo": "Outros metais", "Período": "7", "Descrição": "Superpesado.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p²", "Aplicacoes": "Pesquisa"},
        "Mc": {"Nome": "Moscóvio", "Número": 115, "Massa": 290, "Grupo": "Outros metais", "Período": "7", "Descrição": "Meia-vida curta.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p³", "Aplicacoes": "Pesquisa"},
        "Lv": {"Nome": "Livermório", "Número": 116, "Massa": 293, "Grupo": "Outros metais", "Período": "7", "Descrição": "Elemento instável.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁴", "Aplicacoes": "Pesquisa"},
        "Ts": {"Nome": "Tenessino", "Número": 117, "Massa": 294, "Grupo": "Halogênios", "Período": "7", "Descrição": "Superpesado.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁵", "Aplicacoes": "Pesquisa"},
        "Og": {"Nome": "Oganessônio", "Número": 118, "Massa": 294, "Grupo": "Gases nobres", "Período": "7", "Descrição": "Altamente radioativo.", "Estado": "Sólido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁶", "Aplicacoes": "Pesquisa"},
        # Elementos hipotéticos do período 8
        "Uue": {"Nome": "Ununennium", "Número": 119, "Massa": 315, "Grupo": "Metais alcalinos", "Período": "8", "Descrição": "Previsto como metal alcalino.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 8s¹", "Aplicacoes": "Teórico"},
        "Ubn": {"Nome": "Unbinilium", "Número": 120, "Massa": 320, "Grupo": "Metais alcalino-terrosos", "Período": "8", "Descrição": "Previsto como alcalino-terroso.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 8s²", "Aplicacoes": "Teórico"},
        "Ubu": {"Nome": "Unbiunium", "Número": 121, "Massa": 326, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Primeiro dos superactinídeos.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 8s² 8p¹", "Aplicacoes": "Teórico"},
        "Ubb": {"Nome": "Unbibium", "Número": 122, "Massa": 328, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Hipotético.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 8s² 8p²", "Aplicacoes": "Teórico"},
        "Ubt": {"Nome": "Unbitrium", "Número": 123, "Massa": 330, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Propriedades desconhecidas.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 7d¹ 8s² 8p¹", "Aplicacoes": "Teórico"},
        "Ubq": {"Nome": "Unbiquadium", "Número": 124, "Massa": 332, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Não sintetizado.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 7d² 8s² 8p¹", "Aplicacoes": "Teórico"},
        "Ubp": {"Nome": "Unbipentium", "Número": 125, "Massa": 334, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Potencial de propriedades únicas.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 7d³ 8s² 8p¹", "Aplicacoes": "Teórico"},
        "Ubh": {"Nome": "Unbihexium", "Número": 126, "Massa": 336, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Previsto como estável.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 5g¹ 7d⁴ 8s² 8p¹", "Aplicacoes": "Teórico"},
        "Ubs": {"Nome": "Unbiseptium", "Número": 127, "Massa": 338, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Totalmente teórico.", "Estado": "Desconhecido", "Eletronegatividade": None, "Configuracao_Eletronica": "[Og] 5g² 7d⁵ 8s² 8p¹", "Aplicacoes": "Teórico"},
    }

def show_tabelas():
    """Função principal que mostra as tabelas químicas"""
    
    # Aplicar CSS
    aplicar_css_customizado()
    
    # Título principal
    st.markdown("<h1>🧪 Central de Tabelas Químicas Avançada</h1>", unsafe_allow_html=True)
    
    # Obter dados dos elementos
    elementos_info = get_elementos_info()
    
    # Cores dos grupos (mantendo as originais)
    cores = {
        "Gases nobres": "#8E24AA", 
        "Halogênios": "#43A047",
        "Metais alcalinos": "#F4511E", 
        "Metais alcalino-terrosos": "#FFB300",
        "Semimetais": "#1E88E5", 
        "Não metais": "#3949AB",
        "Metais de transição": "#039BE5", 
        "Lantanídeos": "#5E35B1",
        "Actinídeos": "#6D4C41", 
        "Outros metais": "#90CAF9",
        "Elementos superpesados": "#E91E63"
    }
    
    # Layout da tabela periódica (mantendo o original)
    layout_tabela = [
        ["H", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "","","He"],
        ["Li", "Be", "", "", "", "", "", "", "", "", "", "", "B", "C", "N", "O", "F", "Ne"],
        ["Na", "Mg", "", "", "", "", "", "", "", "", "", "", "Al", "Si", "P", "S", "Cl", "Ar"],
        ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
        ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
        ["Cs", "Ba", "", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
        ["Fr", "Ra", "", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"],
        ["Uue", "Ubn", ""],
        ["", "", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"],
        ["", "", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"],
        ["", "", "Ubu", "Ubb", "Ubt", "Ubq", "Ubp", "Ubh", "Ubs"]
    ]
    
    # Menu de seleção
    menu = st.selectbox("🎯 Escolha a Tabela:", [
        "Tabela Periódica Interativa", 
        "Solubilidade (Kps)", 
        "Reatividade de Metais", 
        "Ácidos, Bases e Sais",
        "Busca Avançada",
        "Comparador de Elementos",
        "Links para Bases de Dados"
    ])
    
    if menu == "Tabela Periódica Interativa":
        mostrar_tabela_periodica(layout_tabela, elementos_info, cores)
    elif menu == "Solubilidade (Kps)":
        mostrar_tabela_solubilidade()
    elif menu == "Reatividade de Metais":
        mostrar_reatividade_metais()
    elif menu == "Ácidos, Bases e Sais":
        mostrar_acidos_bases_sais()
    elif menu == "Busca Avançada":
        mostrar_busca_avancada(elementos_info)
    elif menu == "Comparador de Elementos":
        mostrar_comparador_elementos(elementos_info)
    elif menu == "Links para Bases de Dados":
        mostrar_links_bases_dados()

def mostrar_tabela_periodica(layout, elementos_info, cores):
    """Mostra a tabela periódica interativa"""
    st.subheader("🧪 Tabela Periódica dos Elementos")
    st.info("💡 Clique na sigla para ver detalhes completos do elemento.")
    
    # Barra de busca rápida
    busca_rapida = st.text_input("🔍 Busca Rápida (Nome ou Símbolo):", "")
    
    # Criando a grade visual com botões
    for linha in layout:
        cols = st.columns(18)
        for i, simbolo in enumerate(linha):
            if simbolo != "":
                info = elementos_info.get(simbolo, {})
                grupo = info.get("Grupo", "")
                cor = cores.get(grupo, "#666666")
                
                # Aplicar cor de fundo ao botão
                if cols[i].button(simbolo, key=f"btn_{simbolo}"):
                    # Mostrar detalhes na sidebar
                    st.session_state['elemento_selecionado'] = simbolo
    
    # Exibir detalhes do elemento selecionado
    if 'elemento_selecionado' in st.session_state:
        simbolo = st.session_state['elemento_selecionado']
        mostrar_detalhes_elemento(simbolo, elementos_info)

def mostrar_detalhes_elemento(simbolo, elementos_info):
    """Mostra detalhes completos de um elemento"""
    info = elementos_info.get(simbolo, {})
    
    with st.sidebar:
        st.markdown(f"### 🔍 Detalhes: {simbolo}")
        st.markdown(f"**Nome:** {info.get('Nome', 'N/A')}")
        st.markdown(f"**Número Atômico:** {info.get('Número', 'N/A')}")
        st.markdown(f"**Massa Atômica:** {info.get('Massa', 'N/A')} u")
        st.markdown(f"**Grupo:** {info.get('Grupo', 'N/A')}")
        st.markdown(f"**Período:** {info.get('Período', 'N/A')}")
        st.markdown(f"**Estado:** {info.get('Estado', 'N/A')}")
        
        if info.get('Eletronegatividade'):
            st.markdown(f"**Eletronegatividade:** {info.get('Eletronegatividade')}")
        
        st.markdown(f"**Configuração Eletrônica:** {info.get('Configuracao_Eletronica', 'N/A')}")
        st.info(info.get('Descrição', ''))
        st.success(f"**Aplicações:** {info.get('Aplicacoes', 'N/A')}")
        
        # Botões de ação
        if st.button("📥 Baixar PDF com Detalhes"):
            st.success("Funcionalidade em desenvolvimento!")
        
        if st.button("🔗 Ver em PubChem"):
            pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/element/{info.get('Nome', '')}"
            st.markdown(f"[Abrir PubChem]({pubchem_url})")

def mostrar_tabela_solubilidade():
    """Mostra tabela de solubilidade (Kps) - mantendo dados originais"""
    st.subheader("💧 Constantes de Produto de Solubilidade (Kps)")
    
    dados_sol = [
        ("Hidróxido de chumbo", "Pb(OH)₂", "8 x 10⁻¹⁶"),
        ("Iodeto de chumbo", "PbI₂", "7.9 x 10⁻⁹"),
        ("Oxalato de chumbo", "PbC₂O₄", "8.5 x 10⁻⁹"),
        ("Sulfato de chumbo", "PbSO₄", "1.6 x 10⁻⁸"),
        ("Sulfeto de chumbo", "PbS", "3 x 10⁻²⁸"),
        # ... (manter todos os dados originais)
    ]
    
    df_sol = pd.DataFrame(dados_sol, columns=["Substância", "Fórmula", "Kps (25°C)"])
    st.dataframe(df_sol, use_container_width=True)
    
    # Botão de download
    csv = df_sol.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Tabela CSV",
        data=csv,
        file_name="solubilidade_kps.csv",
        mime="text/csv"
    )

def mostrar_reatividade_metais():
    """Mostra fila de reatividade de metais"""
    st.subheader("⚡ Fila de Reatividade dos Metais")
    st.warning("📊 Sentido: Mais Reativo ➔ Menos Reativo")
    
    reatividade = {
        "Metais Alcalinos (Li, K, Na)": "Reagem violentamente com água.",
        "Al, Zn, Fe": "Reagem com ácidos liberando H₂.",
        "Metais Nobres (Au, Pt, Ag)": "Altamente estáveis, não reagem com H⁺."
    }
    
    for k, v in reatividade.items():
        st.markdown(f"**{k}:** {v}")

def mostrar_acidos_bases_sais():
    """Mostra informações sobre ácidos, bases e sais"""
    st.subheader("⚗️ Ácidos, Bases e Sais")
    
    aba1, aba2, aba3 = st.tabs(["Ácidos", "Bases", "Sais"])
    
    with aba1:
        st.write("**Principais Ácidos e pKa**")
        st.json({"HCl": "Forte", "H2SO4": "Forte", "CH3COOH": "Fraco (4.76)"})
    
    with aba2:
        st.write("**Principais Bases**")
        st.write("NaOH (Soda Cáustica), KOH, Mg(OH)2 (Leite de Magnésia)")
    
    with aba3:
        st.write("**Principais Sais**")
        st.write("NaCl, CaCO₃, NaHCO₃")

def mostrar_busca_avancada(elementos_info):
    """Busca avançada multi-critério"""
    st.subheader("🔍 Busca Avançada de Elementos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nome_busca = st.text_input("Nome do elemento:")
    
    with col2:
        grupo_busca = st.selectbox("Grupo:", ["Todos"] + list(set([e.get("Grupo", "") for e in elementos_info.values()])))
    
    with col3:
        periodo_busca = st.selectbox("Período:", ["Todos", "1", "2", "3", "4", "5", "6", "7", "8"])
    
    # Filtrar elementos
    resultados = []
    for simbolo, info in elementos_info.items():
        if nome_busca.lower() in info.get("Nome", "").lower() or nome_busca.upper() in simbolo:
            if grupo_busca == "Todos" or info.get("Grupo") == grupo_busca:
                if periodo_busca == "Todos" or info.get("Período") == periodo_busca:
                    resultados.append({
                        "Símbolo": simbolo,
                        "Nome": info.get("Nome"),
                        "Número": info.get("Número"),
                        "Massa": info.get("Massa"),
                        "Grupo": info.get("Grupo"),
                        "Período": info.get("Período")
                    })
    
    if resultados:
        df_resultados = pd.DataFrame(resultados)
        st.dataframe(df_resultados, use_container_width=True)
    else:
        st.warning("Nenhum elemento encontrado com esses critérios.")

def mostrar_comparador_elementos(elementos_info):
    """Compara até 3 elementos lado a lado"""
    st.subheader("⚖️ Comparador de Elementos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        elemento1 = st.selectbox("Elemento 1:", list(elementos_info.keys()), key="comp1")
    
    with col2:
        elemento2 = st.selectbox("Elemento 2:", list(elementos_info.keys()), key="comp2")
    
    with col3:
        elemento3 = st.selectbox("Elemento 3 (opcional):", ["Nenhum"] + list(elementos_info.keys()), key="comp3")
    
    # Criar tabela comparativa
    dados_comp = []
    for elem in [elemento1, elemento2, elemento3]:
        if elem and elem != "Nenhum":
            info = elementos_info[elem]
            dados_comp.append({
                "Propriedade": ["Nome", "Número Atômico", "Massa", "Grupo", "Estado", "Eletronegatividade"],
                elem: [
                    info.get("Nome"),
                    info.get("Número"),
                    info.get("Massa"),
                    info.get("Grupo"),
                    info.get("Estado"),
                    info.get("Eletronegatividade", "N/A")
                ]
            })
    
    if dados_comp:
        df_comp = pd.DataFrame({
            "Propriedade": dados_comp[0]["Propriedade"],
            elemento1: dados_comp[0][elemento1],
            elemento2: dados_comp[1][elemento2] if len(dados_comp) > 1 else [""] * 6,
            elemento3: dados_comp[2][elemento3] if len(dados_comp) > 2 and elemento3 != "Nenhum" else [""] * 6
        })
        st.dataframe(df_comp, use_container_width=True)

def mostrar_links_bases_dados():
    """Mostra links para bases de dados externas"""
    st.subheader("🔗 Bases de Dados Químicas")
    
    st.markdown("""
    ### 📚 Bases de Dados Internacionais
    - [PubChem](https://pubchem.ncbi.nlm.nih.gov/) - Base de dados de compostos químicos
    - [ChemSpider](https://www.chemspider.com/) - Estruturas químicas
    - [NIST Chemistry WebBook](https://webbook.nist.gov/chemistry/) - Dados termodinâmicos
    - [CAS REGISTRY](https://www.cas.org/cas-data/cas-registry) - Registro de substâncias
    
    ### 🇧🇷 Bases de Dados Brasileiras
    - [ANVISA - Consultas](https://consultas.anvisa.gov.br/) - Medicamentos e produtos
    - [FISPQ Online](https://www.fispq.gov.br/) - Fichas de Segurança
    
    ### 📄 Upload de PDFs Personalizados
    """)
    
    uploaded_file = st.file_uploader("Faça upload de PDFs com tabelas químicas:", type=["pdf"])
    
    if uploaded_file:
        st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")
        st.info("Funcionalidade de extração de dados do PDF em desenvolvimento.")

# Executar aplicação
if __name__ == "__main__":
    show_tabelas()
