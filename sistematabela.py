import streamlit as st
import pandas as pd
import os
from groq import Groq

def show_tabelas():
    # --- CONFIGURAÇÃO DA IA (LLAMA-3.3-70B-VERSATILE) ---
    client = None
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
    except Exception:
        pass

    # --- ESTILIZAÇÃO DE INTERFACE (BOTÕES E GRIDS) ---
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important;
            height: 45px !important;
            font-size: 12px !important;
            font-weight: bold !important;
            border: 1px solid #555 !important;
            border-radius: 4px;
            transition: 0.3s;
        }
        div.stButton > button:hover {
            border-color: #00d4ff !important;
            color: #00d4ff !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- NAVEGAÇÃO POR SISTEMA (SIDEBAR) ---
    with st.sidebar:
        st.title("📂 Central Saraiva")
        sistema = st.radio("Escolha o Sistema:", [
            "🔳 Tabela Periódica",
            "📊 Bases de Dados (Kps/Metais)",
            "🤖 Agente IA Multimodal",
            "🌐 Portais e Regulação"
        ])
        st.divider()
        st.info("Status: Conectado ao Llama-3.3-Versatile")

    # --- 1. MÓDULO: TABELA PERIÓDICA COMPLETA ---
    if sistema == "🔳 Tabela Periódica":
        st.title("🧪 Tabela Periódica Interativa")
        st.write("Clique no elemento para carregar a ficha técnica na lateral.")

        elementos_info = {
            "H": {"Nome": "Hidrogênio", "Número": 1, "Massa": 1.008, "Grupo": "Não metais", "Descrição": "Elemento mais leve e abundante."},
            "He": {"Nome": "Hélio", "Número": 2, "Massa": 4.0026, "Grupo": "Gases nobres", "Descrição": "Gás nobre, usado em balões."},
            "Li": {"Nome": "Lítio", "Número": 3, "Massa": 6.94, "Grupo": "Metais alcalinos", "Descrição": "Metal altamente reativo, usado em baterias."},
            "Be": {"Nome": "Berílio", "Número": 4, "Massa": 9.0122, "Grupo": "Metais alcalino-terrosos", "Descrição": "Usado em ligas aeroespaciais."},
            "B": {"Nome": "Boro", "Número": 5, "Massa": 10.81, "Grupo": "Semimetais", "Descrição": "Usado em vidros borossilicatos."},
            "C": {"Nome": "Carbono", "Número": 6, "Massa": 12.011, "Grupo": "Não metais", "Descrição": "Base da química orgânica e da vida."},
            "N": {"Nome": "Nitrogênio", "Número": 7, "Massa": 14.007, "Grupo": "Não metais", "Descrição": "78% da atmosfera terrestre."},
            "O": {"Nome": "Oxigênio", "Número": 8, "Massa": 15.999, "Grupo": "Não metais", "Descrição": "Essencial para a respiração celular."},
            "F": {"Nome": "Flúor", "Número": 9, "Massa": 18.998, "Grupo": "Halogênios", "Descrição": "Elemento mais eletronegativo."},
            "Ne": {"Nome": "Neônio", "Número": 10, "Massa": 20.180, "Grupo": "Gases nobres", "Descrição": "Usado em letreiros luminosos."},
            "Na": {"Nome": "Sódio", "Número": 11, "Massa": 22.990, "Grupo": "Metais alcalinos", "Descrição": "Reage violentamente com a água."},
            "Mg": {"Nome": "Magnésio", "Número": 12, "Massa": 24.305, "Grupo": "Metais alcalino-terrosos", "Descrição": "Importante na clorofila e ligas leves."},
            "Al": {"Nome": "Alumínio", "Número": 13, "Massa": 26.982, "Grupo": "Outros metais", "Descrição": "Metal leve e resistente à corrosão."},
            "Si": {"Nome": "Silício", "Número": 14, "Massa": 28.085, "Grupo": "Semimetais", "Descrição": "Base da indústria de semicondutores."},
            "P": {"Nome": "Fósforo", "Número": 15, "Massa": 30.974, "Grupo": "Não metais", "Descrição": "Essencial no DNA e ATP."},
            "S": {"Nome": "Enxofre", "Número": 16, "Massa": 32.06, "Grupo": "Não metais", "Descrição": "Usado na produção de ácido sulfúrico."},
            "Cl": {"Nome": "Cloro", "Número": 17, "Massa": 35.45, "Grupo": "Halogênios", "Descrição": "Usado em purificação de água e PVC."},
            "Ar": {"Nome": "Argônio", "Número": 18, "Massa": 39.948, "Grupo": "Gases nobres", "Descrição": "Gás inerte para soldagem e lâmpadas."},
            "K": {"Nome": "Potássio", "Número": 19, "Massa": 39.098, "Grupo": "Metais alcalinos", "Descrição": "Essencial para funções nervosas."},
            "Ca": {"Nome": "Cálcio", "Número": 20, "Massa": 40.078, "Grupo": "Metais alcalino-terrosos", "Descrição": "Fundamental para ossos e dentes."},
            "Fe": {"Nome": "Ferro", "Número": 26, "Massa": 55.845, "Grupo": "Metais de transição", "Descrição": "Base da indústria siderúrgica e hemoglobina."},
            "Cu": {"Nome": "Cobre", "Número": 29, "Massa": 63.546, "Grupo": "Metais de transição", "Descrição": "Excelente condutor elétrico."},
            "Au": {"Nome": "Ouro", "Número": 79, "Massa": 196.97, "Grupo": "Metais de transição", "Descrição": "Metal nobre de alta maleabilidade."},
            "U": {"Nome": "Urânio", "Número": 92, "Massa": 238.02, "Grupo": "Actinídeos", "Descrição": "Principal combustível nuclear."},
            "Og": {"Nome": "Oganessônio", "Número": 118, "Massa": 294, "Grupo": "Gases nobres", "Descrição": "Elemento sintético superpesado."}
        }

        layout_tabela = [
            ["H", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "He"],
            ["Li", "Be", "", "", "", "", "", "", "", "", "", "", "B", "C", "N", "O", "F", "Ne"],
            ["Na", "Mg", "", "", "", "", "", "", "", "", "", "", "Al", "Si", "P", "S", "Cl", "Ar"],
            ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
            ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
            ["Cs", "Ba", "", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
            ["Fr", "Ra", "", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"]
        ]

        # Renderização da Grid
        for linha in layout_tabela:
            cols = st.columns(18)
            for i, simbolo in enumerate(linha):
                if simbolo != "":
                    if cols[i].button(simbolo, key=f"el_{simbolo}"):
                        info = elementos_info.get(simbolo, {"Nome": "Desconhecido", "Massa": "-", "Grupo": "-", "Descrição": "Dados em atualização."})
                        st.sidebar.markdown(f"## 🔍 Elemento: {simbolo}")
                        st.sidebar.write(f"**Nome:** {info['Nome']}")
                        st.sidebar.write(f"**Massa:** {info['Massa']}")
                        st.sidebar.write(f"**Grupo:** {info['Grupo']}")
                        st.sidebar.info(info['Descrição'])

    # --- 2. MÓDULO: BASES DE DADOS (Kps e Reatividade) ---
    elif sistema == "📊 Bases de Dados (Kps/Metais)":
        st.title("📊 Tabelas de Solubilidade e Reatividade")
        
        aba1, aba2 = st.tabs(["💧 Solubilidade (Kps)", "⚡ Fila de Reatividade"])
        
        with aba1:
            dados_sol = [
                ("Cloreto de Prata", "AgCl", "1.8 x 10⁻¹⁰"),
                ("Sulfato de Bário", "BaSO₄", "1.1 x 10⁻¹⁰"),
                ("Carbonato de Cálcio", "CaCO₃", "3.3 x 10⁻⁹"),
                ("Hidróxido de Magnésio", "Mg(OH)₂", "5.6 x 10⁻¹²"),
                ("Sulfeto de Chumbo", "PbS", "3.0 x 10⁻²⁸")
            ]
            df_sol = pd.DataFrame(dados_sol, columns=["Substância", "Fórmula", "Kps (25°C)"])
            st.table(df_sol)

        with aba2:
            st.subheader("Ordem de Reatividade dos Metais")
            
            st.warning("Metais Nobres (Au, Pt, Ag) apresentam a menor reatividade do sistema.")

    # --- 3. MÓDULO: AGENTE IA MULTIMODAL ---
    elif sistema == "🤖 Agente IA Multimodal":
        st.title("🤖 Agente Llama-3.3 Versatile")
        st.write("Analise textos, descreva reações ou peça orientações técnicas.")
        
        # Simulação de Multimodalidade (Interface pronta)
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            st.file_uploader("📁 Subir Foto/PDF", type=["jpg", "png", "pdf"], help="Analise fichas de segurança (MSDS)")
            st.file_uploader("🎤 Subir Áudio/Vídeo", type=["mp3", "mp4"])
            
        with col_txt:
            pergunta = st.text_area("Comando do Especialista:", placeholder="Ex: Avalie a compatibilidade do ácido sulfúrico com recipientes de zinco...")
            if st.button("🔍 EXECUTAR CONSULTA"):
                if client and pergunta:
                    with st.spinner("IA processando dados científicos..."):
                        chat = client.chat.completions.create(
                            messages=[{"role": "user", "content": f"Aja como um doutor em química e farmacologia. Analise: {pergunta}"}],
                            model="llama-3.3-70b-versatile"
                        )
                        st.success("Análise Técnica Concluída:")
                        st.markdown(chat.choices[0].message.content)

    # --- 4. MÓDULO: PORTAIS E REGULAÇÃO ---
    elif sistema == "🌐 Portais e Regulação":
        st.title("🌐 Acesso a Sistemas Oficiais")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.link_button("💊 ANVISA (RDC 344)", "https://www.in.gov.br/consulta/-/buscar/dou?q=RDC+344")
        with c2:
            st.link_button("🌍 ONU (GHS)", "https://unece.org/about-ghs")
        with c3:
            st.link_button("🧪 PubChem (NIH)", "https://pubchem.ncbi.nlm.nih.gov/")
            
        st.divider()
        st.subheader("Consulta Direta - CRQ-SP")
        st.components.v1.iframe("https://crqsp.org.br/tabelaperiodica/", height=800, scrolling=True)

if __name__ == "__main__":
    show_tabelas()
