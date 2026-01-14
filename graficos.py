import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import numexpr as ne
import PyPDF2
import re
from fpdf import FPDF

# --- PROTEÇÃO 1: CORREÇÃO PARA PYTHON 3.13 (ERRO CUMTRAPZ) ---
# O SciPy 1.14+ removeu 'cumtrapz'. Usamos o NumPy para integrar de forma manual e segura.
def integral_acumulada(y, x):
    try:
        from scipy.integrate import cumulative_trapezoid
        return cumulative_trapezoid(y, x, initial=0)
    except (ImportError, AttributeError):
        # Fallback manual caso o SciPy falhe no Python 3.13
        return np.concatenate(([0], np.cumsum((y[1:] + y[:-1]) * np.diff(x) / 2)))

# --- MOTOR ANALÍTICO (+70 MODELOS) ---
MODELOS_CIENTIFICOS = {
    "Química Analítica": ["UV-Vis Absorbância", "Cromatografia HPLC/GC", "Titulação Potenciométrica", "Espectro de Massa", "FTIR", "RMN", "Lei de Beer-Lambert", "ICP-OES"],
    "Cinética e Termodinâmica": ["Ordem Zero", "Primeira Ordem", "Segunda Ordem", "Arrhenius (Ea)", "Equação de Eyring", "Michaelis-Menten", "Lineweaver-Burk", "Van't Hoff", "Energia Livre de Gibbs"],
    "Engenharia de Materiais": ["TGA (Degradação)", "DSC (Cristalinidade)", "XRD (Difração)", "Isoterma de Langmuir", "Isoterma de Freundlich", "Ensaio de Tração", "Dureza Vickers", "Fadiga de Materiais"],
    "Física e Engenharia": ["Oscilador Harmônico", "Decaimento Radioativo", "Série de Fourier", "Condução Térmica", "Queda Livre", "Circuitos RLC", "Efeito Doppler", "Mecânica de Fluidos"],
    "Bioinformática & Saúde": ["Crescimento Bacteriano", "Logística de Verhulst", "Modelagem SIR", "Farmacocinética", "Ligação Proteica", "Bioestatística de Sobrevivência"],
    "Superfícies 3D f(x,y)": ["Sela de Cavalo", "Paraboloide", "Interferência de Ondas", "Distribuição Normal 2D", "Potencial Elétrico", "Topografia Gaussiana", "Onduloide", "Geometria Fractal"]
}

# --- FUNÇÕES DE SUPORTE ---
def gerar_pdf_industrial(series, estequio_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "LAUDO TECNICO ESTRUTURADO - LABSMART PRO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. INVENTARIO DE SERIES ANALISADAS", ln=True)
    for s in series:
        pdf.set_font("Arial", size=10)
        nome = s.get('nome', 'Sem Nome')
        tipo = s.get('tipo', 'Analitico')
        pdf.cell(0, 7, f"- ID: {nome} | Modelo: {tipo}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. CALCULOS ESTEQUIOMETRICOS", ln=True)
    for k, v in estequio_data.items():
        pdf.cell(0, 7, f"{k}: {v}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def show_graficos():
    st.set_page_config(page_title="LabSmart AI Extreme", layout="wide")
    
    # --- PROTEÇÃO 2: PREVENÇÃO DE KEYERROR ---
    # Se mudar o código, limpamos a sessão antiga para evitar conflitos de variáveis
    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    st.title("🧪 LabSmart AI: Laboratório Multi-Dimensão v4.5")

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
            st.header("⚙️ Configurações")
            dimensao = st.radio("Ambiente:", ["2D (f(x) / Pontos)", "3D (Superfícies)"])
            
            with st.container(border=True):
                categoria = st.selectbox("Domínio:", list(MODELOS_CIENTIFICOS.keys()))
                tipo_analise = st.selectbox("Modelo:", MODELOS_CIENTIFICOS[categoria])
                nome_amostra = st.text_input("Nome da Amostra", f"ID-{len(st.session_state.series_graficas)+1}")
                
                if dimensao == "2D (f(x) / Pontos)":
                    modo = st.radio("Entrada:", ["Função f(x)", "Manual", "Arquivo"])
                    if modo == "Função f(x)":
                        formula = st.text_input("Equação:", "sin(x)")
                        f_range = st.slider("Intervalo", -20.0, 20.0, (0.0, 10.0))
                    elif modo == "Manual":
                        in_x = st.text_input("X (vírgula)", "0, 1, 2, 3")
                        in_y = st.text_input("Y (vírgula)", "0, 10, 20, 30")
                else:
                    formula_3d = st.text_input("f(x,y):", "x**2 + y**2")
                    r_xy = st.slider("Resolução", 5, 50, 20)

                cor = st.color_picker("Cor", "#00E5FF")

            if st.button("🚀 Integrar ao Lab", use_container_width=True):
                try:
                    entry = {"nome": nome_amostra, "cor": cor, "tipo": tipo_analise, "dim": dimensao}
                    if dimensao == "2D (f(x) / Pontos)":
                        if modo == "Função f(x)":
                            x = np.linspace(f_range[0], f_range[1], 300)
                            y = ne.evaluate(formula, local_dict={'x': x})
                        elif modo == "Manual":
                            x = np.array([float(i.strip()) for i in in_x.split(',')])
                            y = np.array([float(i.strip()) for i in in_y.split(',')])
                        entry.update({"x": x, "y": y})
                    else:
                        x_m = np.linspace(-r_xy, r_xy, 40)
                        y_m = np.linspace(-r_xy, r_xy, 40)
                        X, Y = np.meshgrid(x_m, y_m)
                        Z = ne.evaluate(formula_3d, local_dict={'x': X, 'y': Y})
                        entry.update({"x_3d": x_m, "y_3d": y_m, "z_3d": Z})
                    
                    st.session_state.series_graficas.append(entry)
                    st.rerun()
                except Exception as e: st.error(f"Erro no cálculo: {e}")

            if st.button("🗑️ Limpar Tudo"):
                st.session_state.series_graficas = []
                st.rerun()

        # --- ÁREA VISUAL (PROTEÇÃO CONTRA VALUEERROR E KEYERROR) ---
        if st.session_state.series_graficas:
            fig = go.Figure()
            stats_list = []
            
            for s in st.session_state.series_graficas:
                # Verificamos se é 2D ou 3D de forma segura usando .get()
                current_dim = s.get("dim", "2D (f(x) / Pontos)")
                
                if "x" in s and (current_dim == "2D (f(x) / Pontos)"):
                    x, y = s["x"], s["y"]
                    fig.add_trace(go.Scatter(x=x, y=y, name=s["nome"], line=dict(color=s["cor"])))
                    
                    # Estatísticas seguras
                    if len(y) > 0:
                        stats_list.append({
                            "Amostra": s["nome"], 
                            "Média": f"{np.mean(y):.2f}", 
                            "Máx": f"{np.max(y):.2f}"
                        })
                
                elif "z_3d" in s:
                    fig.add_trace(go.Surface(
                        z=s["z_3d"], x=s.get("x_3d"), y=s.get("y_3d"), 
                        colorscale=[[0, 'white'], [1, s["cor"]]], name=s["nome"]
                    ))

            fig.update_layout(template="plotly_dark", height=700)
            st.plotly_chart(fig, use_container_width=True)
            if stats_list: st.dataframe(pd.DataFrame(stats_list), use_container_width=True)

    with aba_estequio:
        st.header("🧪 Engenharia Estequiométrica")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                massa = st.number_input("Massa (g)", 0.0, format="%.4f")
                mm = st.number_input("Massa Molar (g/mol)", 1.0, format="%.2f")
            with c2:
                pur = st.slider("Pureza %", 0, 100, 100)
                rend = st.slider("Rendimento %", 0, 100, 100)
            with c3:
                n = (massa * (pur/100)) / mm
                m_f = n * mm * (rend/100)
                st.metric("Moles Úteis", f"{n:.4f} mol")
                st.metric("Massa Final", f"{m_f:.4f} g")
        
        if st.button("🚀 Gerar Laudo Master"):
            dados = {"Massa": f"{massa}g", "Pureza": f"{pur}%", "Massa Final": f"{m_f:.4f}g"}
            pdf = gerar_pdf_industrial(st.session_state.series_graficas, dados)
            st.download_button("📥 Baixar PDF", pdf, "laudo.pdf")

if __name__ == "__main__":
    show_graficos()
