import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

try:
    from scipy.integrate import cumulative_trapezoid as cumtrapz
except ImportError:
    from scipy.integrate import cumtrapz
from sklearn.metrics import r2_score
import io
import numexpr as ne
import PyPDF2
import re
from fpdf import FPDF

MODELOS_CIENTIFICOS = {
    "Química Analítica": ["UV-Vis Absorbância", "Cromatografia HPLC/GC", "Titulação Potenciométrica", "Espectro de Massa", "FTIR", "RMN", "Lei de Beer-Lambert", "ICP-OES"],
    "Cinética e Termodinâmica": ["Ordem Zero", "Primeira Ordem", "Segunda Ordem", "Arrhenius (Ea)", "Equação de Eyring", "Michaelis-Menten", "Lineweaver-Burk", "Van't Hoff", "Energia Livre de Gibbs"],
    "Engenharia de Materiais": ["TGA (Degradação)", "DSC (Cristalinidade)", "XRD (Difração)", "Isoterma de Langmuir", "Isoterma de Freundlich", "Ensaio de Tração", "Dureza Vickers", "Fadiga de Materiais"],
    "Física e Engenharia": ["Oscilador Harmônico", "Decaimento Radioativo", "Série de Fourier", "Condução Térmica", "Queda Livre", "Circuitos RLC", "Efeito Doppler", "Mecânica de Fluidos"],
    "Bioinformática & Saúde": ["Crescimento Bacteriano", "Logística de Verhulst", "Modelagem SIR", "Farmacocinética", "Ligação Proteica", "Bioestatística de Sobrevivência"],
    "Superfícies 3D f(x,y)": ["Sela de Cavalo", "Paraboloide", "Interferência de Ondas", "Distribuição Normal 2D", "Potencial Elétrico", "Topografia Gaussiana", "Onduloide", "Geometria Fractal"]
}


def gerar_pdf_industrial(series, estequio_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "LAUDO TÉCNICO ESTRUTURADO - LABSMART PRO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. INVENTÁRIO DE SÉRIES ANALISADAS", ln=True)
    for s in series:
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"- ID: {s['nome']} | Modelo: {s['tipo']} | Dimensão: {s['dim']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. CÁLCULOS ESTEQUIOMÉTRICOS E EFICIÊNCIA", ln=True)
    for k, v in estequio_data.items():
        pdf.cell(0, 7, f"{k}: {v}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def show_graficos():
    st.set_page_config(page_title="LabSmart AI Extreme", layout="wide")
    
    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    st.title("🧪 LabSmart AI: Laboratório Multi-Dimensão v4.0")

    # --- BARRA DE RECURSOS EXTERNOS ---
    with st.expander("🌐 Ecossistema Científico Global", expanded=False):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.link_button("💻 MATLAB Online", "https://matlab.mathworks.com/", use_container_width=True)
        c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
        c3.link_button("📐 GeoGebra", "https://www.geogebra.org/", use_container_width=True)
        c4.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/", use_container_width=True)
        c5.link_button("🧬 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)

    aba_graf, aba_estequio = st.tabs(["📊 Modelagem Avançada 2D/3D", "🧪 Engenharia Estequiométrica"])

    with aba_graf:
        with st.sidebar:
            st.header("⚙️ Configurações de Entrada")
            dimensao = st.radio("Ambiente de Plotagem:", ["2D (f(x) / Experimental)", "3D (Superfícies Analíticas)"])
            
            with st.container(border=True):
                categoria = st.selectbox("Domínio Científico:", list(MODELOS_CIENTIFICOS.keys()))
                tipo_analise = st.selectbox("Modelo Analítico:", MODELOS_CIENTIFICOS[categoria])
                nome = st.text_input("Nome da Amostra", f"ID-{len(st.session_state.series_graficas)+1}")
                
                if dimensao == "2D (f(x) / Experimental)":
                    modo = st.radio("Método:", ["Função f(x)", "Entrada Manual", "IA Upload"])
                    if modo == "Função f(x)":
                        formula = st.text_input("Equação:", "exp(-x/4) * sin(2*x)")
                        f_range = st.slider("Intervalo", -50.0, 50.0, (0.0, 10.0))
                    elif modo == "Entrada Manual":
                        in_x = st.text_input("Eixo X (vírgula)", "0, 1, 2, 3, 4")
                        in_y = st.text_input("Eixo Y (vírgula)", "10, 25, 40, 55, 70")
                else:
                    formula_3d = st.text_input("Equação f(x,y):", "sin(x) * cos(y)")
                    r_xy = st.slider("Refinamento da Malha", 5, 100, 40)

                cor = st.color_picker("Cor Temática", "#00E5FF")

            if st.button("🚀 Processar e Plotar", use_container_width=True):
                try:
                    # PROTEÇÃO: CONVERSÃO FORÇADA PARA EVITAR VALUEERROR
                    entry = {"nome": nome, "cor": cor, "tipo": tipo_analise, "dim": dimensao}
                    if dimensao == "2D (f(x) / Experimental)":
                        if modo == "Função f(x)":
                            x = np.linspace(f_range[0], f_range[1], 500)
                            y = ne.evaluate(formula, local_dict={'x': x})
                        elif modo == "Entrada Manual":
                            x = np.array([float(v.strip()) for v in in_x.split(',')])
                            y = np.array([float(v.strip()) for v in in_y.split(',')])
                        entry.update({"x": x, "y": y})
                    else:
                        x_m = np.linspace(-r_xy, r_xy, 50)
                        y_m = np.linspace(-r_xy, r_xy, 50)
                        X, Y = np.meshgrid(x_m, y_m)
                        Z = ne.evaluate(formula_3d, local_dict={'x': X, 'y': Y})
                        entry.update({"x": x_m, "y": y_m, "z": Z})
                    
                    st.session_state.series_graficas.append(entry)
                    st.rerun()
                except Exception as e: st.error(f"Falha Crítica: {e}")

            if st.button("🗑️ Limpar Workspace"):
                st.session_state.series_graficas = []
                st.rerun()


        if st.session_state.series_graficas:
            fig = go.Figure()
            stats_list = []
            for s in st.session_state.series_graficas:
                if "x" not in s: continue # Proteção de sanidade
                
                if s["dim"] == "2D (f(x) / Experimental)":
                    fig.add_trace(go.Scatter(x=s["x"], y=s["y"], name=s["nome"], line=dict(color=s["cor"], width=3)))
                    stats_list.append({
                        "Amostra": s["nome"], "Média": f"{np.mean(s['y']):.4f}", 
                        "Integral": f"{np.trapz(s['y'], s['x']):.4f}", "Máximo": f"{np.max(s['y']):.4f}"
                    })
                else:
                    fig.add_trace(go.Surface(z=s["z"], x=s["x"], y=s["y"], colorscale='Portland', name=s["nome"]))
            
            fig.update_layout(template="plotly_dark", height=750, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
            if stats_list: st.dataframe(pd.DataFrame(stats_list), use_container_width=True)

    with aba_estequio:
        st.header("🧬 Central de Cálculo Estequiométrico Industrial")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                massa_r = st.number_input("Massa Inicial (g)", 0.0, format="%.4f")
                mm_r = st.number_input("Massa Molar (g/mol)", 1.0, format="%.2f")
            with c2:
                pur = st.slider("Pureza (%)", 0.0, 100.0, 100.0)
                rend = st.slider("Rendimento (%)", 0.0, 100.0, 100.0)
            with c3:
                n_util = (massa_r * (pur/100)) / mm_r
                m_final = n_util * mm_r * (rend/100)
                st.metric("Quantidade de Matéria (n)", f"{n_util:.4f} mol")
                st.metric("Massa Final Realizada", f"{m_final:.4f} g")

        st.divider()
        if st.button("🚀 Gerar Laudo Técnico Master"):
            dados_est = {"Massa In": f"{massa_r}g", "Pureza": f"{pur}%", "Rendimento": f"{rend}%", "Massa Out": f"{m_final:.4f}g"}
            pdf_bytes = gerar_pdf_industrial(st.session_state.series_graficas, dados_est)
            st.download_button("📥 Baixar Relatório PDF", pdf_bytes, "laudo_tecnico_pro.pdf")

if __name__ == "__main__":
    show_graficos()
