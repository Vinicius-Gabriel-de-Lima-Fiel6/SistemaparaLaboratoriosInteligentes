import streamlit as st
import pandas as pd

# ==============================================================================
# 1. FUNÇÕES AUXILIARES E LÓGICA QUÍMICA
# ==============================================================================

def superscript(n):
    """Converte números inteiros para caracteres sobrescritos (ex: 2 -> ²)."""
    mapa = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(n).translate(mapa)

def calcular_distribuicao_pauling(numero_atomico):
    """
    Gera a distribuição eletrônica teórica baseada no Diagrama de Pauling.
    Retorna uma string formatada (ex: 1s² 2s² 2p⁶...).
    """
    try:
        n = int(numero_atomico)
    except:
        return "Desconhecido"

    # Ordem de energia do Diagrama de Pauling
    subniveis_ordem = [
        ("1s", 2), ("2s", 2), ("2p", 6), ("3s", 2), ("3p", 6), ("4s", 2),
        ("3d", 10), ("4p", 6), ("5s", 2), ("4d", 10), ("5p", 6), ("6s", 2),
        ("4f", 14), ("5d", 10), ("6p", 6), ("7s", 2), ("5f", 14), ("6d", 10), ("7p", 6)
    ]
    
    distribuicao = []
    el_restantes = n
    
    for nome, capacidade in subniveis_ordem:
        if el_restantes <= 0:
            break
        
        qtd = min(el_restantes, capacidade)
        distribuicao.append(f"{nome}{superscript(qtd)}")
        el_restantes -= qtd
        
    return "  ".join(distribuicao)

# ==============================================================================
# 2. INTERFACE GRÁFICA: POPUP (MODAL)
# ==============================================================================

@st.dialog("🔬 Detalhes do Elemento")
def mostrar_detalhes_elemento(simbolo, info, cor_grupo):
    # --- Cabeçalho Visual ---
    st.markdown(f"""
        <div style="background-color: {cor_grupo}; padding: 15px; border-radius: 8px; text-align: center; color: white; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
            <h1 style="margin:0; font-size: 3em;">{simbolo}</h1>
            <h3 style="margin:0;">{info.get('Nome', 'Desconhecido')}</h3>
            <p style="margin:0; opacity: 0.9;">{info.get('Grupo', '-')}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- Métricas Principais ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nº Atômico (Z)", info.get('Número', '-'))
    with col2:
        st.metric("Massa Atômica", f"{info.get('Massa', '-')} u")
    with col3:
        st.metric("Período", info.get('Período', '-'))

    st.divider()

    # --- Distribuição Eletrônica Automática ---
    st.markdown("##### ⚛️ Distribuição Eletrônica (Pauling)")
    if isinstance(info.get('Número'), int):
        dist = calcular_distribuicao_pauling(info.get('Número'))
        st.code(dist, language="text")
    else:
        st.caption("Sem dados numéricos para cálculo.")

    # --- Abas de Informação Detalhada ---
    tab_info, tab_uso, tab_seguranca = st.tabs(["📖 Descrição", "⚙️ Aplicações", "⚠️ Segurança"])
    
    with tab_info:
        st.write(info.get('Descrição', 'Sem descrição disponível.'))
        if 'Estado' in info:
            st.write(f"**Estado Físico:** {info.get('Estado')}")

    with tab_uso:
        if 'Aplicacoes' in info:
            st.info(info['Aplicacoes'])
        else:
            st.write("Aplicações específicas não cadastradas.")

    with tab_seguranca:
        if 'Perigos' in info:
            st.error(f"**Riscos:** {info['Perigos']}")
        else:
            st.warning("Informações de segurança detalhadas não disponíveis. Trate com precaução padrão de laboratório.")

# ==============================================================================
# 3. DADOS (O GRANDE BLOCO DE DADOS)
# ==============================================================================

def carregar_dados_elementos():
    # Seu dicionário original COMPLETO
    elementos = {
       "H": {"Nome": "Hidrogênio", "Número": 1, "Massa": 1.008, "Grupo": "Não metais", "Período": "1", "Descrição": "Elemento mais leve e abundante."},
        "He": {"Nome": "Hélio", "Número": 2, "Massa": 4.0026, "Grupo": "Gases nobres", "Período": "1", "Descrição": "Gás nobre, usado em balões."},
        "Li": {"Nome": "Lítio", "Número": 3, "Massa": 6.94, "Grupo": "Metais alcalinos", "Período": "2", "Descrição": "Metal pouco reativo."},
        "Be": {"Nome": "Berílio", "Número": 4, "Massa": 9.0122, "Grupo": "Metais alcalino-terrosos", "Período": "2", "Descrição": "Carga para estabilidade é +2."},
        "B": {"Nome": "Boro", "Número": 5, "Massa": 10.81, "Grupo": "Semimetais", "Período": "2", "Descrição": "Precisa perder 3 elétrons para ficar estável."},
        "C": {"Nome": "Carbono", "Número": 6, "Massa": 12.011, "Grupo": "Não metais", "Período": "2", "Descrição": "Tetravalente e forma cadeias carbônicas."},
        "N": {"Nome": "Nitrogênio", "Número": 7, "Massa": 14.007, "Grupo": "Não metais", "Período": "2", "Descrição": "Elemento fundamental para a vida."},
        "O": {"Nome": "Oxigênio", "Número": 8, "Massa": 15.999, "Grupo": "Não metais", "Período": "2", "Descrição": "Essencial para a respiração."},
        "F": {"Nome": "Flúor", "Número": 9, "Massa": 18.998, "Grupo": "Halogênios", "Período": "2", "Descrição": "Mais eletronegativo da tabela."},
        "Ne": {"Nome": "Neônio", "Número": 10, "Massa": 20.180, "Grupo": "Gases nobres", "Período": "2", "Descrição": "Usado em neons e luzes."},
        "Na": {"Nome": "Sódio", "Número": 11, "Massa": 22.990, "Grupo": "Metais alcalinos", "Período": "3", "Descrição": "Muito eletropositivo e seus eletrólitos conduzem eletricidade."},
        "Mg": {"Nome": "Magnésio", "Número": 12, "Massa": 24.305, "Grupo": "Metais alcalino-terrosos", "Período": "3", "Descrição": "Pode formar o leite de magnésia."},
        "Al": {"Nome": "Alumínio", "Número": 13, "Massa": 26.982, "Grupo": "Outros metais", "Período": "3", "Descrição": "Metal forte e muito maleável."},
        "Si": {"Nome": "Silício", "Número": 14, "Massa": 28.085, "Grupo": "Semimetais", "Período": "3", "Descrição": "Usado em semicondutores."},
        "P": {"Nome": "Fósforo", "Número": 15, "Massa": 30.974, "Grupo": "Não metais", "Período": "3", "Descrição": "Fundamental à vida e precisa de 3 elétrons para a estabilidade."},
        "S": {"Nome": "Enxofre", "Número": 16, "Massa": 32.06, "Grupo": "Não metais", "Período": "3", "Descrição": "Fundamental à vida e precisa de 2 elétrons."},
        "Cl": {"Nome": "Cloro", "Número": 17, "Massa": 35.45, "Grupo": "Halogênios", "Período": "3", "Descrição": "Altamente eletronegativo e precisa de 1 elétron."},
        "Ar": {"Nome": "Argônio", "Número": 18, "Massa": 39.948, "Grupo": "Gases nobres", "Período": "3", "Descrição": "Gás nobre, usado em lâmpadas e fotografia."},
        "K": {"Nome": "Potássio", "Número": 19, "Massa": 39.098, "Grupo": "Metais alcalinos", "Período": "4", "Descrição": "Metal alcalino altamente reativo, essencial para funções celulares."},
        "Ca": {"Nome": "Cálcio", "Número": 20, "Massa": 40.078, "Grupo": "Metais alcalino-terrosos", "Período": "4", "Descrição": "Importante para ossos e dentes."},
        "Sc": {"Nome": "Escândio", "Número": 21, "Massa": 44.956, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Usado em ligas leves."},
        "Ti": {"Nome": "Titânio", "Número": 22, "Massa": 47.867, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Forte e resistente à corrosão."},
        "V": {"Nome": "Vanádio", "Número": 23, "Massa": 50.942, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Fortalece aço."},
        "Cr": {"Nome": "Cromo", "Número": 24, "Massa": 51.996, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Usado em cromagem e ligas."},
        "Mn": {"Nome": "Manganês", "Número": 25, "Massa": 54.938, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Importante para ligas de aço."},
        "Fe": {"Nome": "Ferro", "Número": 26, "Massa": 55.845, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Essencial na hemoglobina."},
        "Co": {"Nome": "Cobalto", "Número": 27, "Massa": 58.933, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Usado em ímãs e baterias."},
        "Ni": {"Nome": "Níquel", "Número": 28, "Massa": 58.693, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Usado em ligas e moedas."},
        "Cu": {"Nome": "Cobre", "Número": 29, "Massa": 63.546, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Excelente condutor elétrico."},
        "Zn": {"Nome": "Zinco", "Número": 30, "Massa": 65.38, "Grupo": "Metais de transição", "Período": "4", "Descrição": "Galvanização e essencial ao organismo."},
        "Ga": {"Nome": "Gálio", "Número": 31, "Massa": 69.723, "Grupo": "Outros metais", "Período": "4", "Descrição": "Derrete na mão, usado em eletrônicos."},
        "Ge": {"Nome": "Germânio", "Número": 32, "Massa": 72.63, "Grupo": "Semimetais", "Período": "4", "Descrição": "Usado em semicondutores."},
        "As": {"Nome": "Arsênio", "Número": 33, "Massa": 74.922, "Grupo": "Semimetais", "Período": "4", "Descrição": "Tóxico, usado em pesticidas."},
        "Se": {"Nome": "Selênio", "Número": 34, "Massa": 78.971, "Grupo": "Não metais", "Período": "4", "Descrição": "Essencial em pequenas quantidades."},
        "Br": {"Nome": "Bromo", "Número": 35, "Massa": 79.904, "Grupo": "Halogênios", "Período": "4", "Descrição": "Líquido, usado em retardadores de chama."},
        "Kr": {"Nome": "Criptônio", "Número": 36, "Massa": 83.798, "Grupo": "Gases nobres", "Período": "4", "Descrição": "Usado em lâmpadas e fotografia."},
        "Rb": {"Nome": "Rubídio", "Número": 37, "Massa": 85.468, "Grupo": "Metais alcalinos", "Período": "5", "Descrição": "Altamente reativo, usado em pesquisas."},
        "Sr": {"Nome": "Estrôncio", "Número": 38, "Massa": 87.62, "Grupo": "Metais alcalino-terrosos", "Período": "5", "Descrição": "Fogos de artifício e ligas metálicas."},
        "Y": {"Nome": "Ítrio", "Número": 39, "Massa": 88.906, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Usado em LEDs e supercondutores."},
        "Zr": {"Nome": "Zircônio", "Número": 40, "Massa": 91.224, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Resistente à corrosão, usado em reatores."},
        "Nb": {"Nome": "Nióbio", "Número": 41, "Massa": 92.906, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Usado para fortalecer aço e em supercondutores."},
        "Mo": {"Nome": "Molibdênio", "Número": 42, "Massa": 95.95, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Essencial em ligas e enzimas."},
        "Tc": {"Nome": "Tecnécio", "Número": 43, "Massa": 98, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Radioativo, usado em medicina nuclear."},
        "Ru": {"Nome": "Rutênio", "Número": 44, "Massa": 101.07, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Catalisador e ligas elétricas."},
        "Rh": {"Nome": "Ródio", "Número": 45, "Massa": 102.91, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Catalisadores automotivos."},
        "Pd": {"Nome": "Paládio", "Número": 46, "Massa": 106.42, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Joalheria e catalisadores."},
        "Ag": {"Nome": "Prata", "Número": 47, "Massa": 107.87, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Melhor condutor elétrico."},
        "Cd": {"Nome": "Cádmio", "Número": 48, "Massa": 112.41, "Grupo": "Metais de transição", "Período": "5", "Descrição": "Baterias e revestimentos."},
        "In": {"Nome": "Índio", "Número": 49, "Massa": 114.82, "Grupo": "Outros metais", "Período": "5", "Descrição": "Telas sensíveis ao toque."},
        "Sn": {"Nome": "Estanho", "Número": 50, "Massa": 118.71, "Grupo": "Outros metais", "Período": "5", "Descrição": "Bronze, soldas."},
        "Sb": {"Nome": "Antimônio", "Número": 51, "Massa": 121.76, "Grupo": "Semimetais", "Período": "5", "Descrição": "Retardadores de chama e ligas."},
        "Te": {"Nome": "Telúrio", "Número": 52, "Massa": 127.60, "Grupo": "Semimetais", "Período": "5", "Descrição": "Ligas metálicas e semicondutores."},
        "I": {"Nome": "Iodo", "Número": 53, "Massa": 126.90, "Grupo": "Halogênios", "Período": "5", "Descrição": "Função da tireoide, antissépticos."},
        "Xe": {"Nome": "Xenônio", "Número": 54, "Massa": 131.29, "Grupo": "Gases nobres", "Período": "5", "Descrição": "Lâmpadas e anestesia."},
        "Cs": {"Nome": "Césio", "Número": 55, "Massa": 132.91, "Grupo": "Metais alcalinos", "Período": "6", "Descrição": "Relógios atômicos."},
        "Ba": {"Nome": "Bário", "Número": 56, "Massa": 137.33, "Grupo": "Metais alcalino-terrosos", "Período": "6", "Descrição": "Radiologia, fogos de artifício."},
        "La": {"Nome": "Lantânio", "Número": 57, "Massa": 138.91, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Inicia os lantanídeos, lentes ópticas."},
        "Ce": {"Nome": "Cério", "Número": 58, "Massa": 140.12, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Catalisadores, polidores."},
        "Pr": {"Nome": "Praseodímio", "Número": 59, "Massa": 140.91, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs e ligas aeronáuticas."},
        "Nd": {"Nome": "Neodímio", "Número": 60, "Massa": 144.24, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs potentes."},
        "Pm": {"Nome": "Promécio", "Número": 61, "Massa": 145, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Radioativo, baterias nucleares."},
        "Sm": {"Nome": "Samário", "Número": 62, "Massa": 150.36, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs e lasers."},
        "Eu": {"Nome": "Európio", "Número": 63, "Massa": 151.96, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Fósforos de telas e lâmpadas."},
        "Gd": {"Nome": "Gadolínio", "Número": 64, "Massa": 157.25, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ressonância magnética."},
        "Tb": {"Nome": "Térbio", "Número": 65, "Massa": 158.93, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Fósforos verdes e eletrônicos."},
        "Dy": {"Nome": "Disprósio", "Número": 66, "Massa": 162.50, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs e lasers."},
        "Ho": {"Nome": "Hólmio", "Número": 67, "Massa": 164.93, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Ímãs e aplicações nucleares."},
        "Er": {"Nome": "Érbio", "Número": 68, "Massa": 167.26, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Fibras ópticas e lasers médicos."},
        "Tm": {"Nome": "Túlio", "Número": 69, "Massa": 168.93, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Lasers portáteis."},
        "Yb": {"Nome": "Itérbio", "Número": 70, "Massa": 173.05, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Relógios atômicos e materiais especiais."},
        "Lu": {"Nome": "Lutécio", "Número": 71, "Massa": 174.97, "Grupo": "Lantanídeos", "Período": "6", "Descrição": "Tomografia e catálise."},
        "Hf": {"Nome": "Háfnio", "Número": 72, "Massa": 178.49, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Ligas de alta temperatura."},
        "Ta": {"Nome": "Tântalo", "Número": 73, "Massa": 180.95, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Eletrônicos e implantes."},
        "W": {"Nome": "Tungstênio", "Número": 74, "Massa": 183.84, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Mais alto ponto de fusão."},
        "Re": {"Nome": "Rênio", "Número": 75, "Massa": 186.21, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Ligas e catalisadores."},
        "Os": {"Nome": "Ósmio", "Número": 76, "Massa": 190.23, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Metal mais denso."},
        "Ir": {"Nome": "Irídio", "Número": 77, "Massa": 192.22, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Equipamentos médicos, resistente à corrosão."},
        "Pt": {"Nome": "Platina", "Número": 78, "Massa": 195.08, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Joias e catalisadores."},
        "Au": {"Nome": "Ouro", "Número": 79, "Massa": 196.97, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Metal precioso e maleável."},
        "Hg": {"Nome": "Mercúrio", "Número": 80, "Massa": 200.59, "Grupo": "Metais de transição", "Período": "6", "Descrição": "Único metal líquido à temperatura ambiente."},
        "Tl": {"Nome": "Tálio", "Número": 81, "Massa": 204.38, "Grupo": "Outros metais", "Período": "6", "Descrição": "Tóxico, usado em eletrônicos."},
        "Pb": {"Nome": "Chumbo", "Número": 82, "Massa": 207.2, "Grupo": "Outros metais", "Período": "6", "Descrição": "Denso, usado em proteção contra radiação."},
        "Bi": {"Nome": "Bismuto", "Número": 83, "Massa": 208.98, "Grupo": "Outros metais", "Período": "6", "Descrição": "Menos tóxico que o chumbo."},
        "Po": {"Nome": "Polônio", "Número": 84, "Massa": 209, "Grupo": "Semimetais", "Período": "6", "Descrição": "Radioativo, fontes de calor."},
        "At": {"Nome": "Astato", "Número": 85, "Massa": 210, "Grupo": "Halogênios", "Período": "6", "Descrição": "Raro e radioativo."},
        "Rn": {"Nome": "Radônio", "Número": 86, "Massa": 222, "Grupo": "Gases nobres", "Período": "6", "Descrição": "Radioativo, perigoso em ambientes fechados."},
        "Fr": {"Nome": "Frâncio", "Número": 87, "Massa": 223, "Grupo": "Metais alcalinos", "Período": "7", "Descrição": "Extremamente raro e radioativo."},
        "Ra": {"Nome": "Rádio", "Número": 88, "Massa": 226, "Grupo": "Metais alcalino-terrosos", "Período": "7", "Descrição": "Radioativo, usado em luminância antiga."},
        "Ac": {"Nome": "Actínio", "Número": 89, "Massa": 227, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Inicia os actinídeos, altamente radioativo."},
        "Th": {"Nome": "Tório", "Número": 90, "Massa": 232.04, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Potencial combustível nuclear."},
        "Pa": {"Nome": "Protactínio", "Número": 91, "Massa": 231.04, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Radioativo, usado em pesquisas nucleares."},
        "Np": {"Nome": "Neptúnio", "Número": 93, "Massa": 237, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Produzido em reatores nucleares, radioativo."},
        "Pu": {"Nome": "Plutônio", "Número": 94, "Massa": 244, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Usado em armas nucleares e reatores."},
        "Am": {"Nome": "Amerício", "Número": 95, "Massa": 243, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Detectores de fumaça."},
        "Cm": {"Nome": "Cúrio", "Número": 96, "Massa": 247, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Fonte de energia espacial."},
        "Bk": {"Nome": "Berquélio", "Número": 97, "Massa": 247, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Usado em pesquisa nuclear."},
        "Cf": {"Nome": "Califórnio", "Número": 98, "Massa": 251, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Fonte de nêutrons."},
        "Es": {"Nome": "Einstênio", "Número": 99, "Massa": 252, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Produzido em explosões nucleares."},
        "Fm": {"Nome": "Férmio", "Número": 100, "Massa": 257, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Usado em estudos científicos."},
        "Md": {"Nome": "Mendelévio", "Número": 101, "Massa": 258, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Pesquisa química nuclear."},
        "No": {"Nome": "Nobélio", "Número": 102, "Massa": 259, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Experimentos laboratoriais."},
        "Lr": {"Nome": "Laurêncio", "Número": 103, "Massa": 266, "Grupo": "Actinídeos", "Período": "7", "Descrição": "Elemento sintético radioativo."},
        "Rf": {"Nome": "Rutherfórdio", "Número": 104, "Massa": 267, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Elemento sintético para pesquisa."},
        "Db": {"Nome": "Dúbnio", "Número": 105, "Massa": 268, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Radioativo, instável."},
        "Sg": {"Nome": "Seabórgio", "Número": 106, "Massa": 271, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Usado apenas em pesquisa."},
        "Bh": {"Nome": "Bóhrio", "Número": 107, "Massa": 270, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Instável e sintético."},
        "Hs": {"Nome": "Hássio", "Número": 108, "Massa": 277, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Pesquisado em laboratórios nucleares."},
        "Mt": {"Nome": "Meitnério", "Número": 109, "Massa": 278, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Superpesado e sintético."},
        "Ds": {"Nome": "Darmstádio", "Número": 110, "Massa": 281, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Meia-vida muito curta."},
        "Rg": {"Nome": "Roentgênio", "Número": 111, "Massa": 282, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Elemento radioativo sintético."},
        "Cn": {"Nome": "Copernício", "Número": 112, "Massa": 285, "Grupo": "Metais de transição", "Período": "7", "Descrição": "Altamente instável."},
        "Nh": {"Nome": "Nihônio", "Número": 113, "Massa": 286, "Grupo": "Outros metais", "Período": "7", "Descrição": "Elemento sintético."},
        "Fl": {"Nome": "Fleróvio", "Número": 114, "Massa": 289, "Grupo": "Outros metais", "Período": "7", "Descrição": "Superpesado, sintético."},
        "Mc": {"Nome": "Moscóvio", "Número": 115, "Massa": 290, "Grupo": "Outros metais", "Período": "7", "Descrição": "Meia-vida curta."},
        "Lv": {"Nome": "Livermório", "Número": 116, "Massa": 293, "Grupo": "Outros metais", "Período": "7", "Descrição": "Elemento instável."},
        "Ts": {"Nome": "Tenessino", "Número": 117, "Massa": 294, "Grupo": "Halogênios", "Período": "7", "Descrição": "Superpesado e sintético."},
        "Og": {"Nome": "Oganessônio", "Número": 118, "Massa": 294, "Grupo": "Gases nobres", "Período": "7", "Descrição": "Altamente radioativo e sintético."},
        "Uue": {"Nome": "Ununennium", "Número": 119, "Massa": 315, "Grupo": "Metais alcalinos", "Período": "8", "Descrição": "Previsto como metal alcalino superpesado."},
        "Ubn": {"Nome": "Unbinilium", "Número": 120, "Massa": 320, "Grupo": "Metais alcalino-terrosos", "Período": "8", "Descrição": "Previsto como metal alcalino-terroso."},
        "Ubu": {"Nome": "Unbiunium", "Número": 121, "Massa": 326, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Primeiro dos superactinídeos."},
        "Ubb": {"Nome": "Unbibium", "Número": 122, "Massa": 328, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Hipotético do grupo 4."},
        "Ubt": {"Nome": "Unbitrium", "Número": 123, "Massa": 330, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Propriedades desconhecidas."},
        "Ubq": {"Nome": "Unbiquadium", "Número": 124, "Massa": 332, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Ainda não sintetizado."},
        "Ubp": {"Nome": "Unbipentium", "Número": 125, "Massa": 334, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Potencial de propriedades únicas."},
        "Ubh": {"Nome": "Unbihexium", "Número": 126, "Massa": 336, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Previsto como altamente estável."},
        "Ubs": {"Nome": "Unbiseptium", "Número": 127, "Massa": 338, "Grupo": "Elementos superpesados", "Período": "8", "Descrição": "Totalmente teórico, sem dados experimentais."},
        "U": {"Nome":"Urânio","Número":92,"Massa":238.0289,"Grupo":"Actinídeos","Período":"7","Descrição":"Combustível nuclear, ogivas, blindagem, corantes de vidro e cerâmica."}
    }

    # ENRIQUECIMENTO DE DADOS (Injeção de Aplicações e Perigos)
    # Atualizamos o dicionário existente com dados extras para os principais elementos
    dados_extras = {
        "H": {
            "Aplicacoes": "Combustível (foguetes), Células de hidrogênio, Síntese de amônia (Haber-Bosch).",
            "Perigos": "Altamente inflamável, risco de explosão com ar, asfixiante simples."
        },
        "He": {
            "Aplicacoes": "Ressonância Magnética (supercondutores), Gás de purga, Balões.",
            "Perigos": "Gás inerte, mas causa asfixia por deslocamento de oxigênio. Risco criogênico."
        },
        "Li": {
            "Aplicacoes": "Baterias (Li-Ion), Tratamento de transtorno bipolar, Lubrificantes.",
            "Perigos": "Reage com água liberando hidrogênio inflamável. Corrosivo."
        },
        "C": {
            "Aplicacoes": "Aço (liga com Ferro), Filtros (Carvão ativado), Datação (C-14), Diamantes.",
            "Perigos": "Monóxido de Carbono (CO) é letal. Poeiras combustíveis."
        },
        "O": {
            "Aplicacoes": "Medicina (respiração), Siderurgia, Combustão, Tratamento de água.",
            "Perigos": "Oxidante forte (acelera incêndios). Ozônio é tóxico."
        },
        "Na": {
            "Aplicacoes": "Lâmpadas de vapor, Síntese orgânica, Sal de cozinha (NaCl).",
            "Perigos": "Reage violentamente com água. Causa queimaduras químicas graves."
        },
        "Cl": {
            "Aplicacoes": "PVC, Tratamento de água, Solventes, Branqueamento de papel.",
            "Perigos": "Gás extremamente tóxico e corrosivo (usado como arma química). Edema pulmonar."
        },
        "Fe": {
            "Aplicacoes": "Aço (construção, veículos), Ferramentas, Hemoglobina.",
            "Perigos": "Pó fino pode ser inflamável. Ingestão excessiva é tóxica."
        },
        "Hg": {
            "Aplicacoes": "Lâmpadas fluorescentes, Extração de ouro (ilegal), Antigos termômetros.",
            "Perigos": "Neurotoxina potente. Acumula no organismo. Danos renais e cerebrais."
        },
        "Pb": {
            "Aplicacoes": "Baterias chumbo-ácido, Blindagem de radiação, Munição.",
            "Perigos": "Saturnismo (neurotóxico crônico). Afeta o desenvolvimento infantil."
        },
        "U": {
            "Aplicacoes": "Combustível nuclear, Projéteis perfurantes (empobrecido).",
            "Perigos": "Radioativo e quimicamente tóxico (rins)."
        }
    }

    # Merge dos dados extras no dicionário principal
    for simbolo, extras in dados_extras.items():
        if simbolo in elementos:
            elementos[simbolo].update(extras)
    
    return elementos

# ==============================================================================
# 4. APP PRINCIPAL
# ==============================================================================

def show_tabelas():
    st.set_page_config(layout="wide", page_title="Central Química")
    st.title("📚 Central de Tabelas e Dados Químicos")


    st.markdown("""
        <style>
        /* Estilo dos botões da tabela periódica */
        div.stButton > button {
            width: 100% !important;
            height: 50px !important; /* Aumentei um pouco a altura */
            padding: 0px 1px !important; /* Espaçamento interno mínimo */
            font-size: 11px !important; /* Fonte menor para caber melhor */
            line-height: 1.1 !important; /* Espaçamento entre linhas colado */
            white-space: normal !important; /* FORÇA A QUEBRA DE LINHA */
            word-wrap: break-word !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid #444 !important;
            border-radius: 4px !important;
        }
        
        /* Efeito de destaque ao passar o mouse */
        div.stButton > button:hover {
            border-color: #ffffff !important;
            background-color: rgba(255,255,255,0.1) !important;
        }

        /* Ajuste radical de colunas para telas pequenas */
        [data-testid="column"] {
            min-width: 0px !important;
            flex-basis: 0 !important;
            flex-grow: 1 !important;
            gap: 1px !important;
            padding: 0px !important;
        }
        
        /* Remove margens extras que o Streamlit coloca entre colunas */
        [data-testid="stHorizontalBlock"] {
            gap: 2px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Carregar dados
    elementos_info = carregar_dados_elementos()

    # Cores por grupo
    cores = {
        "Gases nobres": "#8E24AA", "Halogênios": "#43A047",
        "Metais alcalinos": "#F4511E", "Metais alcalino-terrosos": "#FFB300",
        "Semimetais": "#1E88E5", "Não metais": "#3949AB",
        "Metais de transição": "#039BE5", "Lantanídeos": "#5E35B1",
        "Actinídeos": "#6D4C41", "Outros metais": "#90CAF9",
        "Elementos superpesados": "#757575", "Desconhecido": "#333"
    }

    # Layout Matriz da Tabela
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

    # --- NAVEGAÇÃO SUPERIOR ---
    tab_ferramentas, tab_links = st.tabs(["🧪 Tabelas e Ferramentas Internas", "🔗 Bancos de Dados Externos"])

    # --------------------------------------------------------------------------
    # ABA 1: FERRAMENTAS INTERNAS
    # --------------------------------------------------------------------------
    with tab_ferramentas:
        menu = st.selectbox("Selecione a Tabela/Ferramenta:", [
            "Tabela Periódica Interativa", 
            "Solubilidade (Kps)", 
            "Reatividade de Metais", 
            "Ácidos, Bases e Sais"
        ])

        if menu == "Tabela Periódica Interativa":
            st.subheader("Tabela Periódica Expandida")
            st.caption("Clique em um elemento para ver: Distribuição Eletrônica, Aplicações e Riscos.")
            
            # Renderização da Tabela
            for linha in layout_tabela:
                cols = st.columns(18)
                for i, simbolo in enumerate(linha):
                    if simbolo != "":
                        # Dados seguros com fallback
                        dados = elementos_info.get(simbolo, {"Nome": simbolo, "Grupo": "Desconhecido"})
                        cor_btn = cores.get(dados.get('Grupo'), "#333")
                        
                        # Botão
                        if cols[i].button(simbolo, key=f"btn_{simbolo}", help=dados.get('Nome')):
                            mostrar_detalhes_elemento(simbolo, dados, cor_btn)

        elif menu == "Solubilidade (Kps)":
            st.subheader("💧 Tabela de Produto de Solubilidade (Kps)")
            st.write("Valores de referência a 25°C.")
            
            # DADOS COMPLETOS DE KPS (Como solicitado)
            dados_sol = [
                ("Hidróxido de chumbo", "Pb(OH)₂", "8 x 10⁻¹⁶"),
                ("Iodeto de chumbo", "PbI₂", "7.9 x 10⁻¹⁶"),
                ("Oxalato de chumbo", "PbC₂O₄", "8.5 x 10⁻¹⁶"),
                ("Sulfato de chumbo", "PbSO₄", "1.6 x 10⁻¹⁶"),
                ("Sulfeto de chumbo", "PbS", "3 x 10⁻²⁸"),
                ("Fosfato de magnésio e amônio", "MgNH₄PO₄", "3.5 x 10⁻¹⁹"),
                ("Carbonato de magnésio", "MgCO₃", "3.5 x 10⁻¹⁹"),
                ("Hidróxido de magnésio", "Mg(OH)₂", "7.1 x 10⁻¹²"),
                ("Carbonato de manganês", "MnCO₃", "5.0 x 10⁻¹⁰"),
                ("Hidróxido de manganês", "Mn(OH)₂", "2 x 10⁻¹⁴"),
                ("Sulfeto de manganês", "MnS", "3 x 10⁻¹⁴"),
                ("Brometo de mercúrio(I)", "Hg₂Br₂", "5.6 x 10⁻¹⁷"),
                ("Carbonato de mercúrio(I)", "Hg₂CO₃", "8.9 x 10⁻¹⁷"),
                ("Cloreto de mercúrio(I)", "Hg₂Cl₂", "1.2 x 10⁻¹⁷"),
                ("Iodeto de mercúrio(I)", "Hg₂I₂", "4.7 x 10⁻¹⁹"),
                ("Tiocianato de mercúrio(I)", "Hg₂(SCN)₂", "3.0 x 10⁻¹⁹"),
                ("Hidróxido de mercúrio(II)", "Hg(OH)₂", "3.6 x 10⁻¹³"),
                ("Sulfeto de mercúrio(II)", "HgS", "5 x 10⁻⁵⁴"),
                ("Carbonato de níquel", "NiCO₃", "1.3 x 10⁻¹²"),
                ("Hidróxido de níquel", "Ni(OH)₂", "6 x 10⁻¹³"),
                ("Sulfeto de níquel", "NiS", "1.3 x 10⁻¹³"),
                ("Arsênio de prata", "Ag₃AsO₄", "6 x 10⁻²³"),
                ("Brometo de prata", "AgBr", "5.0 x 10⁻¹³"),
                ("Carbonato de prata", "Ag₂CO₃", "8.1 x 10⁻¹²"),
                ("Cloreto de prata", "AgCl", "1.8 x 10⁻¹²"),
                ("Cromato de prata", "Ag₂CrO₄", "1.2 x 10⁻¹²"),
                ("Cianeto de prata", "AgCN", "2.2 x 10⁻¹⁶"),
                ("Iodato de prata", "AgIO₃", "3.1 x 10⁻¹⁷"),
                ("Iodeto de prata", "AgI", "8.3 x 10⁻¹⁷"),
                ("Oxalato de prata", "Ag₂C₂O₄", "3.8 x 10⁻¹⁷"),
                ("Sulfeto de prata", "Ag₂S", "8 x 10⁻¹⁸"),
                ("Tiocianato de prata", "AgSCN", "1.1 x 10⁻¹⁸"),
                ("Carbonato de estrôncio", "SrCO₃", "9.3 x 10⁻¹⁸"),
                ("Oxalato de estrôncio", "SrC₂O₄", "3.2 x 10⁻¹⁸"),
                ("Sulfato de estrôncio", "SrSO₄", "3.2 x 10⁻¹⁶"),
                ("Cloreto de tálio(I)", "TlCl", "1.8 x 10⁻¹⁴"),
                ("Sulfeto de tálio(I)", "Tl₂S", "1.5 x 10⁻¹³"),
                ("Carbonato de zinco", "ZnCO₃", "1.0 x 10⁻¹⁶"),
                ("Hidróxido de zinco", "Zn(OH)₂", "3.0 x 10⁻¹¹"),
                ("Oxalato de zinco", "ZnC₂O₄", "1.3 x 10⁻¹⁷"),
                ("Sulfeto de zinco", "ZnS", "3.3 x 10⁻²³")
            ]
            
            df_sol = pd.DataFrame(dados_sol, columns=["Substância", "Fórmula", "Kps (25°C)"])
            st.dataframe(df_sol, use_container_width=True, hide_index=True, height=600)

        elif menu == "Reatividade de Metais":
            st.subheader("⚡ Fila de Reatividade dos Metais")
            c1, c2 = st.columns(2)
            with c1:
                st.error("🔥 **Mais Reativos (Oxidam Facilmente)**")
                st.markdown("""
                1. **Li, K, Rb, Cs** (Metais Alcalinos)
                2. **Ba, Sr, Ca** (Alcalino-Terrosos)
                3. **Na** (Sódio)
                4. **Mg** (Magnésio)
                5. **Al** (Alumínio)
                6. **Zn** (Zinco) - *Produz H₂ com ácidos*
                7. **Fe** (Ferro)
                """)
            with c2:
                st.success("💎 **Menos Reativos (Metais Nobres)**")
                st.markdown("""
                8. **H (Hidrogênio)** - *Referência*
                9. **Cu** (Cobre)
                10. **Hg** (Mercúrio)
                11. **Ag** (Prata)
                12. **Pd** (Paládio)
                13. **Pt** (Platina)
                14. **Au** (Ouro)
                """)

        elif menu == "Ácidos, Bases e Sais":
            subtab1, subtab2, subtab3 = st.tabs(["🧪 Ácidos", "🧴 Bases", "🧂 Sais"])
            with subtab1:
                st.write("### Principais Ácidos")
                st.json({
                    "Fortes": ["HCl (Clorídrico)", "HBr (Bromídrico)", "HI (Iodídrico)", "H₂SO₄ (Sulfúrico)", "HNO₃ (Nítrico)", "HClO₄ (Perclórico)"],
                    "Moderados": ["HF (Fluorídrico)", "H₃PO₄ (Fosfórico)"],
                    "Fracos": ["CH₃COOH (Acético/Vinagre)", "H₂CO₃ (Carbônico)", "HCN (Cianídrico)"]
                })
            with subtab2:
                st.write("### Principais Bases")
                st.markdown("""
                * **Fortes (Solúveis):** Família 1A (NaOH, KOH) e 2A (exceto Mg).
                * **Fracas (Insolúveis):** NH₄OH e metais de transição (Fe(OH)₃, Al(OH)₃).
                """)
            with subtab3:
                st.write("### Regra de Solubilidade de Sais")
                st.markdown("""
                * **Nitratos (NO₃⁻):** Todos solúveis.
                * **Cloretos (Cl⁻):** Solúveis, exceto Ag⁺, Pb²⁺, Hg₂²⁺.
                * **Sulfatos (SO₄²⁻):** Solúveis, exceto Ca²⁺, Sr²⁺, Ba²⁺, Pb²⁺.
                * **Carbonatos/Fosfatos:** Insolúveis (exceto família 1A e NH₄⁺).
                """)

    # --------------------------------------------------------------------------
    # ABA 2: LINKS EXTERNOS
    # --------------------------------------------------------------------------
    with tab_links:
        st.header("🌍 Central de Links e Bancos de Dados")
        st.caption("Acesso direto a fontes oficiais e ferramentas de pesquisa.")

        col_br, col_int, col_tools = st.columns(3)

        with col_br:
            st.subheader("🇧🇷 Brasil (Regulatório)")
            st.link_button("ANVISA - Farmacopeia", "https://www.gov.br/anvisa/pt-br/assuntos/farmacopeia", use_container_width=True)
            st.link_button("Consulta de Medicamentos", "https://consultas.anvisa.gov.br/#/medicamentos/", use_container_width=True)
            st.link_button("CETESB (FISPQ/Emergência)", "https://cetesb.sp.gov.br/emergencias-quimicas/", use_container_width=True)
            st.link_button("Conselho Federal de Química", "https://cfq.org.br/", use_container_width=True)

        with col_int:
            st.subheader("🌎 Internacional / Pesquisa")
            st.link_button("PubChem (NIH)", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)
            st.link_button("DrugBank Online", "https://go.drugbank.com/", use_container_width=True)
            st.link_button("IUPAC (Oficial)", "https://iupac.org/", use_container_width=True)
            st.link_button("WebElements", "https://www.webelements.com/", use_container_width=True)

        with col_tools:
            st.subheader("📚 Ferramentas de Estudo")
            st.link_button("Khan Academy (Química)", "https://pt.khanacademy.org/science/chemistry", use_container_width=True)
            st.link_button("Ptable (Tabela Dinâmica)", "https://ptable.com/", use_container_width=True)
            st.link_button("ScienceDirect (Artigos)", "https://www.sciencedirect.com/", use_container_width=True)

        st.divider()
        st.info("ℹ️ **Nota:** Verifique sempre a data de atualização das informações nos sites regulatórios. O PubChem é recomendado para estruturas 3D e dados toxicológicos profundos.")

if __name__ == "__main__":
    show_tabelas()

