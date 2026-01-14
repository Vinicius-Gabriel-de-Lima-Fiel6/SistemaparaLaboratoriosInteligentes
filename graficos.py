import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
# Correção definitiva para SciPy 1.14+ (Remoção do cumtrapz)
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

# --- FUNÇÕES DE SUPORTE (LÓGICA ORIGINAL PRESERVADA) ---
def extrair_dados_inteligente(arquivo):
    if arquivo is None: return None
    nome = arquivo.name.lower()
    try:
        if nome.endswith('.csv'):
            return pd.read_csv(arquivo)
        elif nome.endswith(('.xls', '.xlsx')):
            return pd.read_excel(arquivo)
        elif nome.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            texto = "".join([p.extract_text() for p in leitor.pages])
            numeros = re.findall(r"[-+]?\d*\.\d+|\d+", texto)
            dados = [float(n) for n in numeros]
            if len(dados) >= 4:
                meio = len(dados) // 2
                return pd.DataFrame({'X': dados[:meio], 'Y': dados[meio:]})
    except: return None
    return None

def gerar_pdf_laudo(series, stats, org_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Laudo Tecnico - {org_name}", ln=True, align='C')
    pdf.ln(10)
    for s in series:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Amostra: {s['nome']}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Tipo: {s.get('tipo', 'Analise')}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- FUNÇÃO PRINCIPAL ---
def show_graficos():
    st.set_page_config(page_title="LabSmart AI", layout="wide")
    st.markdown("<style>.stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }</style>", unsafe_allow_html=True)
    st.title("📊 Laboratório Gráfico de Alta Precisão (Multi-Dimensão)")

    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    # --- RECURSOS CIENTÍFICOS (LINKS) ---
    with st.expander("🌐 Ferramentas de Apoio Científico", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.link_button("🌐 GeoGebra", "https://www.geogebra.org/graphing", use_container_width=True)
        c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
        c3.link_button("📈 Weibull Analysis", "https://www.weibull.com", use_container_width=True)
        c4.link_button("💻 Matlab Web", "https://matlab.mathworks.com/", use_container_width=True)

    aba_graf, aba_estequio = st.tabs(["📈 Análise Gráfica & 3D", "🧪 Estequiometria & Laudos"])

    with aba_graf:
        with st.sidebar:
            st.header("📥 Entrada Inteligente")
            dimensao = st.radio("Dimensão:", ["2D (f(x) ou Pontos)", "3D (f(x,y))"])
            modo_entrada = st.radio("Método:", ["Manual/Função", "Upload de Arquivo"])
            
            with st.container(border=True):
                tipo_analise = st.selectbox("Modelo Analítico:", 
                    ["Linhas e Pontos", "Regressão Polinomial", "Superfície 3D", "Integral Acumulada", "Derivada"])
                nome = st.text_input("ID Amostra", f"Amostra_{len(st.session_state.series_graficas)+1}")
                
                if dimensao == "2D (f(x) ou Pontos)":
                    if modo_entrada == "Manual/Função":
                        sub_modo = st.selectbox("Formato:", ["Função f(x)", "Pontos Manuais"])
                        if sub_modo == "Função f(x)":
                            formula = st.text_input("f(x):", "sin(x)")
                            f_range = st.slider("Intervalo X", -50.0, 50.0, (0.0, 10.0))
                        else:
                            in_x = st.text_input("Eixos X (vírgula)", "1, 2, 3")
                            in_y = st.text_input("Eixos Y (vírgula)", "10, 20, 30")
                    else:
                        up_arq = st.file_uploader("Arquivo (CSV/PDF)", type=["csv", "pdf", "xlsx"])
                else:
                    # LÓGICA PARA 3D f(x,y)
                    st.info("💡 Use 'x' e 'y' na fórmula")
                    formula_3d = st.text_input("f(x,y):", "sin(sqrt(x**2 + y**2))")
                    r_xy = st.slider("Alcance (X e Y)", 1, 50, 10)

                cor = st.color_picker("Cor", "#1f77b4")

            if st.button("➕ Integrar ao Laboratório", use_container_width=True):
                try:
                    data_entry = {"nome": nome, "cor": cor, "tipo": tipo_analise, "dim": dimensao}
                    if dimensao == "2D (f(x) ou Pontos)":
                        if modo_entrada == "Manual/Função":
                            if sub_modo == "Função f(x)":
                                x = np.linspace(f_range[0], f_range[1], 200)
                                y = ne.evaluate(formula, local_dict={'x': x})
                            else:
                                x = np.fromstring(in_x, sep=',')
                                y = np.fromstring(in_y, sep=',')
                        else:
                            df = extrair_dados_inteligente(up_arq)
                            x, y = df.iloc[:,0].values, df.iloc[:,1].values
                        data_entry.update({"x": x, "y": y})
                    else:
                        # Geração de Malha 3D
                        x_3d = np.linspace(-r_xy, r_xy, 50)
                        y_3d = np.linspace(-r_xy, r_xy, 50)
                        X, Y = np.meshgrid(x_3d, y_3d)
                        Z = ne.evaluate(formula_3d, local_dict={'x': X, 'y': Y})
                        data_entry.update({"x": x_3d, "y": y_3d, "z": Z})
                    
                    st.session_state.series_graficas.append(data_entry)
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

        # --- RENDERIZAÇÃO ---
        if st.session_state.series_graficas:
            fig = go.Figure()
            for s in st.session_state.series_graficas:
                if s["dim"] == "2D (f(x) ou Pontos)":
                    if s["tipo"] == "Integral Acumulada":
                        iy = cumtrapz(s["y"], s["x"], initial=0)
                        fig.add_trace(go.Scatter(x=s["x"], y=iy, name=s["nome"], fill='tozeroy'))
                    else:
                        fig.add_trace(go.Scatter(x=s["x"], y=s["y"], name=s["nome"], line=dict(color=s["cor"])))
                else:
                    fig.add_trace(go.Surface(z=s["z"], x=s["x"], y=s["y"], colorscale=[[0, 'white'], [1, s["cor"]]], name=s["nome"]))
            
            fig.update_layout(template="plotly_white", autosize=True, height=600)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show_graficos()
