import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import numexpr as ne
import re
import io

BIBLIOTECA_CIENTIFICA = {
    "Física 1: Mecânica e Dinâmica": {
        "MRUV: Posição": "s0 + v0*t + 0.5*a*t**2",
        "Energia Cinética": "0.5 * m * v**2",
        "Energia Potencial Gravitacional": "m * 9.8 * h",
        "Queda Livre com Arrast": "(m*9.8/k) * (1 - exp(-k*t/m))",
        "Alcance de Projétil": "(v**2 * sin(2*theta)) / 9.8",
        "Força Centrípeta": "m * v**2 / r",
        "Pêndulo Simples": "A * cos(sqrt(9.8/L) * t)",
        "Potência": "F * v",
        "Quantidade de Movimento": "m * v"
    },
    "Física 2: Fluidos e Termodinâmica": {
        "Equação de Bernoulli": "p1 + 0.5*rho*v1**2 + rho*9.8*h1",
        "Viscosidade de Poiseuille": "(pi * R**4 * deltaP) / (8 * eta * L)",
        "Lei de Stevin": "p0 + rho * 9.8 * h",
        "Dilatação Linear": "L0 * (1 + alpha * deltaT)",
        "Gás Ideal (p/V)": "(n * 0.082 * T) / V",
        "Eficiência de Carnot": "1 - (T_fria / T_quente)",
        "Variação de Entropia": "n * 8.314 * log(V2/V1)",
        "Lei de Resfriamento de Newton": "T_amb + (T0 - T_amb) * exp(-k * t)"
    },
    "Física 3 e 4: Eletromagnetismo e Moderna": {
        "Lei de Coulomb": "k * q1 * q2 / r**2",
        "Carga de Capacitor (RC)": "V0 * (1 - exp(-t/(R*C)))",
        "Descarga de Indutor (RL)": "I0 * exp(-t*(R/L))",
        "Lei de Snell (Refração)": "asin((n1 * sin(theta1)) / n2)",
        "Energia de Einstein": "m * 3e8**2",
        "Decaimento Atômico": "N0 * exp(-lambda_val * t)",
        "Efeito Fotoelétrico": "h * f - trab",
        "Comprimento de Onda de De Broglie": "6.63e-34 / (m * v)"
    },
    "Química Analítica e Físico-Química": {
        "Lei de Beer-Lambert": "eps * b * c",
        "Equação de Arrhenius": "A * exp(-Ea / (8.314 * T))",
        "Equação de Nernst": "E0 - (0.0592/n) * log10(Q)",
        "Isoterma de Langmuir": "(qmax * kl * C) / (1 + kl * C)",
        "Isoterma de Freundlich": "kf * C**(1/n)",
        "Cinética de Ordem 1": "C0 * exp(-k * t)",
        "Cinética de Ordem 2": "C0 / (1 + k * t * C0)",
        "Equação de Henderson-Hasselbalch": "pKa + log10(sal / acido)"
    },
    "Bioquímica e Biologia": {
        "Michaelis-Menten": "(Vmax * S) / (Km + S)",
        "Crescimento Logístico": "K / (1 + ((K-N0)/N0) * exp(-r * t))",
        "Equação de Hill": "Vmax * (S**n / (Ka**n + S**n))",
        "Difusão de Fick": "D * (C2 - C1) / d",
        "Modelo SIR (Epidemiologia)": "I0 * exp((beta - gamma) * t)",
        "Inibição Enzimática Competitiva": "(Vmax * S) / (Km * (1 + I/Ki) + S)"
    },
    "Farmácia e Farmacocinética": {
        "Eliminação Monocompartimental": "C0 * exp(-ke * t)",
        "Absorção Extra-Vascular (Bateman)": "((F * D * ka) / (Vd * (ka - ke))) * (exp(-ke * t) - exp(-ka * t))",
        "Infusão IV Contínua": "(R / (ke * Vd)) * (1 - exp(-ke * t))",
        "Dose de Manutenção": "(Css * Cl * tau) / F",
        "Estado Estacionário (Css)": "Dose / (Cl * tau)",
        "Volume de Distribuição": "Dose / C0",
        "Meia-vida": "0.693 / ke"
    }
}

def show_graficos():
    st.set_page_config(page_title="SmartGraphs Ultra", layout="wide")
    
    # --- CSS PARA FORÇAR BOTÕES DA SIDEBAR VERDES COM TEXTO PRETO ---
    st.markdown("""
        <style>
        /* Seleciona apenas botões dentro da sidebar */
        section[data-testid="stSidebar"] .stButton button {
            background-color: #00FF00 !important; /* Verde Puro */
            color: #000000 !important;            /* Texto Preto */
            border-radius: 5px;
            border: none;
            font-weight: bold;
        }
        /* Efeito de hover para feedback visual */
        section[data-testid="stSidebar"] .stButton button:hover {
            background-color: #00CC00 !important; /* Verde um pouco mais escuro */
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if 'plots' not in st.session_state:
        st.session_state.plots = []

    st.title("🔬 SmartGraphs AI: Laboratório Multi-Plataforma")

    # --- ECOSSISTEMA CIENTÍFICO EXPANDIDO ---
    with st.expander("🛠️ Ferramentas Auxiliares e Bases de Dados", expanded=True):
        st.subheader("Cálculo e Simulação")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.link_button("💻 MATLAB Online", "https://matlab.mathworks.com/", use_container_width=True)
        c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
        c3.link_button("📐 GeoGebra 3D", "https://www.geogebra.org/3d", use_container_width=True)
        c4.link_button("🐍 Google Colab", "https://colab.research.google.com/", use_container_width=True)
        c5.link_button("📊 Desmos Graphing", "https://www.desmos.com/calculator", use_container_width=True)

        st.subheader("Bancos de Dados e Pesquisa")
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.link_button("📚 ScienceDirect", "https://www.sciencedirect.com/", use_container_width=True)
        d2.link_button("💊 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)
        d3.link_button("🧬 Reaxys", "https://www.reaxys.com/", use_container_width=True)
        d4.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/chemistry/", use_container_width=True)
        d5.link_button("📑 Google Scholar", "https://scholar.google.com/", use_container_width=True)

    with st.sidebar:
        st.header("⚙️ Configurar Fenômeno")
        area = st.selectbox("Área Acadêmica:", list(BIBLIOTECA_CIENTIFICA.keys()))
        modelo = st.selectbox("Modelo:", list(BIBLIOTECA_CIENTIFICA[area].keys()))
        formula_base = BIBLIOTECA_CIENTIFICA[area][modelo]
        
        st.info(f"Fórmula: {formula_base}")
        
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', formula_base)
        var_indep = 't' if 't' in tokens else 'x'
        reservadas = {var_indep, 'exp', 'log10', 'sin', 'cos', 'sqrt', 'pow', 'log', 'asin', 'pi', 'ln'}
        params = sorted(list(set(tokens) - reservadas))
        
        p_values = {}
        for p in params:
            p_values[p] = st.number_input(f"Parâmetro {p}:", value=1.0, format="%.4f")
            
        alcance = st.slider(f"Alcance de {var_indep}:", 0.0, 1000.0, (0.0, 50.0))
        cor = st.color_picker("Cor do Plot", "#00FFAA")
        nome_serie = st.text_input("Identificação do Ensaio", f"Lote {len(st.session_state.plots)+1}")

        # Botão Plotar (Sidebar)
        if st.button("🚀 Plotar e Analisar", use_container_width=True):
            try:
                x_val = np.linspace(alcance[0], alcance[1], 1000)
                contexto = p_values.copy()
                contexto[var_indep] = x_val
                contexto['ln'] = np.log
                y_val = ne.evaluate(formula_base, local_dict=contexto)
                
                st.session_state.plots.append({
                    "nome": nome_serie, "x": x_val, "y": y_val, "cor": cor, "modelo": modelo
                })
                st.rerun()
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

        # Botão Resetar (Sidebar)
        if st.button("🗑️ Resetar Bancada", use_container_width=True):
            st.session_state.plots = []
            st.rerun()

    # --- ÁREA VISUAL E EXPORTAÇÃO ---
    if st.session_state.plots:
        fig = go.Figure()
        for p in st.session_state.plots:
            fig.add_trace(go.Scatter(x=p["x"], y=p["y"], name=f"{p['nome']} ({p['modelo']})",
                                   line=dict(color=p["cor"], width=3)))
        
        fig.update_layout(template="plotly_dark", height=700, xaxis_title="Eixo de Controle", yaxis_title="Resposta Científica")
        st.plotly_chart(fig, use_container_width=True)
        
        df_exp = pd.DataFrame()
        for p in st.session_state.plots:
            df_exp = pd.concat([df_exp, pd.DataFrame({f"{p['nome']}_X": p['x'], f"{p['nome']}_Y": p['y']})], axis=1)
        
        # Este botão de exportação fica fora da sidebar e manterá o estilo padrão do Streamlit
        st.download_button("📥 Exportar Dados Brutos (CSV)", df_exp.to_csv(index=False).encode('utf-8'), 
                           "lab_data.csv", "text/csv", use_container_width=True)
    else:
        st.info("Aguardando modelagem. Use as ferramentas acima para buscar constantes se necessário.")

if __name__ == "__main__":
    show_graficos()
